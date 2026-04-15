# app/pages/forecast_page.py — Forecast page
# Shows next 5 hourly forecast periods: icon + time label + temperature.

import displayio
from app.pages.base_page import BasePage
from app import theme, config
from app.icon_sheet import get_shared_icon_sheet
from app.ui_helpers import load_font, make_label, truncate

_MAX_ROWS = 5


class ForecastPage(BasePage):

    def _build(self):
        W, H = self._display.width, self._display.height
        font = load_font(config.FONT_MAIN)
        P    = theme.PAD

        # Background
        bg_pal    = displayio.Palette(1)
        bg_pal[0] = theme.C_BG
        bg_bmp    = displayio.Bitmap(W, H, 1)
        self.group.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

        # Page title
        title = make_label(font, "FORECAST", theme.C_PAGE_TITLE, scale=1)
        title.anchor_point = (0.5, 0.0)
        title.anchored_position = (W // 2, P)
        self.group.append(title)

        # Icon sheet (shared reference)
        self._icon_grids = []
        self._sheet_bmp, self._sheet_pal = get_shared_icon_sheet()

        # Row labels
        self._row_labels = []
        self._row_temps  = []
        title_h = 20 + P
        row_h   = (H - title_h - P) // _MAX_ROWS

        for i in range(_MAX_ROWS):
            y = title_h + i * row_h + row_h // 2

            # Icon
            if self._sheet_bmp and self._sheet_pal:
                grid = displayio.TileGrid(
                    self._sheet_bmp, pixel_shader=self._sheet_pal,
                    width=1, height=1,
                    tile_width=theme.ICON_W, tile_height=theme.ICON_H,
                )
                grp = displayio.Group(scale=1)
                grp.append(grid)
                grp.x = P
                grp.y = y - theme.ICON_H // 2
                self.group.append(grp)
                self._icon_grids.append(grid)
            else:
                self._icon_grids.append(None)

            icon_offset = theme.ICON_W + P * 2

            # Time label
            lbl = make_label(font, "--", theme.C_LABEL, scale=1)
            lbl.anchor_point = (0.0, 0.5)
            lbl.anchored_position = (icon_offset, y)
            self.group.append(lbl)
            self._row_labels.append(lbl)

            # Temp label (right-aligned)
            tmp = make_label(font, "--", theme.C_VALUE, scale=2)
            tmp.anchor_point = (1.0, 0.5)
            tmp.anchored_position = (W - P, y)
            self.group.append(tmp)
            self._row_temps.append(tmp)

        self._W = W

    def _refresh(self):
        forecast = self._cache.forecast
        for i in range(_MAX_ROWS):
            if i < len(forecast):
                entry = forecast[i]
                if self._icon_grids[i] is not None:
                    try:
                        self._icon_grids[i][0] = entry.get("icon", 0)
                    except Exception:
                        pass
                self._row_labels[i].text = truncate(entry.get("label", "--"), 8)
                self._row_labels[i].color = theme.C_LABEL
                self._row_temps[i].text  = "{:.0f}{}".format(
                    entry.get("temp", 0), config.TEMP_SUFFIX)
                self._row_temps[i].color = theme.C_VALUE
            else:
                if self._icon_grids[i] is not None:
                    try:
                        self._icon_grids[i][0] = 0
                    except Exception:
                        pass
                self._row_labels[i].text = "--"
                self._row_temps[i].text  = "--"

    def update(self, now_struct):
        if self._state.weather_dirty:
            self._dirty = True
            self._state.weather_dirty = False
