# app/input.py — Debounced 3-button input handler
# Wraps keypad.Keys for edge-triggered, debounced events.
# Pages never poll raw pins; they consume events from this module.

import time
import board
from app.constants import BTN_BACK, BTN_HOME, BTN_NEXT

_BUTTON_MAP = {0: BTN_BACK, 1: BTN_HOME, 2: BTN_NEXT}


def _resolve_pin(pin):
    if isinstance(pin, str):
        try:
            return getattr(board, pin)
        except AttributeError:
            raise ValueError("Invalid pin name: {}".format(pin))
    return pin

class InputHandler:
    """
    Manages BACK / HOME / NEXT buttons.
    Call update() each loop tick; consume events via pop_event().
    """

    def __init__(self, pin_back, pin_home, pin_next, debounce_secs=0.075):
        import keypad
        pins = (
            _resolve_pin(pin_back),
            _resolve_pin(pin_home),
            _resolve_pin(pin_next),
        )
        self._keys = keypad.Keys(pins, value_when_pressed=False, pull=True)
        self._event_queue = []
        self._debounce_secs = debounce_secs
        self._last_press = {}   # key_num → monotonic

    def update(self):
        """Poll keypad and enqueue valid press events."""
        ev = self._keys.events.get()
        while ev is not None:
            if ev.pressed:
                now = time.monotonic()
                last = self._last_press.get(ev.key_number, 0.0)
                if (now - last) >= self._debounce_secs:
                    self._last_press[ev.key_number] = now
                    name = _BUTTON_MAP.get(ev.key_number)
                    if name:
                        self._event_queue.append(name)
            ev = self._keys.events.get()

    def pop_event(self):
        """Return and remove the oldest event, or None if queue is empty."""
        if self._event_queue:
            return self._event_queue.pop(0)
        return None

    def has_events(self):
        return len(self._event_queue) > 0

    def flush(self):
        """Discard all pending events."""
        self._event_queue.clear()
        _ = self._keys.events.get()   # drain hardware buffer

    def deinit(self):
        self._keys.deinit()
