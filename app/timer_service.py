# app/timer_service.py — Local countdown timer
# State machine: IDLE → SELECTING → RUNNING → COMPLETE
# Runs entirely on time.monotonic(); survives page navigation.

import time
from app.constants import (
    TIMER_IDLE, TIMER_SELECTING, TIMER_RUNNING, TIMER_COMPLETE,
    TIMER_PRESETS, TIMER_PRESET_LABELS,
    ALARM_ACTIVE,
)

class TimerService:
    def __init__(self, audio, state):
        self._audio = audio
        self._state = state

    # ── Public API ────────────────────────────────────────────────────────────

    def start_selecting(self):
        """Enter preset-selection mode."""
        s = self._state
        if s.timer_state in (TIMER_IDLE, TIMER_COMPLETE):
            s.timer_state      = TIMER_SELECTING
            s.timer_preset_idx = 0
            s.timer_dirty      = True

    def cycle_preset(self):
        """Advance to next preset (NEXT button in SELECTING state)."""
        s = self._state
        if s.timer_state == TIMER_SELECTING:
            s.timer_preset_idx = (s.timer_preset_idx + 1) % len(TIMER_PRESETS)
            s.timer_dirty = True
            self._audio.click()

    def start_timer(self):
        """Start countdown from selected preset (HOME in SELECTING)."""
        s = self._state
        if s.timer_state == TIMER_SELECTING:
            duration = TIMER_PRESETS[s.timer_preset_idx]
            s.timer_end_mono = time.monotonic() + duration
            s.timer_state    = TIMER_RUNNING
            s.timer_dirty    = True
            self._audio.click()

    def cancel(self):
        """Cancel/reset timer (BACK button)."""
        s = self._state
        s.timer_state = TIMER_IDLE
        s.timer_dirty = True
        self._audio.stop()

    def remaining_secs(self):
        """Seconds remaining; 0 if not running."""
        s = self._state
        if s.timer_state != TIMER_RUNNING:
            return 0
        return max(0.0, s.timer_end_mono - time.monotonic())

    def preset_label(self):
        return TIMER_PRESET_LABELS[self._state.timer_preset_idx]

    def preset_secs(self):
        return TIMER_PRESETS[self._state.timer_preset_idx]

    # ── Loop update ───────────────────────────────────────────────────────────

    def update(self):
        """Called every loop tick. Fires ALARM_ACTIVE on completion."""
        s = self._state
        if s.timer_state != TIMER_RUNNING:
            return
        if time.monotonic() >= s.timer_end_mono:
            s.timer_state = TIMER_COMPLETE
            s.timer_dirty = True
            s.mode        = ALARM_ACTIVE
            self._audio.play("timer_done", loop=True)
