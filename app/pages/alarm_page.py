# app/pages/alarm_page.py — Alarm page
# Configure a single daily alarm. HOME: dismiss/confirm. BACK/NEXT: adjust.

import displayio
from app.pages.base_page import BasePage
from app import theme, config
from app.constants import (
    BTN_BACK, BTN_HOME, BTN_NEXT,
    FOCUSED_VIEW, MANUAL_NAV, ALARM_ACTIVE,
)
from app.ui_helpers import load_font, make_label

# Sub-states for alarm editing
_EDIT_NONE = 0
_EDIT_HOUR = 1
_EDIT_MIN  = 2


class AlarmPage(BasePage):

    def __init__(self, display, state, cache, alarm_svc, audio):
        super().__init__(display, state, cache)
        self._alarm = alarm_svc
        self._audio = audio
        self._edit  = _EDIT_NONE

    def _build(self):
        W, H = self._display.width, self._display.height
        font = load_font(config.FONT_MAIN)
        P    = theme.PAD

        bg_pal    = displayio.Palette(1)
        bg_pal[0] = theme.C_BG
        bg_bmp    = displayio.Bitmap(W, H, 1)
        self.group.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

        title = make_label(font, "ALARM", theme.C_PAGE_TITLE, scale=1)
        title.anchor_point = (0.5, 0.0)
        title.anchored_position = (W // 2, P)
        self.group.append(title)

        # Enabled indicator
        self._enabled_lbl = make_label(font, "OFF", theme.C_ERR, scale=2)
        self._enabled_lbl.anchor_point = (0.5, 0.0)
        self._enabled_lbl.anchored_position = (W // 2, P + 28)
        self.group.append(self._enabled_lbl)

        # Large alarm time
        self._time_lbl = make_label(font, "7:00 AM", theme.C_TIME, scale=4)
        self._time_lbl.anchor_point = (0.5, 0.5)
        self._time_lbl.anchored_position = (W // 2, H // 2)
        self.group.append(self._time_lbl)

        # Edit cursor indicator
        self._cursor_lbl = make_label(font, "", theme.C_ACTIVE, scale=1)
        self._cursor_lbl.anchor_point = (0.5, 0.0)
        self._cursor_lbl.anchored_position = (W // 2, H // 2 + 44)
        self.group.append(self._cursor_lbl)

        # Instructions
        self._hint_lbl = make_label(font, "HOME: edit alarm", theme.C_LABEL, scale=1)
        self._hint_lbl.anchor_point = (0.5, 1.0)
        self._hint_lbl.anchored_position = (W // 2, H - P)
        self.group.append(self._hint_lbl)

        self._W = W
        self._H = H

    def _refresh(self):
        s = self._state
        # Enabled
        if s.alarm_enabled:
            self._enabled_lbl.text  = "ON"
            self._enabled_lbl.color = theme.C_OK
        else:
            self._enabled_lbl.text  = "OFF"
            self._enabled_lbl.color = theme.C_ERR

        # Time
        self._time_lbl.text = self._alarm.formatted_time()

        # Edit cursor
        if self._edit == _EDIT_NONE:
            self._cursor_lbl.text = ""
            self._hint_lbl.text   = "HOME: edit  BACK: en/disable"
        elif self._edit == _EDIT_HOUR:
            self._cursor_lbl.text  = "^ HOUR  NEXT: ok"
            self._cursor_lbl.color = theme.C_ACTIVE
            self._hint_lbl.text    = "BACK: \u2193 hour  HOME: next field"
        elif self._edit == _EDIT_MIN:
            self._cursor_lbl.text  = "^ MIN  HOME: save"
            self._cursor_lbl.color = theme.C_ACTIVE
            self._hint_lbl.text    = "BACK: \u2193 min  NEXT: \u2191 min"

    def update(self, now_struct):
        if self._state.mode == ALARM_ACTIVE and self._alarm.is_ringing():
            self._dirty = True

    def handle_input(self, event):
        s = self._state

        # If alarm is ringing, any button dismisses it
        if s.mode == ALARM_ACTIVE and self._alarm.is_ringing():
            self._alarm.dismiss()
            self._edit  = _EDIT_NONE
            self._dirty = True
            return True

        if self._edit == _EDIT_NONE:
            if event == BTN_HOME:
                # Start editing hour
                self._edit = _EDIT_HOUR
                s.mode = FOCUSED_VIEW
                self._audio.click()
                self._dirty = True
                return True
            elif event == BTN_BACK:
                self._alarm.toggle_enabled()
                self._dirty = True
                return True

        elif self._edit == _EDIT_HOUR:
            if event == BTN_NEXT:
                self._alarm.increment_hour()
                self._dirty = True
                return True
            elif event == BTN_BACK:
                self._alarm.decrement_hour()
                self._dirty = True
                return True
            elif event == BTN_HOME:
                self._edit = _EDIT_MIN
                self._audio.click()
                self._dirty = True
                return True

        elif self._edit == _EDIT_MIN:
            if event == BTN_NEXT:
                self._alarm.increment_minute()
                self._dirty = True
                return True
            elif event == BTN_BACK:
                self._alarm.decrement_minute()
                self._dirty = True
                return True
            elif event == BTN_HOME:
                # Save / done
                self._edit  = _EDIT_NONE
                s.mode = MANUAL_NAV
                self._audio.click()
                self._dirty = True
                return True

        return False
