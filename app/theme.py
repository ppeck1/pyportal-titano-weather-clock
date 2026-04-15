# app/theme.py — Color palette and layout metrics
# Dark / minimal aesthetic. Do not change without preserving the ambient feel.

# ── Raw palette ───────────────────────────────────────────────────────────────
BLACK    = 0x000000
WHITE    = 0xFFFFFF
DIM_GRAY = 0x606060
MID_GRAY = 0x909090
LT_GRAY  = 0xBBBBBB
WARM     = 0xFFEECC
RED      = 0xFF3333
AMBER    = 0xFFAA00
BLUE     = 0x4488FF
GREEN    = 0x44BB44

# ── Semantic colors ───────────────────────────────────────────────────────────
C_BG         = BLACK
C_TIME       = WHITE
C_DATE       = LT_GRAY
C_TEMP       = WHITE
C_DIVIDER    = DIM_GRAY
C_LABEL      = MID_GRAY
C_VALUE      = LT_GRAY
C_STALE      = AMBER
C_OFFLINE    = RED
C_PRIORITY   = AMBER
C_ACTIVE     = BLUE
C_OK         = GREEN
C_ERR        = RED
C_PAGE_TITLE = MID_GRAY

# ── Layout ────────────────────────────────────────────────────────────────────
PAD           = 8
LINE_GAP      = 4
DIVIDER_THICK = 2
ICON_W        = 32
ICON_H        = 32
ICON_PAD      = 4

# Hero page proportions
TOP_H_FRACTION = 0.55   # top weather/icon zone
SPLIT_LEFT     = 0.50   # icon/temp horizontal split

# Label scale limits
TEMP_MIN_SCALE  = 1; TEMP_MAX_SCALE  = 6
CLOCK_MIN_SCALE = 1; CLOCK_MAX_SCALE = 7
WEEKDAY_SCALE   = 2
DATE_SCALE      = 1

# Freshness / stale-display threshold
STALE_THRESHOLD_SECS = 1800    # 30 min: weather older than this shows stale indicator
