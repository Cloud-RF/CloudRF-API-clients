"""
Spatial + frequency search over the spectra_rrl SQLite database.

The search takes a GeoJSON "circle" (as produced by the map UI — a Point
Feature with a `radius` property in metres, or a Polygon approximation of
one) plus a lower/upper frequency bound, and returns every licensed device
whose site falls inside that shape and whose (frequency ± bandwidth/2)
range overlaps the requested band.

Kept independent of Flask so it can be unit-tested / reused on its own.
"""
import math
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "spectra_rrl.db"

EARTH_RADIUS_M = 6_371_000
METERS_PER_DEG_LAT = 111_320.0

FREQ_UNIT_MULTIPLIERS = {
    "hz": 1,
    "khz": 1e3,
    "mhz": 1e6,
    "ghz": 1e9,
}
_FREQ_STRING_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([a-zA-Z]*)\s*$")


class SearchError(ValueError):
    """Raised for bad input; the Flask layer turns this into a 400."""


# --------------------------------------------------------------------------
# Parsing helpers
# --------------------------------------------------------------------------

def parse_frequency(value):
    """Accept a plain number (Hz) or a string like '88 MHz' / '2.4GHz'."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = _FREQ_STRING_RE.match(value)
        if not match:
            raise SearchError(f"Could not parse frequency: {value!r}")
        number, unit = match.groups()
        unit = unit.lower() or "hz"
        if unit not in FREQ_UNIT_MULTIPLIERS:
            raise SearchError(f"Unknown frequency unit: {unit!r} (use Hz/kHz/MHz/GHz)")
        return float(number) * FREQ_UNIT_MULTIPLIERS[unit]
    raise SearchError(f"Invalid frequency value: {value!r}")


def parse_circle(payload):
    """
    Extract a normalised shape from the request payload.

    Accepts, under payload["circle"]:
      - a GeoJSON Feature/geometry with geometry.type == "Point" and either
        geometry-level or Feature.properties "radius" (metres), or
      - a GeoJSON Feature/geometry with geometry.type == "Polygon".

    Also accepts the flat convenience form: payload["lat"], payload["lng"],
    payload["radius_m"].

    Returns either:
      {"kind": "circle", "lat": .., "lng": .., "radius_m": ..}
      {"kind": "polygon", "ring": [(lng, lat), ...]}
    """
    if "lat" in payload and "lng" in payload and "radius_m" in payload:
        try:
            lat = float(payload["lat"])
            lng = float(payload["lng"])
            radius_m = float(payload["radius_m"])
        except (TypeError, ValueError):
            raise SearchError("lat/lng/radius_m must be numbers")
        if radius_m <= 0:
            raise SearchError("radius_m must be positive")
        return {"kind": "circle", "lat": lat, "lng": lng, "radius_m": radius_m}

    circle = payload.get("circle")
    if circle is None:
        raise SearchError(
            "Provide a GeoJSON shape under 'circle' (Point+radius, or Polygon), "
            "or lat/lng/radius_m"
        )

    geometry = circle.get("geometry") if circle.get("type") == "Feature" else circle
    if not isinstance(geometry, dict) or "type" not in geometry:
        raise SearchError("'circle' must be a GeoJSON Feature or geometry object")

    geom_type = geometry.get("type")

    if geom_type == "Point":
        coords = geometry.get("coordinates")
        if not (isinstance(coords, (list, tuple)) and len(coords) >= 2):
            raise SearchError("Point geometry needs [lng, lat] coordinates")
        lng, lat = float(coords[0]), float(coords[1])

        radius_m = None
        props = circle.get("properties") if circle.get("type") == "Feature" else None
        if props and "radius" in props:
            radius_m = props["radius"]
        elif "radius" in geometry:
            radius_m = geometry["radius"]
        elif "radius_m" in payload:
            radius_m = payload["radius_m"]

        if radius_m is None:
            raise SearchError(
                "Point geometry needs a 'radius' (metres) property for a circle"
            )
        radius_m = float(radius_m)
        if radius_m <= 0:
            raise SearchError("radius must be positive")
        return {"kind": "circle", "lat": lat, "lng": lng, "radius_m": radius_m}

    if geom_type == "Polygon":
        rings = geometry.get("coordinates")
        if not rings or not rings[0]:
            raise SearchError("Polygon geometry has no coordinates")
        ring = [(float(x), float(y)) for x, y in rings[0]]
        if len(ring) < 4:
            raise SearchError("Polygon ring needs at least 4 points (incl. closing point)")
        return {"kind": "polygon", "ring": ring}

    raise SearchError(f"Unsupported geometry type: {geom_type!r} (use Point or Polygon)")


# --------------------------------------------------------------------------
# Geometry math
# --------------------------------------------------------------------------

def haversine_m(lat1, lng1, lat2, lng2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1, math.sqrt(a)))


def circle_bbox(lat, lng, radius_m):
    dlat = radius_m / METERS_PER_DEG_LAT
    cos_lat = max(math.cos(math.radians(lat)), 1e-6)  # guard near the poles
    dlng = radius_m / (METERS_PER_DEG_LAT * cos_lat)
    return (lat - dlat, lat + dlat, lng - dlng, lng + dlng)


def polygon_bbox(ring):
    lngs = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return (min(lats), max(lats), min(lngs), max(lngs))


def point_in_polygon(lng, lat, ring):
    """Ray-casting point-in-polygon test. `ring` is a list of (lng, lat)."""
    inside = False
    n = len(ring)
    x, y = lng, lat
    x1, y1 = ring[0]
    for i in range(1, n + 1):
        x2, y2 = ring[i % n]
        if ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-15) + x1
        ):
            inside = not inside
        x1, y1 = x2, y2
    return inside


# --------------------------------------------------------------------------
# Database access
# --------------------------------------------------------------------------

def get_connection():
    if not DB_PATH.exists():
        raise SearchError(
            f"Database not found at {DB_PATH}. Run "
            f"build_sqlite_db.py first (see README.md)."
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_indexes(conn):
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_site_lat_lng ON site(latitude, longitude)"
    )
    conn.commit()


def find_candidate_sites(conn, shape):
    """Return [(site_id, lat, lng, distance_m_or_None), ...] inside `shape`."""
    if shape["kind"] == "circle":
        latmin, latmax, lngmin, lngmax = circle_bbox(
            shape["lat"], shape["lng"], shape["radius_m"]
        )
    else:
        latmin, latmax, lngmin, lngmax = polygon_bbox(shape["ring"])

    rows = conn.execute(
        """
        SELECT site_id, latitude, longitude
        FROM site
        WHERE latitude BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
        """,
        (latmin, latmax, lngmin, lngmax),
    ).fetchall()

    results = []
    if shape["kind"] == "circle":
        for row in rows:
            dist = haversine_m(shape["lat"], shape["lng"], row["latitude"], row["longitude"])
            if dist <= shape["radius_m"]:
                results.append((row["site_id"], row["latitude"], row["longitude"], dist))
    else:
        for row in rows:
            if point_in_polygon(row["longitude"], row["latitude"], shape["ring"]):
                results.append((row["site_id"], row["latitude"], row["longitude"], None))
    return results


DEVICE_QUERY = """
SELECT
    d.sdd_id, d.licence_no, d.site_id, d.antenna_id,
    d.frequency, d.bandwidth,
    d.emission, d.device_type, d.station_type, d.station_name, d.call_sign,
    d.transmitter_power, d.transmitter_power_unit,
    d.eirp, d.eirp_unit,
    d.polarisation, d.azimuth, d.height, d.tilt,
    ant.gain AS antenna_gain_dbi,
    d.class_of_station_code, cos.description AS class_of_station_desc,
    l.licence_type_name, l.licence_category_name,
    l.status, lst.status_text,
    l.date_issued, l.date_of_effect, l.date_of_expiry,
    l.client_no, c.licencee, c.trading_name,
    l.sv_id, sv.sv_name,
    l.ss_id, ssv.ss_name,
    cs.site_id AS _site_id, cs.latitude, cs.longitude, cs.distance_m
