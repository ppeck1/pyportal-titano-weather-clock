# PyPortal Titano — Portrait UI
# Top row: [ icon | temperature ]  (50/50 split)
# Divider (dim gray)
# Big HH:MM clock (no seconds)
# Two-line date at bottom (Weekday line larger)
#
# CircuitPython 10.x, ESP32 AirLift (esp32spi) + adafruit_requests.Session

import os, time, board, busio, digitalio, rtc, displayio, terminalio
from adafruit_display_text import label
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socketpool as esp_socketpool
import adafruit_requests

# ----- Optional icon support -----
HAS_IMAGELoad = True
try:
    import adafruit_imageload
except Exception:
    HAS_IMAGELoad = False

# ----- Font (04b30) with fallback -----
try:
    from adafruit_bitmap_font import bitmap_font
    FONT = bitmap_font.load_font("/fonts/04b30-20.bdf")
except Exception:
    FONT = terminalio.FONT

# ----- Auto-brightness (light sensor) -----
from analogio import AnalogIn
AUTO_DIM = True           # set False to use FIXED_BRIGHTNESS
FIXED_BRIGHTNESS = 0.75   # used when AUTO_DIM=False
MIN_BRIGHT = 0.12
MAX_BRIGHT = 1.00
DIM_UPDATE_SECS = 2.0

try:
    import ssl
    SSL_CTX = ssl.create_default_context()
except Exception:
    SSL_CTX = None

# ---------- Display (portrait) ----------
display = board.DISPLAY
display.rotation = 270          # 90 or 270; change if upside-down for your mount
W, H = display.width, display.height  # (240 x 320 in portrait on Titano)
root = displayio.Group()
display.root_group = root

# Light sensor
try:
    light = AnalogIn(board.LIGHT)
except Exception:
    light = None

def set_brightness(v):
    try:
        display.brightness = max(0.0, min(1.0, v))
    except Exception:
        pass

# ---------- Layout constants ----------
PAD = 8
TOP_H_FRACTION = 0.55       # how much height the top row uses (icon + temp)
SPLIT_LEFT = 0.50           # 50/50 split between icon and temp
TEMP_MIN_SCALE, TEMP_MAX_SCALE = 1, 6
CLOCK_MIN_SCALE, CLOCK_MAX_SCALE = 1, 7
WEEKDAY_SCALE = 2           # larger weekday
DATE_SCALE = 1              # month/day/year line

DIVIDER_COLOR = 0x606060    # dim gray
DIVIDER_THICK = 2           # px

ICON_W, ICON_H = 32, 32
ICON_PAD = 4

# ---------- APIs / Config ----------
TIMEZONE_API_PRIMARY  = "http://worldtimeapi.org/api/ip"
TIMEZONE_API_FALLBACK = "http://worldtimeapi.org/api/timezone/America/New_York"
UTC_OFFSET = None  # None uses API; or set e.g. -4 to force EDT

LATITUDE, LONGITUDE = 40.0, -100.0
USE_FAHRENHEIT = True
TEMP_UNIT = "fahrenheit" if USE_FAHRENHEIT else "celsius"
WEATHER_REFRESH_SECS = 10 * 60
TIME_RESYNC_SECS     = 10 * 60

OPEN_METEO_URL = (
    "http://api.open-meteo.com/v1/forecast?"
    f"latitude={LATITUDE}&longitude={LONGITUDE}"
    f"&current=temperature_2m,weather_code"
    f"&temperature_unit={TEMP_UNIT}"
)

ICON_SHEET = "/weather_icons_32x32_9.bmp"  # or "/weather_icons_32x32_9_v2.bmp"

# ---------- Wi-Fi ----------
SSID = os.getenv("CIRCUITPY_WIFI_SSID")
PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp32_cs  = digitalio.DigitalInOut(board.ESP_CS)
esp32_rdy = digitalio.DigitalInOut(board.ESP_BUSY)
esp32_rst = digitalio.DigitalInOut(board.ESP_RESET)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_rdy, esp32_rst)

pool = esp_socketpool.SocketPool(esp)
requests = adafruit_requests.Session(pool, SSL_CTX)

def try_wifi(max_tries=6):
    if not SSID or not PASSWORD:
        return False
    for _ in range(max_tries):
        try:
            esp.connect_AP(bytes(SSID, "utf-8"), bytes(PASSWORD, "utf-8"))
            return True
        except Exception:
            time.sleep(1.5)
    return esp.is_connected

def _sync_time_once(url):
    r = requests.get(url, timeout=8)
    data = r.json()
    r.close()
    epoch = int(data["unixtime"])
    if UTC_OFFSET is None:
        offset = int(data.get("raw_offset", 0)) + int(data.get("dst_offset", 0))
    else:
        offset = int(UTC_OFFSET * 3600)
    rtc.RTC().datetime = time.localtime(epoch + offset)

