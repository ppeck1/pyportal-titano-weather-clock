# app/icon_sheet.py — Shared weather icon sheet loader
# Loads the icon bitmap/palette once and reuses them across pages.

import displayio
from app import config, theme

_HAS_IMAGELOAD = True
try:
    import adafruit_imageload
except Exception:
    _HAS_IMAGELOAD = False

_BITMAP = None
_PALETTE = None
_LOAD_FAILED = False


def get_shared_icon_sheet():
    """Return (bitmap, palette) for the shared weather icon sheet, or (None, None)."""
    global _BITMAP, _PALETTE, _LOAD_FAILED

    if _BITMAP is not None and _PALETTE is not None:
        return _BITMAP, _PALETTE
    if _LOAD_FAILED or not _HAS_IMAGELOAD:
        return None, None

    try:
        bmp, pal = adafruit_imageload.load(
            config.ICON_SHEET,
            bitmap=displayio.Bitmap,
            palette=displayio.Palette,
        )

        iw, ih = theme.ICON_W, theme.ICON_H
        bg_indices = set()
        cols = bmp.width // iw
        rows = bmp.height // ih
        for ty in range(rows):
            for tx in range(cols):
                bg_indices.add(bmp[tx * iw, ty * ih])

        for idx in bg_indices:
            try:
                pal.make_transparent(idx)
            except Exception:
                pass

        _BITMAP = bmp
        _PALETTE = pal
        return _BITMAP, _PALETTE
    except Exception as e:
        print("Icon sheet load failed:", e)
        _LOAD_FAILED = True
        return None, None
