# app/ui_helpers.py — Shared display utilities
# Formatting helpers and label-fitting logic.
# Pages import from here; no display state stored here.

import time
import terminalio
import displayio
from adafruit_display_text import label as adafruit_label

try:
    from adafruit_bitmap_font import bitmap_font
    _HAS_FONT = True
except Exception:
    _HAS_FONT = False

# ── Font loader ───────────────────────────────────────────────────────────────
_font_cache = {}

def load_font(path):
    """Load BDF font with cache and fallback to terminalio."""
    if path in _font_cache:
        return _font_cache[path]
    if _HAS_FONT:
        candidates = (path, path.lstrip("/")) if path.startswith("/") else (path, "/" + path)
        for candidate in candidates:
            try:
                f = bitmap_font.load_font(candidate)
                print("Font load: ok path={}".format(candidate))
                _font_cache[path] = f
                return f
            except Exception:
                pass
    print("Font load: fallback terminalio path={}".format(path))
    _font_cache[path] = terminalio.FONT
    return terminalio.FONT

# ── Label helpers ─────────────────────────────────────────────────────────────
def make_label(font, text, color, scale=1, anchor=(0.5, 0.5)):
    lbl = adafruit_label.Label(font, text=text, color=color, scale=scale)
    lbl.anchor_point = anchor
    return lbl

def bbox_scaled(lbl):
    _, _, w, h = lbl.bounding_box
    return w * lbl.scale, h * lbl.scale

def fit_label_to_box(lbl, max_w, max_h, min_scale=1, max_scale=6):
    for s in range(max_scale, min_scale - 1, -1):
        lbl.scale = s
        w, h = bbox_scaled(lbl)
        if w <= max_w and h <= max_h:
            return s
    lbl.scale = min_scale
    return min_scale

def center_in_box(lbl, box_x, box_y, box_w, box_h):
    """Set anchored_position to center label in a bounding box."""
    lbl.anchor_point = (0.5, 0.5)
    lbl.anchored_position = (box_x + box_w // 2, box_y + box_h // 2)

def place_label(lbl, x, y, anchor=(0.0, 0.0)):
    lbl.anchor_point = anchor
    lbl.anchored_position = (x, y)

# ── Time / date formatting ────────────────────────────────────────────────────
WD_FULL = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MO_FULL = ("January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December")

def fmt_time(t):
    return "{:02d}:{:02d}".format(t.tm_hour, t.tm_min)

def fmt_time_12(t):
    h = t.tm_hour % 12 or 12
    am = "AM" if t.tm_hour < 12 else "PM"
    return "{:d}:{:02d} {}".format(h, t.tm_min, am)

def fmt_weekday(t):
    return WD_FULL[t.tm_wday]

def fmt_date_line(t):
    return "{} {}, {}".format(MO_FULL[t.tm_mon - 1], t.tm_mday, t.tm_year)

def fmt_date_short(t):
    return "{}/{}/{}".format(t.tm_mon, t.tm_mday, t.tm_year)

def fmt_duration(secs):
    secs = max(0, int(secs))
    m, s = divmod(secs, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return "{:d}:{:02d}:{:02d}".format(h, m, s)
    return "{:02d}:{:02d}".format(m, s)

def fmt_stale_age(secs):
    if secs is None:
        return "never synced"
    if secs < 60:
        return "just now"
    if secs < 3600:
        return "{:.0f}m ago".format(secs / 60)
    return "{:.0f}h ago".format(secs / 3600)

# ── Divider bitmap ────────────────────────────────────────────────────────────
def make_divider(width, thick, color):
    pal = displayio.Palette(1)
    pal[0] = color
    bmp = displayio.Bitmap(width, thick, 1)
    tg = displayio.TileGrid(bmp, pixel_shader=pal)
    return tg

# ── Truncation ────────────────────────────────────────────────────────────────
def truncate(s, max_chars):
    if len(s) <= max_chars:
        return s
    return s[:max_chars - 1] + "\u2026"   # ellipsis
