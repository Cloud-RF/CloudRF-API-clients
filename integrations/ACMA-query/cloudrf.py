"""
CloudRF Area API integration.

Builds an RF coverage-prediction request from one of our search-result
sites, POSTs it directly to https://api.cloudrf.com/area, and normalises
the response into a PNG URL + a Leaflet-friendly lat/lng bounds pair.

Requires a CloudRF account + API key, set either as the CLOUDRF_API_KEY
environment variable before starting the Flask app, or entered into the
Settings modal in the UI (stored in data/settings.json via settings.py
and pushed here with set_api_key — see app.py). A UI-entered key takes
precedence over the environment variable when both are present. Get a
key at https://cloudrf.com.

Request/response field names, types, and valid ranges below are verified
against CloudRF's own OpenAPI 3.0.1 spec, extracted directly from the
embedded ReDoc state on https://cloudrf.com/documentation/developer/
(not a paraphrase) — every field CloudRF requires or that we set has a
matching entry there. Two things worth knowing:

  - output.col: the spec's JSON Schema types this as a string, but its
    own description documents numeric codes (`9` = "Greyscale/GIS", which
    is what CLOUDRF_COLOUR uses) alongside string names like
    "RAINBOW.dBm" — sending the plain integer works in practice.
  - antenna.hbw/vbw (custom beamwidth) are documented as "for use only
    with `ant` value of `0`" — since we always use ant=1 (dipole), they're
    intentionally omitted here rather than sent as unused zeros.
"""
import json
import os
import uuid

import requests

CLOUDRF_AREA_URL = "https://api.cloudrf.com/area"
CLOUDRF_COLOUR = 9  # "Greyscale/GIS" — see output.col in the spec excerpt above
CLOUDRF_TIMEOUT = 60  # seconds

# The API key can come from the CLOUDRF_API_KEY env var, or be set at
# runtime via the Settings modal (set_api_key) — which takes precedence.
_runtime_api_key = None


def set_api_key(key):
    """Set (or, with a falsy key, clear) the UI-configured API key override."""
    global _runtime_api_key
    _runtime_api_key = key or None


def get_api_key():
    return _runtime_api_key or os.environ.get("CLOUDRF_API_KEY")


def has_api_key_from_env():
    return bool(os.environ.get("CLOUDRF_API_KEY"))


# Engineering defaults for request fields the task spec didn't pin down.
# All easy to retune here without touching the request-building logic.
DEFAULT_ANTENNA_GAIN_DBI = 2  # used when the site has no antenna.gain on record
DEFAULT_ANTENNA_HEIGHT_M = 10
DEFAULT_BANDWIDTH_MHZ = 0.0125  # 12.5 kHz, a common narrowband default
DEFAULT_RECEIVER_HEIGHT_M = 2
DEFAULT_RECEIVER_SENSITIVITY_DBM = -110
DEFAULT_NOISE_FLOOR_DBM = -110
DEFAULT_RELIABILITY_PCT = 50
DEFAULT_PROPAGATION_MODEL = 7  # P.525
DEFAULT_CLUTTER_FILE = "Minimal.clt"

# Hard min/max bounds per CloudRF's schema, used to clamp real-world DB
# values (or the rare bad/placeholder ACMA record) into what the API will
# actually accept, rather than sending an out-of-range value and getting
# a validation error back.
TX_ALT_RANGE = (0.1, 120000)
TXW_RANGE = (0.001, 2_000_000)
BWI_RANGE = (0.001, 200)
TXG_RANGE = (-10, 60)
RAD_RANGE = (0.03, 400)
FRQ_RANGE_MHZ = (2, 100000)


class CloudRFError(RuntimeError):
    """Raised for any problem building the request or talking to CloudRF."""


def _clamp(value, bounds):
    lo, hi = bounds
    return max(lo, min(hi, value))


