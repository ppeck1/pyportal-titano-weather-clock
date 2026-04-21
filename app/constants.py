# app/constants.py — PyPortal Titano Ambient Dashboard
# All app-wide string constants, enums, and magic numbers.

# ── App states ──────────────────────────────────────────────────────────────
BOOT              = "BOOT"
CONNECTING_WIFI   = "CONNECTING_WIFI"
SYNCING_TIME      = "SYNCING_TIME"
AMBIENT_ROTATE    = "AMBIENT_ROTATE"
MANUAL_NAV        = "MANUAL_NAV"
FOCUSED_VIEW      = "FOCUSED_VIEW"
ALARM_ACTIVE      = "ALARM_ACTIVE"
ERROR_RECOVERABLE = "ERROR_RECOVERABLE"

# ── Input events ─────────────────────────────────────────────────────────────
BTN_BACK = "BACK"
BTN_HOME = "HOME"
BTN_NEXT = "NEXT"

# ── Default hardware config ──────────────────────────────────────────────────
DEFAULT_PIN_BACK = "D3"
DEFAULT_PIN_HOME = ""
DEFAULT_PIN_NEXT = "D4"
DEFAULT_DEBOUNCE_SECS = 0.075

# ── Page indices ─────────────────────────────────────────────────────────────
PAGE_HERO     = 0
PAGE_FORECAST = 1
PAGE_CALENDAR = 2
PAGE_TASKS    = 3
PAGE_TIMER    = 4
PAGE_ALARM    = 5
PAGE_STATUS   = 6
PAGE_COUNT    = 7

PAGE_LABELS = ("CLOCK", "FORECAST", "CALENDAR", "TASKS", "TIMER", "ALARM", "STATUS")

# ── Timer states ─────────────────────────────────────────────────────────────
TIMER_IDLE      = "IDLE"
TIMER_SELECTING = "SELECTING"
TIMER_RUNNING   = "RUNNING"
TIMER_COMPLETE  = "COMPLETE"

TIMER_PRESETS       = (60, 300, 600, 1500)        # seconds
TIMER_PRESET_LABELS = ("1 min", "5 min", "10 min", "25 min")

# ── Alarm states ─────────────────────────────────────────────────────────────
ALARM_IDLE    = "IDLE"
ALARM_RINGING = "RINGING"

# ── Audio patterns ────────────────────────────────────────────────────────────
AUDIO_CLICK      = "click"
AUDIO_TIMER_DONE = "timer_done"
AUDIO_ALARM      = "alarm"

# ── Icon mapping (WMO weather code → sprite row index) ───────────────────────
# Sheet has 9 icons across a single row: 0=Clear 1=PartlyCloudy 2=Overcast
# 3=Drizzle 4=Rain 5=Showers 6=Thunder 7=Snow 8=Fog
WMO_MAP = (
    # (codes tuple, icon_index)
    ((0,),               0),
    ((1, 2),             1),
    ((3,),               2),
    ((51, 53, 55, 56, 57), 3),
    ((61, 63, 65, 66, 67), 4),
    ((80, 81, 82),       5),
    ((95, 96, 97),       6),
    ((71, 73, 75, 77, 85, 86), 7),
    ((45, 48),           8),
)


def icon_index_for_code(code):
    c = int(code)
    for codes, idx in WMO_MAP:
        if c in codes:
            return idx
    return 2  # default overcast


WEATHER_LABELS = (
    "Clear", "Partly Cloudy", "Overcast",
    "Drizzle", "Rain", "Showers",
    "Thunder", "Snow", "Fog"
)
