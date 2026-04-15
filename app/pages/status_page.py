# app/pages/status_page.py — Status / diagnostics page
# Shows Wi-Fi, IP, sync ages, brightness, and build info.

import time
import displayio
from app.pages.base_page import BasePage
from app import theme, config
from app.ui_helpers import load_font, make_label, fmt_stale_age, truncate


def _normalize_generated_at(generated_at):
    if not generated_at:
        return None

    stamp = str(generated_at).strip()
    if not stamp:
        return None

    if stamp.endswith("Z"):
        stamp = stamp[:-1]

    stamp = stamp.replace("T", " ")
    if " " not in stamp:
        return stamp

    date_part, time_part = stamp.split(" ", 1)
    if "+" in time_part:
        time_part = time_part.split("+", 1)[0]
    elif "-" in time_part:
        time_part = time_part.split("-", 1)[0]

    return "{} {}".format(date_part, time_part)


def _parse_generated_at_epoch(generated_at):
    stamp = _normalize_generated_at(generated_at)
    if not stamp or " " not in stamp:
        return None

    try:
        date_part, time_part = stamp.split(" ", 1)
        year_s, month_s, day_s = date_part.split("-", 2)
        hour_s, minute_s, second_s = time_part.split(":", 2)
        second_s = second_s.split(".", 1)[0]
        return time.mktime((
            int(year_s), int(month_s), int(day_s),
            int(hour_s), int(minute_s), int(second_s),
            0, -1, -1,
        ))
    except Exception:
        return None


def _format_age_from_seconds(age_secs):
    if age_secs < 0:
        age_secs = 0
    if age_secs < 60:
        return "just now"
    if age_secs < 3600:
        return "{:.0f}m".format(age_secs / 60)
    if age_secs < 86400:
        return "{:.0f}h".format(age_secs / 3600)
    return "{:.0f}d".format(age_secs / 86400)


def _format_generated_at_short(generated_at):
    stamp = _normalize_generated_at(generated_at)
    if not stamp:
        return None
    if " " in stamp:
        stamp = stamp.split(" ", 1)[1]
    if len(stamp) >= 5 and stamp[2] == ":":
        return stamp[:5]
    return truncate(str(generated_at), 8)


def _format_dashboard_freshness(generated_at, last_dashboard_sync):
    payload_epoch = _parse_generated_at_epoch(generated_at)

    if payload_epoch is not None:
        try:
            now_epoch = time.mktime(time.localtime())
            return _format_age_from_seconds(now_epoch - payload_epoch)
        except Exception:
            pass

    short_stamp = _format_generated_at_short(generated_at)
    if short_stamp:
        return short_stamp

    if last_dashboard_sync:
        try:
            return "sync {}".format(
                _format_age_from_seconds(time.monotonic() - last_dashboard_sync)
            )
        except Exception:
            return "sync ?"

    return "N/A"


class StatusPage(BasePage):

    def _build(self):
        W, H = self._display.width, self._display.height
        font = load_font(config.FONT_MAIN)
        P    = theme.PAD

        bg_pal    = displayio.Palette(1)
        bg_pal[0] = theme.C_BG
        bg_bmp    = displayio.Bitmap(W, H, 1)
        self.group.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

        title = make_label(font, "STATUS", theme.C_PAGE_TITLE, scale=1)
        title.anchor_point = (0.5, 0.0)
        title.anchored_position = (W // 2, P)
        self.group.append(title)

        # Rows: label + value side-by-side
        self._rows = []
        row_defs = [
            "Wi-Fi", "IP", "Weather", "Calendar", "Tasks",
            "Dashboard", "Brightness", "Auto-dim", "Build",
        ]
        title_h = 24 + P
        row_h   = (H - title_h - P) // len(row_defs)

        for i, name in enumerate(row_defs):
            y = title_h + i * row_h + row_h // 2

            k_lbl = make_label(font, name, theme.C_LABEL, scale=1)
            k_lbl.anchor_point = (0.0, 0.5)
            k_lbl.anchored_position = (P, y)
            self.group.append(k_lbl)

            v_lbl = make_label(font, "--", theme.C_VALUE, scale=1)
            v_lbl.anchor_point = (1.0, 0.5)
            v_lbl.anchored_position = (W - P, y)
            self.group.append(v_lbl)
            self._rows.append(v_lbl)

        self._W = W

    def _refresh(self):
        s = self._state

        # Wi-Fi
        if s.wifi_connected:
            self._rows[0].text  = "connected"
            self._rows[0].color = theme.C_OK
        else:
            self._rows[0].text  = "offline"
            self._rows[0].color = theme.C_ERR

        # IP
        self._rows[1].text  = truncate(s.ip_address or "--", 16)
        self._rows[1].color = theme.C_VALUE

        # Sync ages
        wx_age  = s.stale_age_secs(s.last_weather_sync)
        cal_age = s.stale_age_secs(s.last_calendar_sync)
        tsk_age = s.stale_age_secs(s.last_tasks_sync)

        self._rows[2].text  = fmt_stale_age(wx_age)
        self._rows[2].color = theme.C_STALE if s.is_stale(s.last_weather_sync) else theme.C_OK

        self._rows[3].text  = fmt_stale_age(cal_age)
        self._rows[3].color = theme.C_STALE if s.is_stale(s.last_calendar_sync) else theme.C_OK

        self._rows[4].text  = fmt_stale_age(tsk_age)
        self._rows[4].color = theme.C_STALE if s.is_stale(s.last_tasks_sync) else theme.C_OK

        # Dashboard freshness
        self._rows[5].text = _format_dashboard_freshness(
            self._cache.dashboard_generated_at,
            s.last_dashboard_sync,
        )
        self._rows[5].color = (
            theme.C_STALE if s.is_stale(s.last_dashboard_sync) else theme.C_OK
        ) if (self._cache.dashboard_generated_at or s.last_dashboard_sync) else theme.C_VALUE

        # Brightness
        self._rows[6].text  = "{:.0f}%".format(s.brightness * 100)
        self._rows[6].color = theme.C_VALUE

        # Auto-dim
        self._rows[7].text  = "auto" if s.auto_dim else "fixed"
        self._rows[7].color = theme.C_VALUE

        # Build
        self._rows[8].text  = s.build
        self._rows[8].color = theme.C_LABEL

    def update(self, now_struct):
        # Refresh every few seconds while on this page
        self._dirty = True
