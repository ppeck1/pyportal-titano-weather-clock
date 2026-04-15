# app/brightness.py — Auto-brightness controller
# Reads the onboard light sensor and adjusts display brightness.
# Falls back to fixed brightness if sensor is unavailable.

import time
import board
from app import config

class BrightnessManager:
    def __init__(self, display):
        self._display = display
        self._light   = None
        self._last_update = 0.0
        self._current = config.MAX_BRIGHT
        self._init_sensor()

    def _init_sensor(self):
        try:
            from analogio import AnalogIn
            self._light = AnalogIn(board.LIGHT)
        except Exception:
            self._light = None

    def _set(self, v):
        v = max(0.0, min(1.0, v))
        self._current = v
        try:
            self._display.brightness = v
        except Exception:
            pass

    def update_if_due(self, state):
        """Update brightness if AUTO_DIM is on and interval elapsed."""
        now = time.monotonic()
        if (now - self._last_update) < config.DIM_UPDATE_SECS:
            return
        self._last_update = now

        if config.AUTO_DIM and self._light is not None:
            frac = self._light.value / 65535.0
            frac = frac ** 0.6   # gamma curve; makes mid-light feel natural
            target = config.MIN_BRIGHT + (config.MAX_BRIGHT - config.MIN_BRIGHT) * frac
            self._set(target)
        else:
            self._set(config.FIXED_BRIGHTNESS)

        state.brightness = self._current
        state.auto_dim   = config.AUTO_DIM and (self._light is not None)

    @property
    def current(self):
        return self._current