def sync_time_with_retries():
    urls = [TIMEZONE_API_PRIMARY, TIMEZONE_API_FALLBACK]
    delay = 1.5
    for _ in range(5):
        for url in urls:
            try:
                _sync_time_once(url)
                if time.localtime().tm_year >= 2020:
                    return True
            except Exception:
                pass
        time.sleep(delay)
        delay = min(delay + 1.0, 5.0)
    return False

wifi_ok = try_wifi()
time.sleep(2)
if wifi_ok:
    sync_time_with_retries()

# ---------- Weather → icon index map ----------
def icon_index_for_code(c):
    c=int(c)
    if c==0:return 0          # Clear
    if c in (1,2):return 1    # Mainly clear/Partly cloudy
    if c==3:return 2          # Overcast
    if c in (51,53,55,56,57):return 3  # Drizzle / freezing drizzle
    if c in (61,63,65,66,67):return 4  # Rain / freezing rain
    if c in (80,81,82):return 5        # Showers
    if c in (95,96,97):return 6        # Thunder
    if c in (71,73,75,77,85,86):return 7  # Snow
    if c in (45,48):return 8           # Fog
    return 2

# ---------- UI elements ----------
# Temperature (top-right box)
temp_lbl = label.Label(FONT, text="--°F", scale=2)
temp_lbl.anchor_point = (0.5, 0.5)  # centered in its box
root.append(temp_lbl)

# Clock + date (bottom)
time_lbl = label.Label(FONT, text="--:--", scale=4)
time_lbl.anchor_point = (0.5, 0.0)   # centered, top inside its area
root.append(time_lbl)

weekday_lbl = label.Label(FONT, text="Weekday", scale=WEEKDAY_SCALE)
weekday_lbl.anchor_point = (0.5, 1.0)  # centered, above the very bottom
root.append(weekday_lbl)

date_lbl = label.Label(FONT, text="Month Day, Year", scale=DATE_SCALE)
date_lbl.anchor_point = (0.5, 1.0)     # centered, at bottom
root.append(date_lbl)

# Divider (bitmap + palette, then scaled to full width)
divider_palette = displayio.Palette(1)
divider_palette[0] = DIVIDER_COLOR
divider_bitmap = None
divider_tg = None

def build_divider(width, y):
    global divider_bitmap, divider_tg
    # Rebuild a 1xTHICK bmp and scale/stretch by TileGrid width isn't supported,
    # so we just create a bitmap of the full width.
    divider_bitmap = displayio.Bitmap(width, DIVIDER_THICK, 1)
    divider_tg = displayio.TileGrid(divider_bitmap, pixel_shader=divider_palette, x=0, y=y)
    root.append(divider_tg)