def _to_watts(power, unit):
    """Best-effort conversion of a transmitter/EIRP power figure to watts."""
    if power is None:
        return None
    try:
        power = float(power)
    except (TypeError, ValueError):
        return None
    unit = (unit or "W").strip().lower()
    if unit in ("w", "watt", "watts"):
        return power
    if unit == "mw":
        return power / 1000.0
    if unit == "kw":
        return power * 1000.0
    if unit == "dbm":
        return 10 ** ((power - 30) / 10)
    if unit == "dbw":
        return 10 ** (power / 10)
    return power  # unknown unit: assume watts rather than dropping the value


def _polarisation(code):
    code = (code or "").strip().upper()
    if code.startswith("H"):
        return "h"
    return "v"  # vertical is the overwhelmingly common default in this data


def build_area_request(site, radius_m):
    """
    site: dict with keys lat, lng, name, frequency_hz, bandwidth_hz,
          transmitter_power, transmitter_power_unit, eirp, eirp_unit,
          antenna_gain_dbi, height_m, polarisation. All but lat/lng/name/
          frequency_hz are optional (sensible defaults fill the gaps).
    radius_m: the *search* radius in metres — CloudRF gets half of it,
          converted to km per its API.

    Antenna modelling is deliberately generic: we use a dipole (ant=1)
    with ACMA's own real power and gain figures, but ignore ACMA's
    azimuth/tilt/pattern data entirely (azi/tlt both 0) rather than
    trying to reproduce a real antenna's directional pattern.
    """
    if site.get("frequency_hz") is None:
        raise CloudRFError(f"{site.get('name') or 'site'}: no frequency on record")
    if site.get("lat") is None or site.get("lng") is None:
        raise CloudRFError(f"{site.get('name') or 'site'}: no coordinates on record")

    frq_mhz = site["frequency_hz"] / 1e6
    if not (FRQ_RANGE_MHZ[0] <= frq_mhz <= FRQ_RANGE_MHZ[1]):
        raise CloudRFError(
            f"{site.get('name') or 'site'}: frequency {frq_mhz:g} MHz is outside "
            f"CloudRF's supported range ({FRQ_RANGE_MHZ[0]}-{FRQ_RANGE_MHZ[1]} MHz)"
        )

    height_m = _clamp(site.get("height_m") or DEFAULT_ANTENNA_HEIGHT_M, TX_ALT_RANGE)
    bwi_mhz = _clamp(
        (site.get("bandwidth_hz") / 1e6) if site.get("bandwidth_hz") else DEFAULT_BANDWIDTH_MHZ,
        BWI_RANGE,
    )

    # Power: prefer the raw transmitter power (paired below with the
    # antenna's own real gain, so nothing gets double-counted). EIRP is
    # only used as a fallback power figure for the minority of records
    # with no transmitter_power on file — in that case it's an
    # approximation, since EIRP already has *some* gain baked in, but a
    # rough power figure beats none.
    txw = _to_watts(site.get("transmitter_power"), site.get("transmitter_power_unit"))
    if txw is None:
        txw = _to_watts(site.get("eirp"), site.get("eirp_unit"))
    if txw is None:
        txw = 1.0
    txw = _clamp(txw, TXW_RANGE)

    antenna_gain = site.get("antenna_gain_dbi")
    txg = _clamp(antenna_gain if antenna_gain is not None else DEFAULT_ANTENNA_GAIN_DBI, TXG_RANGE)

    lat, lng = site["lat"], site["lng"]
    radius_km = _clamp((radius_m / 2) / 1000, RAD_RANGE)

    return {
        "site": (site.get("name") or "Site")[:50],
        "network": "ACMA Query Tool",
        "transmitter": {
            "lat": lat,
            "lon": lng,
            "alt": height_m,
            "frq": frq_mhz,
            "txw": txw,
            "bwi": bwi_mhz,
        },
        "receiver": {
            "lat": lat,
            "lon": lng,
            "alt": DEFAULT_RECEIVER_HEIGHT_M,
            "rxg": 0,
            "rxs": DEFAULT_RECEIVER_SENSITIVITY_DBM,
        },
        "antenna": {
            "txg": txg,
            "txl": 0,
            "ant": 1,  # vertical dipole (omni-directional) — no ACMA pattern data used
            "azi": 0,
            "tlt": 0,
            "pol": _polarisation(site.get("polarisation")),
        },
        "model": {
            "pm": DEFAULT_PROPAGATION_MODEL,
            "pe": 2,
            "ked": 0,
            "rel": DEFAULT_RELIABILITY_PCT,
        },
        "environment": {
            "clt": DEFAULT_CLUTTER_FILE,
            "elevation": 2,
            "landcover": 0,
            "buildings": 0,
            "obstacles": 0,
        },
        "output": {
            "units": "m",  # metric, above ground level ("metric" is not a valid value)
            "col": CLOUDRF_COLOUR,
            "out": 2,
            "nf": DEFAULT_NOISE_FLOOR_DBM,
            "res": 180,
            "rad": radius_km,
        },
    }


