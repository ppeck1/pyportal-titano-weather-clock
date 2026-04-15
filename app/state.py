# app/state.py — Mutable application state
# Single source of truth for runtime state.
# Services and pages read/write fields here; no circular deps.

import time
from app.constants import BOOT, TIMER_IDLE, PAGE_HERO


class AppState:
    def __init__(self):
        # ── App mode ──────────────────────────────────────────────────────────
        self.mode         = BOOT
        self.current_page = PAGE_HERO

        # ── Timing ────────────────────────────────────────────────────────────
        self.last_input_time  = 0.0   # monotonic; for MANUAL_NAV timeout
        self.last_rotate_time = 0.0   # monotonic; for ambient rotation

        # ── Network ───────────────────────────────────────────────────────────
        self.wifi_connected   = False
        self.ip_address       = None
        self.offline_since    = None   # monotonic timestamp

        # ── Sync timestamps (monotonic) ───────────────────────────────────────
        self.last_time_sync      = 0.0
        self.last_weather_sync   = 0.0
        self.last_calendar_sync  = 0.0
        self.last_tasks_sync     = 0.0
        self.last_dashboard_sync = 0.0

        # ── Timer ─────────────────────────────────────────────────────────────
        self.timer_state      = TIMER_IDLE
        self.timer_preset_idx = 0
        self.timer_end_mono   = 0.0
        self.timer_dirty      = False

        # ── Alarm ─────────────────────────────────────────────────────────────
        self.alarm_enabled       = False
        self.alarm_hour          = 7
        self.alarm_minute        = 0
        self.alarm_triggered_day = -1   # tm_yday of last trigger

        # ── Display dirty flags ───────────────────────────────────────────────
        self.weather_dirty  = True
        self.calendar_dirty = True
        self.tasks_dirty    = True
        self.time_dirty     = True

        # ── Build info ────────────────────────────────────────────────────────
        self.build = "v2.0.0"

        # ── Brightness ────────────────────────────────────────────────────────
        self.brightness = 1.0
        self.auto_dim   = True

    # ── Helpers ───────────────────────────────────────────────────────────────
    def mark_all_dirty(self):
        self.weather_dirty  = True
        self.calendar_dirty = True
        self.tasks_dirty    = True
        self.time_dirty     = True

    def stale_age_secs(self, last_sync_mono):
        """Return how many seconds since last sync, or None if never synced."""
        if last_sync_mono == 0.0:
            return None
        return time.monotonic() - last_sync_mono

    def is_stale(self, last_sync_mono, threshold=900):
        age = self.stale_age_secs(last_sync_mono)
        return age is None or age > threshold


# Module-level singleton
state = AppState()
