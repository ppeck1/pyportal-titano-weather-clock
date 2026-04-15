# app/config.py — Configuration loader
# All values read from settings.toml via os.getenv().
# No live credentials or location data in source.

import os
from app import constants


def _get(key, default=None):
    v = os.getenv(key)
    return v if v is not None else default


def _get_float(key, default=0.0):
    try:
        return float(_get(key, default))
    except Exception:
        return float(default)


def _get_int(key, default=0):
    try:
        return int(_get(key, default))
    except Exception:
        return int(default)


def _get_bool(key, default=False):
    v = os.getenv(key)
    if v is None:
        return bool(default)

    s = str(v).strip().lower()
    if s in ("true", "1", "yes", "y", "on"):
        return True
    if s in ("false", "0", "no", "n", "off"):
        return False
    return bool(default)


# ── Network ───────────────────────────────────────────────────────────────────
SSID     = _get("CIRCUITPY_WIFI_SSID", "")
PASSWORD = _get("CIRCUITPY_WIFI_PASSWORD", "")

# ── Location / locale ─────────────────────────────────────────────────────────
TIMEZONE       = _get("TIMEZONE", "America/New_York")
LATITUDE       = _get_float("LATITUDE", 40.11)
LONGITUDE      = _get_float("LONGITUDE", -82.93)
USE_FAHRENHEIT = _get_bool("USE_FAHRENHEIT", True)
TEMP_UNIT      = "fahrenheit" if USE_FAHRENHEIT else "celsius"
TEMP_SUFFIX    = "°F" if USE_FAHRENHEIT else "°C"

# ── Refresh intervals ─────────────────────────────────────────────────────────
WEATHER_REFRESH_SECS   = _get_int("WEATHER_REFRESH_SECS", 600)
TIME_RESYNC_SECS       = _get_int("TIME_RESYNC_SECS", 600)
TIME_RETRY_SECS        = _get_int("TIME_RETRY_SECS", 60)
AMBIENT_ROTATE_SECS    = _get_int("AMBIENT_ROTATE_SECS", 12)
MANUAL_TIMEOUT_SECS    = _get_int("MANUAL_TIMEOUT_SECS", 25)
DASHBOARD_REFRESH_SECS = _get_int("DASHBOARD_REFRESH_SECS", 300)

# ── Dashboard feed ────────────────────────────────────────────────────────────
DASHBOARD_JSON_URL = _get("DASHBOARD_JSON_URL", "")

# ── Display ───────────────────────────────────────────────────────────────────
DISPLAY_ROTATION = 270   # 90 or 270 depending on mount orientation
AUTO_DIM         = True
FIXED_BRIGHTNESS = 0.75
MIN_BRIGHT       = 0.12
MAX_BRIGHT       = 1.00
DIM_UPDATE_SECS  = 2.0

# ── Button GPIO pins ──────────────────────────────────────────────────────────
PIN_BACK = _get("PIN_BACK", constants.DEFAULT_PIN_BACK)
PIN_HOME = _get("PIN_HOME", constants.DEFAULT_PIN_HOME)
PIN_NEXT = _get("PIN_NEXT", constants.DEFAULT_PIN_NEXT)
DEBOUNCE_SECS = _get_float("DEBOUNCE_SECS", constants.DEFAULT_DEBOUNCE_SECS)

# ── Asset paths ───────────────────────────────────────────────────────────────
ICON_SHEET = "/assets/weather_icons_32x32_9.bmp"
FONT_MAIN  = "/fonts/04b30-20.bdf"
FONT_SMALL = "/fonts/04b30-20.bdf"   # same font, scaled differently

# ── External API URLs ─────────────────────────────────────────────────────────
OPEN_METEO_URL = (
    "http://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&current=temperature_2m,weather_code"
    "&hourly=temperature_2m,weather_code,time"
    "&temperature_unit={unit}"
    "&forecast_days=2"
)

TIMEZONE_API_PRIMARY  = "http://worldtimeapi.org/api/ip"
TIMEZONE_API_FALLBACK = "http://worldtimeapi.org/api/timezone/" + TIMEZONE
