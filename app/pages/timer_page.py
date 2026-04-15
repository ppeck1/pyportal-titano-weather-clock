# app/pages/timer_page.py — Timer page
# States: IDLE → SELECTING → RUNNING → COMPLETE
# Consumes input events internally; sets FOCUSED_VIEW while selecting/running.

import displayio
from app.pages.base_page import BasePage
from app import theme, config
from app.constants import (
    TIMER_IDLE, TIMER_SELECTING, TIMER_RUNNING, TIMER_COMPLETE,
    BTN_BACK, BTN_HOME, BTN_NEXT, FOCUSED_VIEW, MANUAL_NAV,
)
from app.ui_helpers import load_font, make_label, fmt_duration


class TimerPage(BasePage):

    def __init__(self, display, state, cache, timer_svc, audio):
        super().__init__(display, state, cache)
        self._timer = timer_svc
        self._audio = audio

    def _build(self):
        W, H = self._display.width, self._display.height
        font = load_font(config.FONT_MAIN)
        P    = theme.PAD

        bg_pal    = displayio.Palette(1)
        bg_pal[0] = theme.C_BG
        bg_bmp    = displayio.Bitmap(W, H, 1)
        self.group.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

        title = make_label(font, "TIMER", theme.C_PAGE_TITLE, scale=1)
        title.anchor_point = (0.5, 0.0)
        title.anchored_position = (W // 2, P)
        self.group.append(title)

        # Big countdown / idle display
        self._count_lbl = make_label(font, "00:00", theme.C_TIME, scale=4)
        self._count_lbl.anchor_point = (0.5, 0.5)
        self._count_lbl.anchored_position = (W // 2, H // 2 - 20)
        self.group.append(self._count_lbl)

        # Preset / status label
        self._status_lbl = make_label(font, "NEXT: cycle  HOME: start", theme.C_LABEL, scale=1)
        self._status_lbl.anchor_point = (0.5, 0.0)
        self._status_lbl.anchored_position = (W // 2, H // 2 + 40)
        self.group.append(self._status_lbl)

        # Instruction hint
        self._hint_lbl = make_label(font, "HOME: open timer", theme.C_LABEL, scale=1)
        self._hint_lbl.anchor_point = (0.5, 1.0)
        self._hint_lbl.anchored_position = (W // 2, H - P)
        self.group.append(self._hint_lbl)

        self._W = W
        self._H = H
        self._last_remaining = -1

    def _refresh(self):
        s   = self._state
        ts  = s.timer_state
        rem = self._timer.remaining_secs()

        if ts == TIMER_IDLE:
            self._count_lbl.text  = "00:00"
            self._count_lbl.color = theme.C_LABEL
            self._status_lbl.text = ""
            self._hint_lbl.text   = "HOME: open timer"

        elif ts == TIMER_SELECTING:
            self._count_lbl.text  = fmt_duration(self._timer.preset_secs())
            self._count_lbl.color = theme.C_ACTIVE
            self._status_lbl.text = "NEXT: cycle  HOME: start  BACK: cancel"
            self._hint_lbl.text   = self._timer.preset_label()

        elif ts == TIMER_RUNNING:
            self._count_lbl.text  = fmt_duration(rem)
            self._count_lbl.color = theme.C_TIME
            self._status_lbl.text = "BACK: cancel"
            self._hint_lbl.text   = ""

        elif ts == TIMER_COMPLETE:
            self._count_lbl.text  = "DONE"
            self._count_lbl.color = theme.C_OK
            self._status_lbl.text = "Any button to dismiss"
            self._hint_lbl.text   = ""

    def update(self, now_struct):
        ts  = self._state.timer_state
        rem = self._timer.remaining_secs()

        # Mark dirty if timer is running (countdown changes every second)
        if ts == TIMER_RUNNING:
            secs_left = int(rem)
            if secs_left != self._last_remaining:
                self._last_remaining = secs_left
                self._dirty = True

        if self._state.timer_dirty:
            self._dirty = True
            self._state.timer_dirty = False

    def handle_input(self, event):
        s  = self._state
        ts = s.timer_state

        if ts == TIMER_IDLE:
            if event == BTN_HOME:
                self._timer.start_selecting()
                s.mode = FOCUSED_VIEW
                self._audio.click()
                return True

        elif ts == TIMER_SELECTING:
            if event == BTN_NEXT:
                self._timer.cycle_preset()
                return True
            elif event == BTN_HOME:
                self._timer.start_timer()
                return True
            elif event == BTN_BACK:
                self._timer.cancel()
                s.mode = MANUAL_NAV
                return True

        elif ts == TIMER_RUNNING:
            if event == BTN_BACK:
                self._timer.cancel()
                s.mode = MANUAL_NAV
                return True
            return True   # absorb all input while running

        elif ts == TIMER_COMPLETE:
            # Any button dismisses
            self._timer.cancel()
            self._audio.stop()
            s.mode = MANUAL_NAV
            return True

        return False
