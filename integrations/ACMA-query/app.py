"""
Local web app: Leaflet map + collapsible side-panel form for drawing an
adjustable circle and exporting it as GeoJSON.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000 in a browser.
"""
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

import cloudrf
import search as geosearch
import settings as appsettings

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "shapes.json"
DATA_FILE.parent.mkdir(exist_ok=True)

app = Flask(__name__)
_lock = threading.Lock()

# In-memory, process-lifetime cache of fetched CloudRF coverage PNGs,
# keyed by job id, so the browser can load them from our own origin
# (no CloudRF credentials or CORS exposure in client JS).
_cloudrf_images = {}
_cloudrf_images_lock = threading.Lock()

# Load any previously-saved settings (e.g. a CloudRF key entered via the
# Settings modal) so they survive a server restart.
cloudrf.set_api_key(appsettings.read_settings().get("cloudrf_api_key"))


def _read_shapes():
    if not DATA_FILE.exists():
        return []
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _write_shapes(shapes):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(shapes, f, indent=2)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/shapes", methods=["GET"])
def list_shapes():
    with _lock:
        return jsonify(_read_shapes())


@app.route("/api/shapes", methods=["POST"])
def create_shape():
    payload = request.get_json(silent=True) or {}
    geojson = payload.get("geojson")
    if not geojson:
        return jsonify({"error": "geojson is required"}), 400

    shape = {
        "id": uuid.uuid4().hex,
        "name": payload.get("name") or "Untitled shape",
        "description": payload.get("description", ""),
        "geojson": geojson,
        "created": datetime.now(timezone.utc).isoformat(),
    }

    with _lock:
        shapes = _read_shapes()
        shapes.append(shape)
        _write_shapes(shapes)

    return jsonify(shape), 201


@app.route("/api/shapes/<shape_id>", methods=["DELETE"])
def delete_shape(shape_id):
    with _lock:
        shapes = _read_shapes()
        remaining = [s for s in shapes if s["id"] != shape_id]
        if len(remaining) == len(shapes):
            return jsonify({"error": "not found"}), 404
        _write_shapes(remaining)
    return jsonify({"status": "deleted"})


@app.route("/api/search", methods=["GET", "POST"])
def search_licences():
    """
    Search licensed devices/sites by GeoJSON circle (or polygon) + frequency band.

    POST body (preferred):
        {
          "circle": <GeoJSON Feature or geometry — Point with a "radius" (m)
                     property, or a Polygon>,
          "freq_min": <number in Hz, or "<value> <unit>" e.g. "88 MHz">,
          "freq_max": <same>,
          "limit": <optional, default 500, max 5000>
        }
    lat/lng/radius_m may be given at the top level instead of "circle".

    GET accepts the same fields as query-string params, with "circle" as a
    JSON-encoded string, e.g.:
        /api/search?lat=-33.8&lng=151.2&radius_m=5000&freq_min=88MHz&freq_max=108MHz

    Returns a GeoJSON FeatureCollection (one Feature per matching device,
    geometry = its site's location) plus a "meta" block.
    """
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
    else:
        payload = request.args.to_dict()
        if "circle" in payload:
            try:
                payload["circle"] = json.loads(payload["circle"])
            except json.JSONDecodeError:
                return jsonify({"error": "circle must be JSON-encoded GeoJSON"}), 400

    try:
        shape = geosearch.parse_circle(payload)
        freq_min = geosearch.parse_frequency(payload.get("freq_min"))
        freq_max = geosearch.parse_frequency(payload.get("freq_max"))
        if freq_min is None and freq_max is None:
            raise geosearch.SearchError("freq_min and/or freq_max is required")
        if freq_min is not None and freq_max is not None and freq_min > freq_max:
            raise geosearch.SearchError("freq_min must be <= freq_max")

        limit = int(payload.get("limit") or 500)
        limit = max(1, min(limit, 5000))
    except geosearch.SearchError as e:
        return jsonify({"error": str(e)}), 400
    except (TypeError, ValueError) as e:
        return jsonify({"error": f"invalid request: {e}"}), 400

    try:
        conn = geosearch.get_connection()
    except geosearch.SearchError as e:
        return jsonify({"error": str(e)}), 503

    try:
        geosearch.ensure_indexes(conn)
        rows, truncated = geosearch.search(conn, shape, freq_min, freq_max, limit)
        features = [geosearch.row_to_feature(row) for row in rows]
    except geosearch.SearchError as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

    return jsonify({
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "count": len(features),
            "truncated": truncated,
            "shape": shape,
            "freq_min_hz": freq_min,
            "freq_max_hz": freq_max,
            "limit": limit,
        },
    })


