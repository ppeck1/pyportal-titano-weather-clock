# app/pages/calendar_page.py — Calendar page
# Shows next 3 events from the dashboard feed: time + title.

import displayio
from app.pages.base_page import BasePage
from app import theme, config
from app.ui_helpers import load_font, make_label, truncate

_MAX_EVENTS = 3


class CalendarPage(BasePage):

    def _build(self):
        W, H = self._display.width, self._display.height
        font = load_font(config.FONT_MAIN)
        P    = theme.PAD

        bg_pal    = displayio.Palette(1)
        bg_pal[0] = theme.C_BG
        bg_bmp    = displayio.Bitmap(W, H, 1)
        self.group.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

        # Title
        title = make_label(font, "CALENDAR", theme.C_PAGE_TITLE, scale=1)
        title.anchor_point = (0.5, 0.0)
        title.anchored_position = (W // 2, P)
        self.group.append(title)

        # No-data label
        self._empty_lbl = make_label(font, "No events", theme.C_LABEL, scale=1)
        self._empty_lbl.anchor_point = (0.5, 0.5)
        self._empty_lbl.anchored_position = (W // 2, H // 2)
        self.group.append(self._empty_lbl)

        # Event rows
        title_h = 24 + P
        row_h   = 56
        self._time_lbls  = []
        self._title_lbls = []

        for i in range(_MAX_EVENTS):
            y = title_h + i * row_h

            # Bullet
            bullet = make_label(font, "\u25b6", theme.C_ACTIVE, scale=1)
            bullet.anchor_point = (0.0, 0.0)
            bullet.anchored_position = (P, y + 4)
            self.group.append(bullet)

            # Time
            t_lbl = make_label(font, "--:--", theme.C_LABEL, scale=1)
            t_lbl.anchor_point = (0.0, 0.0)
            t_lbl.anchored_position = (P + 16, y + 4)
            self.group.append(t_lbl)
            self._time_lbls.append(t_lbl)

            # Title (larger)
            ev_lbl = make_label(font, "", theme.C_VALUE, scale=2)
            ev_lbl.anchor_point = (0.0, 0.0)
            ev_lbl.anchored_position = (P + 16, y + 22)
            self.group.append(ev_lbl)
            self._title_lbls.append(ev_lbl)

        # Offline indicator
        self._offline_lbl = make_label(font, "", theme.C_OFFLINE, scale=1)
        self._offline_lbl.anchor_point = (0.5, 1.0)
        self._offline_lbl.anchored_position = (W // 2, H - P)
        self.group.append(self._offline_lbl)

        self._W = W
        self._H = H

    def _refresh(self):
        events = self._cache.calendar
        has_data = len(events) > 0
        self._empty_lbl.text = "" if has_data else "No events"

        for i in range(_MAX_EVENTS):
            if i < len(events):
                ev = events[i]
                self._time_lbls[i].text  = truncate(ev.get("time", ""), 5)
                self._title_lbls[i].text = truncate(ev.get("title", ""), 14)
            else:
                self._time_lbls[i].text  = ""
                self._title_lbls[i].text = ""

        if not self._state.wifi_connected:
            self._offline_lbl.text = "OFFLINE - cached data"
        elif self._state.is_stale(self._state.last_calendar_sync):
            self._offline_lbl.text = "stale"
        else:
            self._offline_lbl.text = ""

    def update(self, now_struct):
        if self._state.calendar_dirty:
            self._dirty = True
            self._state.calendar_dirty = False
