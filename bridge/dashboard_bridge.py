#!/usr/bin/env python3
"""
bridge/dashboard_bridge.py — Dashboard JSON Bridge Service
==========================================================
Runs on a home server / Raspberry Pi / cloud function.
Fetches Google Calendar + Tasks, combines with Open-Meteo weather,
and serves a compact dashboard.json that the PyPortal consumes.

Requirements:
    pip install flask google-auth google-api-python-client requests

Setup:
    1. Create a Google Cloud project.
    2. Enable Calendar API and Tasks API.
    3. Download OAuth credentials as credentials.json into this directory.
    4. Run once interactively to complete OAuth flow: python dashboard_bridge.py
    5. A token.json will be saved for future headless runs.
    6. Set LATITUDE, LONGITUDE, TIMEZONE, and USE_FAHRENHEIT below.
    7. Deploy as a systemd service or cron job.
    8. Set DASHBOARD_JSON_URL in your settings.toml to http://<server>:5050/dashboard.json
"""

import os
import json
import datetime
import requests
from flask import Flask, jsonify

# ── Local config ──────────────────────────────────────────────────────────────
LATITUDE      = 40.11
LONGITUDE     = -82.93
TIMEZONE      = "America/New_York"
USE_FAHRENHEIT = True
TEMP_UNIT     = "fahrenheit" if USE_FAHRENHEIT else "celsius"

MAX_EVENTS = 3
MAX_TASKS  = 5

PORT = 5050

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── Google auth ───────────────────────────────────────────────────────────────
_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
]

def _get_google_creds():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request as GRequest

    creds = None
    token_path = os.path.join(os.path.dirname(__file__), "token.json")
    cred_path  = os.path.join(os.path.dirname(__file__), "credentials.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds

# ── Calendar fetch ────────────────────────────────────────────────────────────
def fetch_calendar_events():
    try:
        from googleapiclient.discovery import build
        creds  = _get_google_creds()
        svc    = build("calendar", "v3", credentials=creds)
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        result  = svc.events().list(
            calendarId="primary",
            timeMin=now_iso,
            maxResults=MAX_EVENTS,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = []
        for item in result.get("items", []):
            start = item.get("start", {})
            dt    = start.get("dateTime", start.get("date", ""))
            # Format time portion only
            try:
                parsed = datetime.datetime.fromisoformat(dt.replace("Z", "+00:00"))
                time_str = parsed.strftime("%-I:%M %p")
            except Exception:
                time_str = dt[:10]
            events.append({
                "time":  time_str,
                "title": item.get("summary", "")[:30],
            })
        return events
    except Exception as e:
        print("Calendar fetch error:", e)
        return []

# ── Tasks fetch ───────────────────────────────────────────────────────────────
def fetch_tasks():
    try:
        from googleapiclient.discovery import build
        creds = _get_google_creds()
        svc   = build("tasks", "v1", credentials=creds)
        result = svc.tasks().list(
            tasklist="@default",
            maxResults=MAX_TASKS,
            showCompleted=False,
        ).execute()
        tasks = []
        for item in result.get("items", []):
            tasks.append({
                "title":    item.get("title", "")[:30],
                "priority": "normal",   # Tasks API has no priority field
            })
        return tasks
    except Exception as e:
        print("Tasks fetch error:", e)
        return []

# ── Weather fetch (Open-Meteo, server-side for richer data) ───────────────────
def fetch_weather():
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LATITUDE}&longitude={LONGITUDE}"
            f"&current=temperature_2m,weather_code"
            f"&hourly=temperature_2m,weather_code"
            f"&temperature_unit={TEMP_UNIT}"
            f"&forecast_days=1"
        )
        r    = requests.get(url, timeout=10)
        data = r.json()
        cur  = data.get("current", {})
        temp = cur.get("temperature_2m")
        code = cur.get("weather_code", 0)

        # Build hourly forecast
        hourly = data.get("hourly", {})
        temps  = hourly.get("temperature_2m", [])
        codes  = hourly.get("weather_code", [])
        now_h  = datetime.datetime.now().hour
        forecast = []
        for i in range(now_h, now_h + 5):
            if i >= len(temps):
                break
            h    = i % 12 or 12
            ampm = "AM" if i < 12 else "PM"
            forecast.append({
                "label": f"{h} {ampm}",
                "temp":  round(temps[i], 1),
                "code":  int(codes[i]) if i < len(codes) else 0,
            })

        return {
            "current_temp": round(temp, 1) if temp is not None else None,
            "weather_code": int(code),
            "forecast":     forecast,
        }
    except Exception as e:
        print("Weather fetch error:", e)
        return {}

# ── Endpoint ──────────────────────────────────────────────────────────────────
@app.route("/dashboard.json")
def dashboard():
    now_iso = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    payload = {
        "generated_at": now_iso,
        "timezone":     TIMEZONE,
        "weather":      fetch_weather(),
        "calendar":     fetch_calendar_events(),
        "tasks":        fetch_tasks(),
    }
    return jsonify(payload)

@app.route("/health")
def health():
    return "ok"

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Dashboard bridge running on http://0.0.0.0:{PORT}/dashboard.json")
    app.run(host="0.0.0.0", port=PORT, debug=False)