def call_area_api(payload):
    api_key = get_api_key()
    if not api_key:
        raise CloudRFError(
            "CloudRF API key not configured. Set it in Settings (top-right "
            "of the map), or set the CLOUDRF_API_KEY environment variable "
            "and restart the server."
        )

    print(f"\n=== CloudRF /area request: {payload.get('site', '?')} ===")
    print(json.dumps(payload, indent=2))
    print("=" * 50)

    try:
        resp = requests.post(
            CLOUDRF_AREA_URL,
            json=payload,
            headers={"key": api_key},
            timeout=CLOUDRF_TIMEOUT,
        )
    except requests.RequestException as e:
        raise CloudRFError(f"Could not reach CloudRF: {e}") from e

    if resp.status_code != 200:
        raise CloudRFError(f"CloudRF returned {resp.status_code}: {resp.text[:300]}")

    try:
        return resp.json()
    except ValueError as e:
        raise CloudRFError(f"CloudRF returned a non-JSON response: {e}") from e


def _flatten_bounds(raw):
    """
    Normalise CloudRF's 'bounds' field — documented as a flat array
    "clockwise from North, East, South, West" in WGS84 decimal degrees,
    e.g. [38.97373, 1.505727, 38.85827, 1.390273] — into two [lat, lon]
    corner pairs. Order-independent (Leaflet's LatLngBounds sorts min/max
    itself) and tolerant of nested-pair variants too.
    """
    nums = []

    def walk(x):
        if isinstance(x, (int, float)):
            nums.append(float(x))
        elif isinstance(x, (list, tuple)):
            for item in x:
                walk(item)

    walk(raw)
    if len(nums) < 4:
        return None
    return [[nums[0], nums[1]], [nums[2], nums[3]]]


def extract_result(result_json):
    png_url = result_json.get("PNG_Mercator") or result_json.get("PNG_WGS84")
    if not png_url:
        raise CloudRFError("CloudRF response had no PNG image URL")

    bounds = _flatten_bounds(result_json.get("bounds"))
    if not bounds:
        raise CloudRFError("CloudRF response had no usable bounds")

    return {
        "png_url": png_url,
        "bounds": bounds,
        "job_id": str(result_json.get("id") or result_json.get("sid") or uuid.uuid4().hex),
        "coverage": result_json.get("coverage"),
    }


def fetch_png_bytes(png_url):
    """Fetch the resulting PNG from CloudRF using our key, so the browser
    never needs CloudRF credentials and we sidestep any CORS issues."""
    try:
        resp = requests.get(png_url, headers={"key": get_api_key()}, timeout=CLOUDRF_TIMEOUT)
    except requests.RequestException as e:
        raise CloudRFError(f"Could not fetch coverage image: {e}") from e
    if resp.status_code != 200:
        raise CloudRFError(f"Coverage image request returned {resp.status_code}")
    return resp.content, resp.headers.get("Content-Type", "image/png")