# Icon holder (group recreated to change scale safely on CP10)
icon_group = None
icon_grid = None
if HAS_IMAGELoad:
    try:
        sheet_bitmap, sheet_palette = adafruit_imageload.load(
            ICON_SHEET,
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        # Smart transparency: mark top-left of each tile as transparent
        try:
            bg_idx = set()
            tiles_across = sheet_bitmap.width // ICON_W
            tiles_down   = sheet_bitmap.height // ICON_H
            for ty in range(tiles_down):
                for tx in range(tiles_across):
                    px = tx * ICON_W
                    py = ty * ICON_H
                    bg_idx.add(sheet_bitmap[px, py])
            for idx in bg_idx:
                try: sheet_palette.make_transparent(idx)
                except Exception: pass
        except Exception:
            try: sheet_palette.make_transparent(0)
            except Exception: pass

        icon_grid = displayio.TileGrid(
            sheet_bitmap,
            pixel_shader=sheet_palette,
            width=1, height=1,
            tile_width=ICON_W, tile_height=ICON_H
        )
        icon_group = displayio.Group(scale=1)
        icon_group.append(icon_grid)
        root.append(icon_group)
    except Exception:
        icon_group = None
        icon_grid = None

# ---------- Helpers ----------
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

def fmt_time(t):  # NO SECONDS
    return f"{t.tm_hour:02d}:{t.tm_min:02d}"

WD_FULL = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
MO_FULL = ["January","February","March","April","May","June","July","August","September","October","November","December"]
def fmt_weekday(t): return WD_FULL[t.tm_wday]
def fmt_date_line(t): return f"{MO_FULL[t.tm_mon-1]} {t.tm_mday}, {t.tm_year}"

def refresh_layout():
    # Regions
    top_h = int(H * TOP_H_FRACTION)
    bottom_y = top_h + PAD

    # Divider placement
    # Clear any existing divider
    global divider_tg
    try:
        if divider_tg in root:
            root.remove(divider_tg)
    except Exception:
        pass
    ###build_divider(W, bottom_y - (DIVIDER_THICK // 2))

    # --- Bottom block: time + weekday + date (anchored to bottom)
    # Date at very bottom
    date_lbl.anchored_position = (W // 2, H - PAD)
    # Weekday just above date with a tiny gap
    weekday_lbl.anchored_position = (W // 2, H - PAD - (date_lbl.bounding_box[3] * date_lbl.scale) - 2)

    # Clock area from divider down to above weekday line
    clock_top = bottom_y + PAD
    clock_bottom = weekday_lbl.anchored_position[1] - (weekday_lbl.bounding_box[3] * weekday_lbl.scale) - 6
    clock_h = max(8, clock_bottom - clock_top)
    fit_label_to_box(time_lbl, W - 2 * PAD, clock_h, min_scale=CLOCK_MIN_SCALE, max_scale=CLOCK_MAX_SCALE)
    # Center clock vertically in its area; top-anchor used, so compute y:
    _, time_h = bbox_scaled(time_lbl)
    time_y = clock_top + (clock_h - time_h) // 2
    time_lbl.anchored_position = (W // 2, time_y)

    # --- Top row: left = icon, right = temperature (centered)
    left_w = int(W * SPLIT_LEFT)
    right_w = W - left_w

    # Icon box
    icon_box_x = PAD
    icon_box_y = PAD
    icon_box_w = left_w - 2 * PAD
    icon_box_h = top_h - 2 * PAD

    # Temp box
    temp_box_x = left_w
    temp_box_y = PAD
    temp_box_w = right_w - PAD
    temp_box_h = top_h - 2 * PAD

    # Fit/center temp in its box
    fit_label_to_box(temp_lbl, temp_box_w, temp_box_h, min_scale=TEMP_MIN_SCALE, max_scale=TEMP_MAX_SCALE)
    temp_lbl.anchored_position = (temp_box_x + temp_box_w // 2, temp_box_y + temp_box_h // 2)

    # Scale+center icon
    global icon_group, icon_grid
    if icon_group is not None and icon_grid is not None:
        max_s_w = max(1, (icon_box_w - ICON_PAD) // ICON_W)
        max_s_h = max(1, (icon_box_h - ICON_PAD) // ICON_H)
        scale = max(1, min(max_s_w, max_s_h))

        try:
            if icon_group in root: root.remove(icon_group)
        except Exception: pass
        try:
            if icon_grid in icon_group: icon_group.remove(icon_grid)
        except Exception: pass

        icon_group = displayio.Group(scale=scale)
        icon_group.append(icon_grid)

        icon_px_w = ICON_W * scale
        icon_px_h = ICON_H * scale
        icon_group.x = icon_box_x + (icon_box_w - icon_px_w) // 2
        icon_group.y = icon_box_y + (icon_box_h - icon_px_h) // 2
        root.append(icon_group)

# ---------- Weather fetch ----------
def fetch_weather_update():
    """Returns temp text and sets icon tile if available."""
    try:
        r = requests.get(OPEN_METEO_URL, timeout=8)
        data = r.json()
        r.close()
        cur = data.get("current", {})
        temp = cur.get("temperature_2m")
        code = cur.get("weather_code")

        if icon_grid is not None and code is not None:
            try:
                icon_grid[0] = icon_index_for_code(code)
            except Exception:
                pass

        if temp is None:
            return None
        unit = "°F" if USE_FAHRENHEIT else "°C"
        return f"{temp:.0f}{unit}"
    except Exception:
        return None

# ---------- Initial draw ----------
now = time.localtime()
temp_text = fetch_weather_update() if wifi_ok else None
temp_lbl.text = temp_text if temp_text else "--°F"
weekday_lbl.text = fmt_weekday(now)
date_lbl.text = fmt_date_line(now)
time_lbl.text = fmt_time(now)
refresh_layout()

# ---------- Loop ----------
last_minute = -1
last_wx = time.monotonic()
last_dim = 0.0
last_time_sync = time.monotonic()

if now.tm_year < 2020 and wifi_ok:
    sync_time_with_retries()
    last_time_sync = time.monotonic()

# Initial brightness
if AUTO_DIM and light is not None:
    set_brightness(MAX_BRIGHT)   # will settle on first cycle
else:
    set_brightness(FIXED_BRIGHTNESS)

while True:
    now_mono = time.monotonic()
    now = time.localtime()

    # Auto-dim
    if AUTO_DIM and light is not None and (now_mono - last_dim) >= DIM_UPDATE_SECS:
        frac = light.value / 65535.0
        frac = frac ** 0.6
        target = MIN_BRIGHT + (MAX_BRIGHT - MIN_BRIGHT) * frac
        set_brightness(target)
        last_dim = now_mono

    # Re-sync time periodically
    if wifi_ok and (now_mono - last_time_sync) >= TIME_RESYNC_SECS:
        if sync_time_with_retries():
            last_time_sync = now_mono

    # Update clock/date once per minute
    if now.tm_min != last_minute:
        time_lbl.text = fmt_time(now)
        weekday_lbl.text = fmt_weekday(now)
        date_lbl.text = fmt_date_line(now)
        last_minute = now.tm_min
        refresh_layout()

    # Weather refresh
    if wifi_ok and (now_mono - last_wx) >= WEATHER_REFRESH_SECS:
        t = fetch_weather_update()
        if t:
            temp_lbl.text = t
            refresh_layout()
        last_wx = now_mono

    time.sleep(0.05)
