# app/alarm_service.py — Daily alarm service
# Single daily alarm. Checks wall-clock time each loop tick.
# Prevents retrigger within the same minute window.

import time
from app.constants import ALARM_IDLE, ALARM_RINGING, ALARM_ACTIVE, PAGE_HERO, AMBIENT_ROTATE


class AlarmService:
    def __init__(self, audio, state, on_dismiss=None):
        self._audio = audio
        self._state = state
        self._ring_state = ALARM_IDLE
        self._on_dismiss = on_dismiss

    # ── Public API ────────────────────────────────────────────────────────────

    def dismiss(self):
        """Dismiss ringing alarm. Owns all alarm-dismiss side effects."""
        s = self._state
        now = time.monotonic()
        self._ring_state = ALARM_IDLE
        s.mode = AMBIENT_ROTATE
        s.current_page = PAGE_HERO
        s.last_rotate_time = now
        s.last_input_time = now
        self._audio.stop()
        if self._on_dismiss is not None:
            try:
                self._on_dismiss()
            except Exception as e:
                print("AlarmService: dismiss callback failed:", e)

    def toggle_enabled(self):
        self._state.alarm_enabled = not self._state.alarm_enabled
        self._audio.click()

    def increment_hour(self):
        self._state.alarm_hour = (self._state.alarm_hour + 1) % 24
        self._audio.click()

    def decrement_hour(self):
        self._state.alarm_hour = (self._state.alarm_hour - 1) % 24
        self._audio.click()

    def increment_minute(self):
        self._state.alarm_minute = (self._state.alarm_minute + 5) % 60
        self._audio.click()

    def decrement_minute(self):
        self._state.alarm_minute = (self._state.alarm_minute - 5) % 60
        self._audio.click()

    def formatted_time(self):
        s = self._state
        h = s.alarm_hour % 12 or 12
        am = "AM" if s.alarm_hour < 12 else "PM"
        return "{:d}:{:02d} {}".format(h, s.alarm_minute, am)

    def is_ringing(self):
        return self._ring_state == ALARM_RINGING

    # ── Loop update ───────────────────────────────────────────────────────────

    def update(self):
        """Check wall-clock time each tick. Fire alarm when due."""
        s = self._state
        if not s.alarm_enabled:
            return
        if self._ring_state == ALARM_RINGING:
            return  # wait for dismiss()

        now = time.localtime()
        today = now.tm_yday

        # Reset trigger guard at start of new day
        if today != s.alarm_triggered_day and now.tm_hour == 0 and now.tm_min == 0:
            s.alarm_triggered_day = -1

        # Check match
        if (now.tm_hour == s.alarm_hour and
                now.tm_min == s.alarm_minute and
                today != s.alarm_triggered_day):
            s.alarm_triggered_day = today
            self._ring_state = ALARM_RINGING
            s.mode = ALARM_ACTIVE
            self._audio.play("alarm", loop=True)

    def set_dismiss_callback(self, callback):
        self._on_dismiss = callback
