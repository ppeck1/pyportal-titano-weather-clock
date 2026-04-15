# app/pages/hero_page.py — Hero page (Clock + Weather)
# Preserves the original portrait layout: icon | temp on top, clock bottom.
# This is the primary ambient display; visual identity of the whole project.

import time
import displayio
from app.pages.base_page import BasePage
from app import theme, config
from app.icon_sheet import get_shared_icon_sheet
from app.ui_helpers import (
    load_font, make_label, bbox_scaled, fit_label_to_box,
    fmt_time, fmt_weekday, fmt_date_line, fmt_stale_age
)


class HeroPage(BasePage):

    def _build(self):
        d = self._display
        W, H = d.width, d.height
        font = load_font(config.FONT_MAIN)

        # ── Background ────────────────────────────────────────────────────────
        bg_pal = displayio.Palette(1)
        bg_pal[0] = theme.C_BG
        bg_bmp = displayio.Bitmap(W, H, 1)
        self.group.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

        # ── Temperature label ─────────────────────────────────────────────────
        self._temp_lbl = make_label(font, "--" + config.TEMP_SUFFIX, theme.C_TEMP, scale=2)
        self.group.append(self._temp_lbl)

        # ── Clock label ───────────────────────────────────────────────────────
        self._time_lbl = make_label(font, "--:--", theme.C_TIME, scale=4)
        self._time_lbl.anchor_point = (0.5, 0.0)
        self.group.append(self._time_lbl)

        # ── Weekday / date ────────────────────────────────────────────────────
        self._weekday_lbl = make_label(font, "Weekday", theme.C_DATE,
                                       scale=theme.WEEKDAY_SCALE)
        self._weekday_lbl.anchor_point = (0.5, 1.0)
        self.group.append(self._weekday_lbl)

        self._date_lbl = make_label(font, "Month Day, Year", theme.C_DATE,
                                    scale=theme.DATE_SCALE)
        self._date_lbl.anchor_point = (0.5, 1.0)
        self.group.append(self._date_lbl)

        # ── Stale / offline indicator ─────────────────────────────────────────
        self._status_lbl = make_label(font, "", theme.C_STALE, scale=1)
        self._status_lbl.anchor_point = (1.0, 0.0)   # top-right
        self.group.append(self._status_lbl)

        # ── Weather icon sheet ────────────────────────────────────────────────
        self._icon_group = None
        self._icon_grid  = None
        self._sheet_bmp, self._sheet_pal = get_shared_icon_sheet()
        if self._sheet_bmp and self._sheet_pal:
            try:
                iw, ih = theme.ICON_W, theme.ICON_H
                self._icon_grid = displayio.TileGrid(
                    self._sheet_bmp, pixel_shader=self._sheet_pal,
                    width=1, height=1,
                    tile_width=iw, tile_height=ih,
                )
                self._icon_group = displayio.Group(scale=1)
                self._icon_group.append(self._icon_grid)
                self.group.append(self._icon_group)
            except Exception as e:
                print("HeroPage: icon init failed:", e)
                self._icon_grid = None
                self._icon_group = None

        self._last_min = -1
        self._W = W
        self._H = H
        self._do_layout()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _do_layout(self):
        W, H = self._W, self._H
        P = theme.PAD
        top_h  = int(H * theme.TOP_H_FRACTION)
        left_w = int(W * theme.SPLIT_LEFT)

        # Date at very bottom
        self._date_lbl.anchored_position = (W // 2, H - P)
        # Weekday above date
        dh = self._date_lbl.bounding_box[3] * self._date_lbl.scale
        self._weekday_lbl.anchored_position = (W // 2, H - P - dh - 2)

        # Clock fills space between divider and weekday
        clock_top = top_h + P * 2
        wday_top  = (self._weekday_lbl.anchored_position[1]
                     - self._weekday_lbl.bounding_box[3] * self._weekday_lbl.scale)
        clock_h   = max(20, wday_top - clock_top - P)
        self._time_lbl.scale = fit_label_to_box(self._time_lbl, int(W * 0.90), clock_h,
                                                max_scale=theme.CLOCK_MAX_SCALE,
                                                min_scale=theme.CLOCK_MIN_SCALE)
        self._time_lbl.anchored_position = (W // 2, clock_top)

        # Top-left icon box
        if self._icon_group is not None:
            ix = max(P, (left_w - theme.ICON_W) // 2)
            iy = max(P + 2, (top_h - theme.ICON_H) // 2)
            self._icon_group.x = ix
            self._icon_group.y = iy

        # Temp centered in right half of top zone
        tb_w = self._temp_lbl.bounding_box[2] * self._temp_lbl.scale
        tb_h = self._temp_lbl.bounding_box[3] * self._temp_lbl.scale
        tx = left_w + (W - left_w - tb_w) // 2
        ty = max(P, (top_h - tb_h) // 2)
        self._temp_lbl.x = tx
        self._temp_lbl.y = ty

        # Status top-right
        self._status_lbl.anchored_position = (W - P, P)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self):
        now = time.localtime()
        self._time_lbl.text    = fmt_time(now)
        self._weekday_lbl.text = fmt_weekday(now)
        self._date_lbl.text    = fmt_date_line(now)

        self._temp_lbl.text = self._cache.temp_str(config.TEMP_SUFFIX)

        # Weather icon index
        if self._icon_grid is not None:
            try:
                self._icon_grid[0] = int(self._cache.icon_index)
            except Exception:
                pass

        # Offline / stale indicator
        if not self._state.wifi_connected:
            self._status_lbl.text  = "OFFLINE"
            self._status_lbl.color = theme.C_ERR
        else:
            age = self._state.stale_age_secs(self._state.last_weather_sync)
            if age is None or age > theme.STALE_THRESHOLD_SECS:
                self._status_lbl.text  = fmt_stale_age(age)
                self._status_lbl.color = theme.C_STALE
            else:
                self._status_lbl.text  = ""
                self._status_lbl.color = theme.C_STALE

        self._do_layout()

    def update(self, now_struct):
        if now_struct.tm_min != self._last_min:
            self._last_min = now_struct.tm_min
            self._dirty = True
        if self._state.time_dirty or self._state.weather_dirty:
            self._dirty = True
            self._state.time_dirty = False
            self._state.weather_dirty = False
