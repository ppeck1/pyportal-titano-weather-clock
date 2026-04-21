# app/weather_service.py — Weather data service
# Fetches current conditions + hourly forecast from Open-Meteo.
# Falls back to dashboard.json weather block if URL is configured.
# Always writes to cache; never blocks the main loop for long.

import time
from app import config
from app.constants import icon_index_for_code, WEATHER_LABELS

_MIN_FORECAST_ENTRIES = 5


class WeatherService:
    def __init__(self, connectivity, cache):
        self._conn  = connectivity
        self._cache = cache

    def _build_url(self):
        return config.OPEN_METEO_URL.format(
            lat=config.LATITUDE,
            lon=config.LONGITUDE,
            unit=config.TEMP_UNIT,
        )

    def _label_for_hour(self, hour_24):
        return "{:d} {}".format(hour_24 % 12 or 12, "AM" if hour_24 < 12 else "PM")

    def _find_start_index(self, times, current_iso):
        if not times:
            return 0
        if current_iso:
            for i, stamp in enumerate(times):
                if str(stamp) >= str(current_iso):
                    return i
        return 0

    def _normalize_forecast(self, raw_entries):
        forecast = list(raw_entries[:_MIN_FORECAST_ENTRIES])
        if forecast and len(forecast) < _MIN_FORECAST_ENTRIES:
            last = forecast[-1]
            next_hour = last.get("hour_24", time.localtime().tm_hour)
            while len(forecast) < _MIN_FORECAST_ENTRIES:
                next_hour = (next_hour + 1) % 24
                forecast.append({
                    "label": self._label_for_hour(next_hour),
                    "temp":  last.get("temp", 0.0),
                    "code":  last.get("code", 0),
                    "icon":  last.get("icon", 0),
                    "hour_24": next_hour,
                })
        for entry in forecast:
            entry.pop("hour_24", None)
        return forecast

    def fetch(self):
        """
        Fetch weather from Open-Meteo.
        Returns True if successful; cache is updated on success.
        """
        try:
            url = self._build_url()
            print("Weather fetch: requesting {}".format(url))
            data = self._conn.get(url, timeout=10)
            cur  = data.get("current", {})
            temp = cur.get("temperature_2m")
            code = cur.get("weather_code")
            if temp is None:
                print("Weather fetch: failed missing current temperature")
                return False

            self._cache.current_temp  = float(temp)
            self._cache.weather_code  = int(code) if code is not None else 0
            self._cache.icon_index    = icon_index_for_code(self._cache.weather_code)
            self._cache.weather_label = WEATHER_LABELS[self._cache.icon_index]

            # Build hourly forecast (next 5 entries from now, extending into next day if needed)
            hourly = data.get("hourly", {})
            temps  = hourly.get("temperature_2m", [])
            codes  = hourly.get("weather_code", [])
            times  = hourly.get("time", [])
            cur_time = cur.get("time")
            forecast = []
            start_idx = self._find_start_index(times, cur_time)
            for i in range(start_idx, len(temps)):
                if len(forecast) >= _MIN_FORECAST_ENTRIES:
                    break
                t = temps[i]
                c = codes[i] if i < len(codes) else 0
                if i < len(times):
                    try:
                        hour_24 = int(str(times[i]).split("T", 1)[1].split(":", 1)[0])
                    except Exception:
                        hour_24 = i % 24
                else:
                    hour_24 = i % 24
                forecast.append({
                    "label": self._label_for_hour(hour_24),
                    "temp":  float(t),
                    "code":  int(c),
                    "icon":  icon_index_for_code(int(c)),
                    "hour_24": hour_24,
                })
            self._cache.forecast = self._normalize_forecast(forecast)
            print("Weather fetch: success temp={} code={} forecast_items={}".format(
                self._cache.current_temp, self._cache.weather_code, len(self._cache.forecast)
            ))
            return True
        except Exception as e:
            print("WeatherService: fetch failed:", e)
            return False

    def ingest_dashboard(self, weather_block):
        """
        Populate cache from dashboard.json weather section.
        Called by the dashboard aggregator service.
        """
        try:
            temp = weather_block.get("current_temp")
            code = weather_block.get("weather_code", 0)
            self._cache.current_temp  = float(temp) if temp is not None else None
            self._cache.weather_code  = int(code)
            self._cache.icon_index    = icon_index_for_code(int(code))
            self._cache.weather_label = WEATHER_LABELS[self._cache.icon_index]
            raw_fc = weather_block.get("forecast", [])
            forecast = []
            for entry in raw_fc:
                c = int(entry.get("code", 0))
                forecast.append({
                    "label": str(entry.get("label", "")),
                    "temp":  float(entry.get("temp", 0)),
                    "code":  c,
                    "icon":  icon_index_for_code(c),
                })
            self._cache.forecast = self._normalize_forecast(forecast)
        except Exception as e:
            print("WeatherService: ingest_dashboard failed:", e)

    def update_if_due(self, state):
        """Fetch weather on schedule, unless dashboard feed is active."""
        if not state.wifi_connected:
            return
        # If dashboard URL is configured, weather comes from there
        if config.DASHBOARD_JSON_URL:
            return
        now = time.monotonic()
        if (now - state.last_weather_sync) >= config.WEATHER_REFRESH_SECS:
            if self.fetch():
                state.last_weather_sync = time.monotonic()
                state.weather_dirty     = True
