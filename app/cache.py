# app/cache.py — In-memory data cache
# Holds last-known-good data for weather, calendar, tasks.
# Services write; pages read. Survives network outages.

class DataCache:
    def __init__(self):
        # ── Weather ───────────────────────────────────────────────────────────
        self.current_temp  = None   # float
        self.weather_code  = None   # int
        self.weather_label = None   # str
        self.icon_index    = 0      # int 0–8

        # ── Forecast (list of dicts: label, temp, code, icon_index) ──────────
        self.forecast = []

        # ── Calendar (list of dicts: time, title) ────────────────────────────
        self.calendar = []

        # ── Tasks (list of dicts: title, priority) ────────────────────────────
        self.tasks = []

        # ── Source flag ───────────────────────────────────────────────────────
        self.dashboard_generated_at = None   # ISO string from feed

    def has_weather(self):
        return self.current_temp is not None

    def has_calendar(self):
        return len(self.calendar) > 0

    def has_tasks(self):
        return len(self.tasks) > 0

    def temp_str(self, suffix):
        if self.current_temp is None:
            return "--" + suffix
        return "{:.0f}{}".format(self.current_temp, suffix)

# Module-level singleton
cache = DataCache()
