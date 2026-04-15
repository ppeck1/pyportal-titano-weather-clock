# code.py — PyPortal Titano Ambient Dashboard
# Entry point. Initialises all services, then runs the scheduler loop.
# This file should stay thin: wiring only, no business logic.
# See app/ for all module code.

import time
import board
import displayio

# ── Display init (must happen before any displayio imports) ───────────────────
display = board.DISPLAY
from app import config
display.rotation = config.DISPLAY_ROTATION
W, H = display.width, display.height
print("Display: {}x{}".format(W, H))

# ── State + cache singletons ──────────────────────────────────────────────────
from app.state import state
from app.cache import cache

# ── Services ──────────────────────────────────────────────────────────────────
from app.audio        import AudioManager
from app.input        import InputHandler
from app.brightness   import BrightnessManager
from app.connectivity import ConnectivityManager
from app.time_service import TimeService
from app.weather_service  import WeatherService
from app.calendar_service import CalendarService
from app.tasks_service    import TasksService
from app.dashboard_service import DashboardService
from app.timer_service import TimerService
from app.alarm_service import AlarmService

audio      = AudioManager()
inp        = InputHandler(config.PIN_BACK, config.PIN_HOME, config.PIN_NEXT,
                          debounce_secs=config.DEBOUNCE_SECS)
brightness = BrightnessManager(display)
conn       = ConnectivityManager(config.SSID, config.PASSWORD)
time_svc   = TimeService(conn)
weather_svc   = WeatherService(conn, cache)
calendar_svc  = CalendarService(cache)
tasks_svc     = TasksService(cache)
dashboard_svc = DashboardService(conn, weather_svc, calendar_svc, tasks_svc)
timer_svc  = TimerService(audio, state)
alarm_svc  = AlarmService(audio, state)

# ── App controller (sets up display root group + pages) ───────────────────────
from app.app_controller import AppController
from app.constants import CONNECTING_WIFI

controller = AppController(
    display, state, cache,
    inp, audio, timer_svc, alarm_svc
)

# ── Boot sequence ─────────────────────────────────────────────────────────────
state.mark_all_dirty()
controller.mark_all_dirty()

print("Connecting Wi-Fi...")
state.mode = CONNECTING_WIFI
wifi_ok = conn.connect()
state.wifi_connected = wifi_ok
print("Wi-Fi:", "ok" if wifi_ok else "failed")

# Keep boot visually fast. Time sync and dashboard hydration happen through the
# normal scheduled update_if_due() calls once the main loop is running.
controller.enter_ambient_rotate(now=time.monotonic())

# Initial brightness
brightness.update_if_due(state)

print("Boot complete. Entering main loop.")

# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    # 1. Collect input
    inp.update()
    controller.handle_events()

    # 2. Network + data updates (non-blocking, scheduled)
    conn.update_if_due(state)
    time_svc.update_if_due(state)
    dashboard_svc.update_if_due(state)   # handles weather/calendar/tasks

    # 3. Local services (timers, alarms — no network)
    timer_svc.update()
    alarm_svc.update()

    # 4. Hardware
    audio.update()
    brightness.update_if_due(state)

    # 5. Render current page (dirty-flag gated)
    now_struct = time.localtime()
    controller.tick(now_struct)

    time.sleep(0.04)   # ~25 Hz loop; saves power, keeps input responsive
