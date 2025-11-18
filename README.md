# pyportal-titano-weather-clock
CircuitPython firmware for a PyPortal Titano portrait weather + clock display.

===================================================

PyPortal Titano Portrait Clock + Weather Display

CircuitPython firmware for the Adafruit PyPortal Titano that turns it into a portrait-mode desk display showing:
• Weather icon and temperature
• Date and weekday
• Large digital time display
• Automatic brightness using the onboard light sensor

The project demonstrates embedded firmware development, hardware integration, and UI rendering using CircuitPython and displayio.

Hardware
---------------------------------------------------
• Adafruit PyPortal Titano (480x320 display)
• ESP32 AirLift for Wi-Fi connectivity
• Built-in light sensor for auto-dimming
• Optional weather icon sprite sheet: weather_icons_32x32_9.bmp

Features
---------------------------------------------------
• Portrait layout optimized for Titano’s larger display
• Weather and temperature pulled from Open-Meteo public API (free, no API key required)
• Time synchronization via WorldTimeAPI (free, no API key required)
• Automatic brightness scaling based on ambient light values
• Periodic refresh intervals for both time and weather data
• Graceful fallback when Wi-Fi or APIs are unavailable

Setup Instructions
---------------------------------------------------
1. Install CircuitPython 10.x on the PyPortal Titano.
2. Copy the project files to the CIRCUITPY drive:
   - code.py (main firmware file)
   - /fonts/04b30-20.bdf (or adjust path in code)
   - /weather_icons_32x32_9.bmp (icon file) in the root directory

3. Add Wi-Fi configuration by creating a secrets.py file on the device:
   Example secrets.py:
   secrets = {
       "ssid": "YOUR_WIFI_NAME",
       "password": "YOUR_WIFI_PASSWORD",
       "timezone": "Region/City",
   }

Timezone Format
---------------------------------------------------
The timezone setting uses the IANA timezone database format. Examples:
America/New_York
America/Chicago
Europe/London
Asia/Tokyo
Australia/Sydney

Full timezone list:
https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

Important Note:
Do not upload real Wi-Fi SSID or password to GitHub. Use a file named secrets_example.py for public repos and add secrets.py to .gitignore.

Configuration
---------------------------------------------------
Adjust these values in code.py for your region:
LATITUDE, LONGITUDE = xx.xxxx, -yy.yyyy
USE_FAHRENHEIT = True or False

Known Future Improvements
---------------------------------------------------
• Divider UI element currently disabled while iterating layout
• Location values to be moved to configuration module for portability
• Consider switching to HTTPS endpoints where supported
• Add small UI indicator when offline or waiting for sync

Why this project exists
---------------------------------------------------
This firmware is part of a learning and capability-building process focused on embedded development, system design, and hardware + software integration. The PyPortal Titano platform has limited example projects available due to its larger resolution and niche adoption, making this implementation relatively unique.

Demonstrated Skills
---------------------------------------------------
• Embedded firmware development in CircuitPython
• Wi-Fi and REST API integration
• Sensor-driven UI logic
• Real-time display rendering and scaling
• Debugging real-world hardware interfaces and timing issues

"""