FROM temp.candidate_sites cs
JOIN device_details d ON d.site_id = cs.site_id
JOIN licence l ON l.licence_no = d.licence_no
LEFT JOIN client c ON c.client_no = l.client_no
LEFT JOIN licence_status lst ON lst.status = l.status
LEFT JOIN licence_service sv ON sv.sv_id = l.sv_id
LEFT JOIN licence_subservice ssv ON ssv.ss_id = l.ss_id
LEFT JOIN class_of_station cos ON cos.code = d.class_of_station_code
LEFT JOIN antenna ant ON ant.antenna_id = d.antenna_id
WHERE d.frequency IS NOT NULL
  AND (d.frequency - COALESCE(d.bandwidth, 0) / 2.0) <= :freq_max
  AND (d.frequency + COALESCE(d.bandwidth, 0) / 2.0) >= :freq_min
ORDER BY cs.distance_m IS NOT NULL DESC, cs.distance_m ASC, d.licence_no ASC
LIMIT :limit
"""


def search(conn, shape, freq_min, freq_max, limit=500):
    candidates = find_candidate_sites(conn, shape)
    if not candidates:
        return [], False

    conn.execute("CREATE TEMP TABLE IF NOT EXISTS candidate_sites "
                 "(site_id TEXT PRIMARY KEY, latitude REAL, longitude REAL, distance_m REAL)")
    conn.execute("DELETE FROM candidate_sites")
    conn.executemany(
        "INSERT INTO candidate_sites (site_id, latitude, longitude, distance_m) VALUES (?, ?, ?, ?)",
        candidates,
    )

    freq_min_eff = freq_min if freq_min is not None else float("-inf")
    freq_max_eff = freq_max if freq_max is not None else float("inf")
    if freq_min_eff > freq_max_eff:
        raise SearchError("freq_min must be <= freq_max")

    rows = conn.execute(
        DEVICE_QUERY,
        {"freq_min": freq_min_eff, "freq_max": freq_max_eff, "limit": limit + 1},
    ).fetchall()

    truncated = len(rows) > limit
    return rows[:limit], truncated


def row_to_feature(row):
    freq = row["frequency"]
    bw = row["bandwidth"] or 0
    properties = {
        "licence_no": row["licence_no"],
        "licence_type": row["licence_type_name"],
        "licence_category": row["licence_category_name"],
        "status": row["status"],
        "status_text": row["status_text"],
        "date_issued": row["date_issued"],
        "date_of_effect": row["date_of_effect"],
        "date_of_expiry": row["date_of_expiry"],
        "client_no": row["client_no"],
        "licencee": row["licencee"],
        "trading_name": row["trading_name"],
        "service": row["sv_name"],
        "subservice": row["ss_name"],
        "site_id": row["site_id"],
        "distance_m": round(row["distance_m"], 1) if row["distance_m"] is not None else None,
        "frequency_hz": freq,
        "bandwidth_hz": row["bandwidth"],
        "freq_range_hz": [freq - bw / 2, freq + bw / 2] if freq is not None else None,
        "emission": row["emission"],
        "device_type": row["device_type"],
        "station_type": row["station_type"],
        "station_name": row["station_name"],
        "call_sign": row["call_sign"],
        "class_of_station": row["class_of_station_code"],
        "class_of_station_desc": row["class_of_station_desc"],
        "antenna_id": row["antenna_id"],
        "antenna_gain_dbi": row["antenna_gain_dbi"],
        "azimuth": row["azimuth"],
        "height_m": row["height"],
        "tilt": row["tilt"],
        "polarisation": row["polarisation"],
        "transmitter_power": row["transmitter_power"],
        "transmitter_power_unit": row["transmitter_power_unit"],
        "eirp": row["eirp"],
        "eirp_unit": row["eirp_unit"],
        "sdd_id": row["sdd_id"],
    }
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]},
        "properties": properties,
    }
