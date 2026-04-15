# app/time_service.py — Time sync service
# Syncs RTC via worldtimeapi.org. Periodic resync via update_if_due().
# Falls back gracefully if network is unavailable.

import time
import rtc
from app import config


class TimeService:
    def __init__(self, connectivity):
        self._conn = connectivity
        self._synced = False
        self._last_attempt = 0.0

    def _sync_once(self, url):
        data = self._conn.get(url, timeout=8)
        epoch = int(data["unixtime"])
        raw_off = int(data.get("raw_offset", 0))
        dst_off = int(data.get("dst_offset", 0))
        offset  = raw_off + dst_off
        rtc.RTC().datetime = time.localtime(epoch + offset)

    def sync(self):
        """
        Attempt a single sync pass against primary then fallback URL.
        Returns True if successful.
        """
        urls = (config.TIMEZONE_API_PRIMARY, config.TIMEZONE_API_FALLBACK)
        for url in urls:
            try:
                self._sync_once(url)
                if time.localtime().tm_year >= 2020:
                    self._synced = True
                    return True
            except Exception:
                pass
        return False

    def update_if_due(self, state):
        """Resync if the resync interval has elapsed."""
        if not state.wifi_connected:
            return
        now = time.monotonic()
        elapsed = now - state.last_time_sync
        due = state.last_time_sync == 0.0 or elapsed >= config.TIME_RESYNC_SECS
        if due and (now - self._last_attempt) >= config.TIME_RETRY_SECS:
            self._last_attempt = now
            if self.sync():
                state.last_time_sync = time.monotonic()
                state.time_dirty = True

    @property
    def synced(self):
        return self._synced
