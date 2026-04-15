# app/dashboard_service.py — Unified dashboard feed service
# Fetches /dashboard.json and distributes data to weather/calendar/tasks.
# If DASHBOARD_JSON_URL is empty, falls back to direct Open-Meteo fetch.

import time
from app import config


class DashboardService:
    def __init__(self, connectivity, weather_svc, calendar_svc, tasks_svc):
        self._conn     = connectivity
        self._wx       = weather_svc
        self._cal      = calendar_svc
        self._tasks    = tasks_svc
        self._last_fetch = 0.0

    def fetch(self, state):
        """
        Fetch dashboard.json and distribute data to sub-services.
        Applies per-section fallback: missing sections keep last-good data.
        Returns True if fetch succeeded.
        """
        if not config.DASHBOARD_JSON_URL:
            return False
        try:
            data = self._conn.get(config.DASHBOARD_JSON_URL, timeout=12)

            self._cache_generated_at(data)

            if "weather" in data:
                self._wx.ingest_dashboard(data["weather"])
                state.last_weather_sync = time.monotonic()
                state.weather_dirty = True

            if "calendar" in data:
                self._cal.ingest(data["calendar"])
                state.last_calendar_sync = time.monotonic()
                state.calendar_dirty = True

            if "tasks" in data:
                self._tasks.ingest(data["tasks"])
                state.last_tasks_sync = time.monotonic()
                state.tasks_dirty = True

            state.last_dashboard_sync = time.monotonic()
            return True
        except Exception as e:
            print("DashboardService: fetch failed:", e)
            return False

    def _cache_generated_at(self, data):
        from app.cache import cache
        cache.dashboard_generated_at = data.get("generated_at")

    def update_if_due(self, state):
        if not state.wifi_connected:
            return
        if not config.DASHBOARD_JSON_URL:
            # Fall through to weather_service direct fetch
            self._wx.update_if_due(state)
            return
        now = time.monotonic()
        if (now - state.last_dashboard_sync) >= config.DASHBOARD_REFRESH_SECS:
            self.fetch(state)
