# app/pages/tasks_page.py — Tasks page
# Shows top 5 tasks from the dashboard feed with priority markers.

import displayio
from app.pages.base_page import BasePage
from app import theme, config
from app.ui_helpers import load_font, make_label, truncate

_MAX_TASKS = 5
_PRIORITY_COLORS = {
    "high":   theme.C_PRIORITY,
    "medium": theme.C_VALUE,
    "low":    theme.C_LABEL,
    "normal": theme.C_VALUE,
}
_PRIORITY_BULLETS = {
    "high":   "!",
    "medium": "\u25cf",
    "low":    "\u25cb",
    "normal": "\u25cf",
}


class TasksPage(BasePage):

    def _build(self):
        W, H = self._display.width, self._display.height
        font = load_font(config.FONT_MAIN)
        P    = theme.PAD

        bg_pal    = displayio.Palette(1)
        bg_pal[0] = theme.C_BG
        bg_bmp    = displayio.Bitmap(W, H, 1)
        self.group.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

        title = make_label(font, "TASKS", theme.C_PAGE_TITLE, scale=1)
        title.anchor_point = (0.5, 0.0)
        title.anchored_position = (W // 2, P)
        self.group.append(title)

        self._empty_lbl = make_label(font, "No tasks", theme.C_LABEL, scale=1)
        self._empty_lbl.anchor_point = (0.5, 0.5)
        self._empty_lbl.anchored_position = (W // 2, H // 2)
        self.group.append(self._empty_lbl)

        title_h = 24 + P
        row_h   = (H - title_h - P * 2) // _MAX_TASKS
        self._bullet_lbls = []
        self._task_lbls   = []

        for i in range(_MAX_TASKS):
            y = title_h + i * row_h + row_h // 2

            bullet = make_label(font, "\u25cf", theme.C_VALUE, scale=1)
            bullet.anchor_point = (0.0, 0.5)
            bullet.anchored_position = (P, y)
            self.group.append(bullet)
            self._bullet_lbls.append(bullet)

            lbl = make_label(font, "", theme.C_VALUE, scale=2)
            lbl.anchor_point = (0.0, 0.5)
            lbl.anchored_position = (P + 14, y)
            self.group.append(lbl)
            self._task_lbls.append(lbl)

        self._offline_lbl = make_label(font, "", theme.C_OFFLINE, scale=1)
        self._offline_lbl.anchor_point = (0.5, 1.0)
        self._offline_lbl.anchored_position = (W // 2, H - P)
        self.group.append(self._offline_lbl)

    def _refresh(self):
        tasks    = self._cache.tasks
        has_data = len(tasks) > 0
        self._empty_lbl.text = "" if has_data else "No tasks"

        for i in range(_MAX_TASKS):
            if i < len(tasks):
                task = tasks[i]
                pri  = task.get("priority", "normal").lower()
                self._bullet_lbls[i].text  = _PRIORITY_BULLETS.get(pri, "\u25cf")
                self._bullet_lbls[i].color = _PRIORITY_COLORS.get(pri, theme.C_VALUE)
                self._task_lbls[i].text    = truncate(task.get("title", ""), 13)
                self._task_lbls[i].color   = _PRIORITY_COLORS.get(pri, theme.C_VALUE)
            else:
                self._bullet_lbls[i].text = ""
                self._task_lbls[i].text   = ""

        if not self._state.wifi_connected:
            self._offline_lbl.text = "OFFLINE - cached data"
        elif self._state.is_stale(self._state.last_tasks_sync):
            self._offline_lbl.text = "stale"
        else:
            self._offline_lbl.text = ""

    def update(self, now_struct):
        if self._state.tasks_dirty:
            self._dirty = True
            self._state.tasks_dirty = False
