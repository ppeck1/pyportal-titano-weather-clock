# app/input.py — Debounced input handler
# Supports 2-button and 3-button configurations using keypad.Keys.
# Pages never poll raw pins; they consume events from this module.

import time
from app.constants import BTN_BACK, BTN_HOME, BTN_NEXT

_HOME_CHORD_WINDOW_SECS = 0.30


def _resolve_pin(pin):
    if pin is None:
        return None
    if isinstance(pin, str):
        name = pin.strip()
        if not name:
            return None
        import board
        try:
            return getattr(board, name)
        except AttributeError:
            raise ValueError("Invalid pin name: {}".format(name))
    return pin

class InputHandler:
    """
    Manages BACK / HOME / NEXT input events.
    Call update() each loop tick; consume events via pop_event().
    """

    def __init__(self, pin_back, pin_home, pin_next, debounce_secs=0.075):
        import keypad
        requested = (
            ("BACK", BTN_BACK, pin_back, True),
            ("HOME", BTN_HOME, pin_home, False),
            ("NEXT", BTN_NEXT, pin_next, False),
        )
        resolved_pairs = []
        for name, event_name, raw_pin, required in requested:
            try:
                resolved = _resolve_pin(raw_pin)
                if resolved is not None:
                    resolved_pairs.append((resolved, event_name))
                elif required:
                    print("Input: required pin {} missing".format(name))
            except Exception as e:
                if required:
                    print("Input: required pin {} invalid ({})".format(name, e))
                else:
                    print("Input: optional pin {} ignored ({})".format(name, e))

        # If HOME is not configured but we have BACK + NEXT, keep a stable 2-button map.
        if len(resolved_pairs) == 2:
            events = [evt for _, evt in resolved_pairs]
            if BTN_BACK in events and BTN_NEXT in events and BTN_HOME not in events:
                self._mode = "two_button"
            else:
                self._mode = "generic"
        else:
            self._mode = "three_button" if len(resolved_pairs) >= 3 else "generic"

        if not resolved_pairs:
            raise ValueError("No usable input pins configured")

        pins = tuple(pin for pin, _evt in resolved_pairs)
        self._event_for_key = {idx: evt for idx, (_pin, evt) in enumerate(resolved_pairs)}
        self._keys = keypad.Keys(pins, value_when_pressed=False, pull=True)
        self._event_queue = []
        self._debounce_secs = debounce_secs
        self._last_press = {}   # key_num → monotonic
        self._pressed = {}
        self._home_emitted = False
        print("Input: initialized mode={} keys={}".format(self._mode, len(pins)))

    def update(self):
        """Poll keypad and enqueue valid press events."""
        ev = self._keys.events.get()
        while ev is not None:
            if ev.pressed:
                self._pressed[ev.key_number] = time.monotonic()
                now = time.monotonic()
                last = self._last_press.get(ev.key_number, 0.0)
                if (now - last) >= self._debounce_secs:
                    self._last_press[ev.key_number] = now
                    name = self._event_for_key.get(ev.key_number)
                    if self._mode == "two_button":
                        other_key = 1 - ev.key_number
                        other_press = self._pressed.get(other_key)
                        if other_press is not None and (now - other_press) <= _HOME_CHORD_WINDOW_SECS:
                            if not self._home_emitted:
                                self._event_queue.append(BTN_HOME)
                                self._home_emitted = True
                        elif name:
                            self._event_queue.append(name)
                    elif name:
                        self._event_queue.append(name)
            else:
                self._pressed.pop(ev.key_number, None)
                if self._mode == "two_button" and not self._pressed:
                    self._home_emitted = False
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
