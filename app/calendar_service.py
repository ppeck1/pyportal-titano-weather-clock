# app/calendar_service.py — Calendar data service
# Reads calendar events from the dashboard.json feed.
# Never touches Google APIs directly.

from app import config

class CalendarService:
    def __init__(self, cache):
        self._cache = cache

    def ingest(self, events):
        """Accepts a list of {time, title} dicts from dashboard feed."""
        try:
            self._cache.calendar = [
                {"time": str(e.get("time", "")),
                 "title": str(e.get("title", ""))}
                for e in (events or [])
            ][:5]
        except Exception as e:
            print("CalendarService: ingest failed:", e)

    def update_if_due(self, state):
        """No-op: calendar is updated via dashboard_service.update_if_due()."""
        pass
