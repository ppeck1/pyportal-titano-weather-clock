# docs/configuration.md — Configuration Reference

All configuration lives in `settings.toml` on the CIRCUITPY drive.
CircuitPython reads this file automatically at boot via `os.getenv()`.

**Never commit `settings.toml` to git.** Use `settings.toml.example` as a template.

---

## Required Keys

| Key | Example | Description |
|-----|---------|-------------|
| `CIRCUITPY_WIFI_SSID` | `"MyNetwork"` | Wi-Fi network name |
| `CIRCUITPY_WIFI_PASSWORD` | `"secret"` | Wi-Fi password |
| `TIMEZONE` | `"America/New_York"` | IANA timezone string |
| `LATITUDE` | `"40.1100"` | Decimal latitude |
| `LONGITUDE` | `"-82.9300"` | Decimal longitude |

---

## Optional Keys (have defaults)

### Units
| Key | Default | Description |
|-----|---------|-------------|
| `USE_FAHRENHEIT` | `"true"` | `"true"` = °F, `"false"` = °C |

### Refresh intervals
| Key | Default | Description |
|-----|---------|-------------|
| `WEATHER_REFRESH_SECS` | `"600"` | Direct Open-Meteo fetch interval (seconds). Only used when `DASHBOARD_JSON_URL` is empty. |
| `DASHBOARD_REFRESH_SECS` | `"300"` | Dashboard feed fetch interval (seconds) |
| `TIME_RESYNC_SECS` | `"600"` | NTP resync interval (seconds) |

### UI timing
| Key | Default | Description |
|-----|---------|-------------|
| `AMBIENT_ROTATE_SECS` | `"12"` | Seconds per page during auto-rotation |
| `MANUAL_TIMEOUT_SECS` | `"25"` | Idle seconds before auto-rotation resumes |

### Dashboard feed
| Key | Default | Description |
|-----|---------|-------------|
| `DASHBOARD_JSON_URL` | `""` | Full URL to dashboard.json endpoint. Leave empty to use direct Open-Meteo only. |

---

## Timezone Format

Use IANA timezone strings from:
https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

Common examples:
```
America/New_York
America/Chicago
America/Denver
America/Los_Angeles
Europe/London
Europe/Paris
Asia/Tokyo
Australia/Sydney
```

---

## Button Pin Mapping

Button pins can be set in `settings.toml` (preferred). This firmware supports
both 2-button and 3-button setups.

```toml
PIN_BACK="D3"
PIN_HOME=""
PIN_NEXT="D4"
```

Recommended PyPortal Titano setup is 2-button (`D3` + `D4`), with `PIN_HOME=""`.
In 2-button mode, pressing both buttons together emits `HOME`.

---

## Display Orientation

Also set in `app/config.py`:

```python
DISPLAY_ROTATION = 270   # 90 or 270 depending on how your device is mounted
```

---

## Migration from secrets.py

If you were using the old `secrets.py` format, translate as follows:

| Old `secrets.py` key | New `settings.toml` key |
|----------------------|-------------------------|
| `secrets["ssid"]` | `CIRCUITPY_WIFI_SSID` |
| `secrets["password"]` | `CIRCUITPY_WIFI_PASSWORD` |
| `secrets["timezone"]` | `TIMEZONE` |

Hardcoded `LATITUDE`, `LONGITUDE` in `code.py` should be moved to `settings.toml`.

---

## Minimal Working Example

```toml
CIRCUITPY_WIFI_SSID="HomeNetwork"
CIRCUITPY_WIFI_PASSWORD="password123"
TIMEZONE="America/Chicago"
LATITUDE="41.8781"
LONGITUDE="-87.6298"
USE_FAHRENHEIT="true"
```

This gives you a working clock + weather display with no calendar or tasks data.