@app.route("/api/cloudrf/area", methods=["POST"])
def cloudrf_area():
    """
    Run a CloudRF Area coverage prediction for one site.

    POST body:
        {
          "site": {
            "lat": .., "lng": .., "name": "...",
            "frequency_hz": .., "bandwidth_hz": ..,
            "eirp": .., "eirp_unit": "...",
            "transmitter_power": .., "transmitter_power_unit": "...",
            "height_m": .., "azimuth": .., "tilt": .., "polarisation": "..."
          },
          "radius_m": <the current search radius, in metres — CloudRF is
                       called with half of this, converted to km>
        }

    Returns {job_id, bounds: [[lat,lon],[lat,lon]], image_url, coverage}
    where image_url is served by this app (see /api/cloudrf/image below),
    never a direct CloudRF URL — so the browser never needs CloudRF
    credentials and there's no CORS dependency on CloudRF's servers.
    """
    payload = request.get_json(silent=True) or {}
    site = payload.get("site") or {}
    radius_m = payload.get("radius_m")
    if not isinstance(radius_m, (int, float)) or radius_m <= 0:
        return jsonify({"error": "radius_m is required and must be positive"}), 400

    try:
        req_payload = cloudrf.build_area_request(site, radius_m)
        result_json = cloudrf.call_area_api(req_payload)
        result = cloudrf.extract_result(result_json)
        image_bytes, content_type = cloudrf.fetch_png_bytes(result["png_url"])
    except cloudrf.CloudRFError as e:
        return jsonify({"error": str(e)}), 502

    job_id = result["job_id"]
    with _cloudrf_images_lock:
        _cloudrf_images[job_id] = (image_bytes, content_type)

    return jsonify({
        "job_id": job_id,
        "bounds": result["bounds"],
        "coverage": result.get("coverage"),
        "image_url": f"/api/cloudrf/image/{job_id}",
    })


@app.route("/api/cloudrf/image/<job_id>")
def cloudrf_image(job_id):
    with _cloudrf_images_lock:
        cached = _cloudrf_images.get(job_id)
    if not cached:
        return jsonify({"error": "not found"}), 404
    image_bytes, content_type = cached
    return Response(image_bytes, mimetype=content_type)


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """
    Returns the UI-configurable settings. The CloudRF key is only included
    if it was set via this UI (settings.json) — if only an environment
    variable is configured, `cloudrf_api_key` comes back empty and
    `cloudrf_api_key_from_env` is true, so the UI can show that a key is
    active without displaying/duplicating the env var's value.
    """
    stored = appsettings.read_settings()
    return jsonify({
        "cloudrf_api_key": stored.get("cloudrf_api_key", ""),
        "cloudrf_api_key_from_env": cloudrf.has_api_key_from_env(),
    })


@app.route("/api/settings", methods=["POST"])
def update_settings():
    """
    Body: {"cloudrf_api_key": "..."}. An empty string clears the UI
    override (falling back to the CLOUDRF_API_KEY env var, if any).
    """
    payload = request.get_json(silent=True) or {}
    if "cloudrf_api_key" not in payload:
        return jsonify({"error": "cloudrf_api_key is required"}), 400

    saved = appsettings.update_settings({"cloudrf_api_key": payload["cloudrf_api_key"]})
    cloudrf.set_api_key(saved.get("cloudrf_api_key"))

    return jsonify({
        "cloudrf_api_key": saved.get("cloudrf_api_key", ""),
        "cloudrf_api_key_from_env": cloudrf.has_api_key_from_env(),
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
