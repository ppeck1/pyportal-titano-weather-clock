# docs/architecture.md — System Architecture

## Overview

The firmware is structured as a cooperative scheduler running on a single thread. There is no RTOS, no asyncio, and no blocking I/O in the main loop. All operations are time-gated with `time.monotonic()`.

---

## State Machine

The top-level app state (`state.mode`) drives all behavior:

```
BOOT
  └─► CONNECTING_WIFI
        └─► SYNCING_TIME
              └─► AMBIENT_ROTATE ◄────────────────────┐
                    │ (any button press)                │
                    ▼                                   │
              MANUAL_NAV ──(inactivity timeout)─────────┘
                    │ (timer complete / alarm fires)
                    ▼
              ALARM_ACTIVE
                    │ (any button)
                    └─► AMBIENT_ROTATE (returns to Hero page)

              FOCUSED_VIEW  ← set by Timer / Alarm pages during editing
```

### State rules

| Transition | Trigger |
|-----------|---------|
| BOOT → CONNECTING_WIFI | Always on startup |
| CONNECTING_WIFI → SYNCING_TIME | Wi-Fi connected |
| SYNCING_TIME → AMBIENT_ROTATE | Time synced (or timeout) |
| AMBIENT_ROTATE → MANUAL_NAV | Any button press |
| MANUAL_NAV → AMBIENT_ROTATE | `MANUAL_TIMEOUT_SECS` of inactivity |
| Any → ALARM_ACTIVE | Timer complete or alarm fires |
| ALARM_ACTIVE → AMBIENT_ROTATE | Any button press |
| Any → FOCUSED_VIEW | Timer/Alarm page enters edit mode |
| FOCUSED_VIEW → MANUAL_NAV | Edit confirmed or cancelled |

---

## Main Loop Shape

```python
while True:
    inp.update()                    # poll hardware buttons
    controller.handle_events()      # dispatch input, manage rotation

    conn.update_if_due(state)       # reconnect Wi-Fi if needed
    time_svc.update_if_due(state)   # NTP resync on schedule
    dashboard_svc.update_if_due(state)  # fetch dashboard.json on schedule

    timer_svc.update()              # check countdown completion
    alarm_svc.update()              # check wall-clock alarm match

    audio.update()                  # advance non-blocking tone playback
    brightness.update_if_due(state) # adjust display brightness

    controller.tick(now_struct)     # update + render current page

    time.sleep(0.04)                # ~25 Hz
```

All service `update_if_due()` methods are no-ops if their interval hasn't elapsed. Rendering only happens when a page's dirty flag is set.

---

## Data Flow

```
Open-Meteo API ──────────────────────────────► WeatherService ──► cache.forecast
                                                                    cache.current_temp

Google Calendar ──► Bridge ──► dashboard.json ► CalendarService ──► cache.calendar
Google Tasks ────► Bridge ──► dashboard.json ► TasksService ──────► cache.tasks

                              cache ──► Pages ──► displayio labels
```

The PyPortal only ever makes HTTP requests to:
1. `worldtimeapi.org` for NTP
2. `api.open-meteo.com` for direct weather (if no dashboard URL)
3. Your `DASHBOARD_JSON_URL` for the unified feed

---

## Page System

Pages are instantiated lazily on first visit. Each page owns a `displayio.Group` that is swapped into the root display group on navigation.

```
AppController._root (displayio.Group)
  └─► current_page.group
        ├─► background TileGrid
        ├─► label objects (reused, never recreated)
        └─► icon TileGrid (Hero page only)
```

Display objects are created once in `_build()` and updated in `_refresh()`. No new displayio objects are allocated per loop tick.

### Page interface

```python
class BasePage:
    def show(root)          # attach to root, call render()
    def hide()              # cleanup hook
    def update(now_struct)  # called every tick; set _dirty if data changed
    def handle_input(event) # return True to consume event
    def render_if_dirty()   # called by controller; redraws only when dirty
    def render()            # force full redraw
```

---

## Dashboard Bridge

The bridge service is a small Flask application that runs on a home server or Raspberry Pi. It is the only component that authenticates to Google.

```
[Google Calendar API] ──┐
[Google Tasks API]    ──┼──► dashboard_bridge.py ──► GET /dashboard.json
[Open-Meteo API]      ──┘           │
                                     └─► PyPortal fetches every DASHBOARD_REFRESH_SECS
```

The PyPortal parses the JSON and distributes sections to the appropriate services. If a section is missing, the last cached data is preserved.

---

## Memory Strategy

- Pages are lazily instantiated (only built when first visited)
- Display objects are created once and mutated in place
- `cache.py` holds the only copies of external data; no duplication in pages
- Font objects are cached in `ui_helpers._font_cache`
- No string formatting occurs outside `_refresh()` calls
- The main loop allocates no new objects per tick

---

## Audio

Audio is generated on-device via PWM square/sine waves using `audiopwmio` + `audiocore.RawSample`. Patterns are defined as `(freq_hz, duration_ms)` tuples. The `AudioManager.update()` method advances playback one step per loop tick without blocking.

Tone buffers are allocated at play-time (small, short-lived). No audio files are required.
