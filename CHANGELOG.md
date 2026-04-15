# CHANGELOG

All notable changes to this project are documented here.
This project follows [Semantic Versioning](https://semver.org/).

---

## v2.0.0 — Modular Ambient Dashboard Refactor

### Architecture
- Refactored monolithic `code.py` into fully modular `app/` package
- Introduced strict app-level state machine (BOOT → CONNECTING_WIFI → SYNCING_TIME → AMBIENT_ROTATE / MANUAL_NAV / FOCUSED_VIEW / ALARM_ACTIVE)
- Separated all concerns into dedicated service modules
- Added lazy page instantiation to conserve CircuitPython RAM

### New Features
- 7-page system: Hero, Forecast, Calendar, Tasks, Timer, Alarm, Status
- Auto-rotating ambient mode with configurable interval
- 3-button physical navigation (BACK / HOME / NEXT)
- Countdown timer with 4 presets (1, 5, 10, 25 min)
- Daily alarm with hour/minute editing and retrigger guard
- Non-blocking PWM audio: UI click, timer-done pattern, alarm pattern
- Unified `dashboard.json` feed for calendar + tasks via bridge service
- Status page showing Wi-Fi state, IP, sync ages, brightness, build info
- Subtle offline / stale-data indicator on Hero page
- Brightness managed by `BrightnessManager`; state exposed to Status page

### Configuration
- Migrated from `secrets.py` to `settings.toml` (CircuitPython native)
- All Wi-Fi, location, timezone, and timing values externalized
- Removed `secrets.py` from tracked files; replaced with `settings.toml.example`
- Added `DASHBOARD_JSON_URL` config key for bridge feed

### Repo cleanup
- Renamed `Changelog` → `CHANGELOG.md`
- Moved `weather_icons_32x32_9.bmp` to `assets/`
- Added `docs/` with architecture, configuration, and hardware-wiring guides
- Added `.gitignore` entries for `settings.toml` and `secrets.py`
- Added bridge service example script (`bridge/dashboard_bridge.py`)

### Preserved
- Original portrait layout and dark/minimal visual identity
- Original BMP weather icon sheet and icon-code mapping
- Original 04b30-20.bdf and daydream20.bdf fonts
- Original Open-Meteo weather API integration and icon mapping logic
- Original auto-brightness via onboard light sensor

---

## v1.0.0 — Initial Release

- First published version of the PyPortal Titano Weather and Clock Display firmware
- Added `code.py`, required fonts, and weather icon assets
- Added `EXAMPLE_secrets.py` for secure configuration setup
- Added README with setup instructions and example screenshot
- Structured repository and created v1.0.0 tagged release
