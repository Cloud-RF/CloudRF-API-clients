"""
Small local settings store (data/settings.json) for values the user can
configure from the UI instead of environment variables — currently just
the CloudRF API key.
"""
import json
import threading
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent / "data" / "settings.json"
SETTINGS_FILE.parent.mkdir(exist_ok=True)

_lock = threading.Lock()


def read_settings():
    if not SETTINGS_FILE.exists():
        return {}
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def write_settings(settings):
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def update_settings(patch):
    """Merge `patch` into the stored settings (a None value deletes the key,
    so submitting an empty field clears that override) and persist it."""
    with _lock:
        settings = read_settings()
        for key, value in patch.items():
            if value is None or value == "":
                settings.pop(key, None)
            else:
                settings[key] = value
        write_settings(settings)
        return settings
