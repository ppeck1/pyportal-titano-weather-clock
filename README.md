=============================

A portrait-mode weather and clock display built using CircuitPython on the Adafruit PyPortal Titano.
This project demonstrates embedded firmware development, Wi-Fi API integration, display rendering, and real-world hardware interaction.

---

## Overview

This firmware turns the PyPortal Titano into a desk display showing:

| Component | Description |
|----------|------------|
| Time | Large digital clock with smooth refresh |
| Date | Full weekday and MM/DD format |
| Weather | Temp and icon from Open-Meteo API |
| Brightness | Automatic dimming via onboard light sensor |
| Internet connectivity | Periodic refresh and graceful offline fallback |
| Portrait UI | Optimized for 480×320 resolution |

---

## Example
(Example image stored in repository: pyportal_titano_weather_clock_example.jpg)

---

## Hardware

| Component | Description |
|-----------|-------------|
| Adafruit PyPortal Titano | 480×320 touchscreen microcontroller |
| ESP32 AirLift | Wi-Fi coprocessor for HTTPS requests |
| Light sensor | Controls automatic screen brightness |
| Weather BMP sprites | 32×32px icons |
| 04b30-20.bdf | Pixel font used for display text |

---

## Repository Structure

pyportal-titano-weather-clock/
├── code.py
├── .gitignore
├── README.md
├── secrets_example.py
├── pyportal_titano_weather_clock_example.jpg
├── fonts/
│   └── 04b30-20.bdf
└── weather_icons_32x32_9.bmp

---

## Setup

### 1. Install CircuitPython
Install CircuitPython for the PyPortal Titano:
https://circuitpython.org/board/pyportal_titano/

### 2. Copy the project files to CIRCUITPY
Place the following on the board:

code.py
weather_icons_32x32_9.bmp
/fonts/04b30-20.bdf

### 3. Create secrets.py

secrets = {
    "ssid": "YOUR_WIFI_NAME",
    "password": "YOUR_WIFI_PASSWORD",
    "timezone": "Region/City"
}

---

## Timezone Format (IANA Standard)

Examples:

America/New_York
America/Chicago
Europe/London
Asia/Tokyo
Australia/Sydney

Full timezone list:
https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

---

## Skills Demonstrated

| Area | Description |
|-------|-------------|
| Firmware development | CircuitPython hardware-level programming |
| REST API integration | JSON weather API and time server |
| Display UI rendering | Text and image layout for portrait mode |
| Hardware interaction | Light sensor-based dimming |
| Secure repo design | .gitignore + secrets handling |
| Debugging | Hardware and software iterative testing |

---

## Roadmap

| Feature | Status |
|---------|--------|
| Touch settings menu | Planned |
| Offline visual indicator | Planned |
| Minimal UI mode | Planned |
| Theme variations | Planned |

---

## Contributing
Pull requests and issues are welcome.

---

## License
MIT License

---

## Acknowledgements
Adafruit Industries for hardware reference docs and CircuitPython examples.
"""
