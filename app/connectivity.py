# app/connectivity.py — Wi-Fi management
# Wraps ESP32 AirLift SPI. Non-blocking reconnect logic.
# Wi-Fi failure never crashes the main loop.

import time
import board
import busio
import digitalio

_RECONNECT_INTERVAL = 60.0   # seconds between reconnect attempts when offline
_VALIDATE_INTERVAL  = 30.0   # seconds between connection-state validation checks


class ConnectivityManager:
    def __init__(self, ssid, password):
        self._ssid      = ssid
        self._password  = password
        self._esp       = None
        self._requests  = None
        self._pool      = None
        self._connected = False
        self._ip        = None
        self._last_attempt = 0.0
        self._last_validate = 0.0
        self._init_hw()

    def _init_hw(self):
        """Initialize ESP32 AirLift hardware."""
        try:
            from adafruit_esp32spi import adafruit_esp32spi
            import adafruit_esp32spi.adafruit_esp32spi_socketpool as esp_socketpool
            import adafruit_requests
            try:
                import ssl
                ssl_ctx = ssl.create_default_context()
            except Exception:
                ssl_ctx = None

            spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
            cs  = digitalio.DigitalInOut(board.ESP_CS)
            rdy = digitalio.DigitalInOut(board.ESP_BUSY)
            rst = digitalio.DigitalInOut(board.ESP_RESET)
            self._esp = adafruit_esp32spi.ESP_SPIcontrol(spi, cs, rdy, rst)
            self._pool = esp_socketpool.SocketPool(self._esp)
            self._requests = adafruit_requests.Session(self._pool, ssl_ctx)
        except Exception as e:
            print("ConnectivityManager: HW init failed:", e)
            self._esp = None

    def _update_ip_address(self):
        try:
            raw = self._esp.ip_address
            self._ip = ".".join(str(b) for b in raw)
        except Exception:
            self._ip = None

    def _mark_disconnected(self):
        self._connected = False
        self._ip = None

    def _validate_connection_state(self):
        if not self._esp:
            self._mark_disconnected()
            return False
        try:
            self._connected = bool(self._esp.is_connected)
        except Exception:
            self._connected = False
        if self._connected:
            self._update_ip_address()
        else:
            self._ip = None
        return self._connected

    def connect(self):
        """Attempt Wi-Fi connection once. Returns True if successful."""
        if not self._esp or not self._ssid or not self._password:
            self._mark_disconnected()
            return False
        try:
            self._esp.connect_AP(
                bytes(self._ssid, "utf-8"),
                bytes(self._password, "utf-8")
            )
            self._connected = True
            self._update_ip_address()
            return True
        except Exception:
            self._mark_disconnected()
            return False

    def connect_with_retry(self, attempts=3, gap_secs=2.0):
        """Attempt Wi-Fi connection multiple times with concise diagnostics."""
        ssid = self._ssid or ""
        if len(ssid) <= 2:
            ssid_masked = "*" * len(ssid)
        else:
            ssid_masked = "{}***{}".format(ssid[:1], ssid[-1:])
        print("Wi-Fi SSID:", ssid_masked if ssid else "(empty)")

        for i in range(1, max(1, int(attempts)) + 1):
            print("Attempt {}/{}...".format(i, attempts))
            ok = self.connect()
            if ok:
                print("Connected, IP={}".format(self._ip or "?"))
                return True
            print("Failed attempt {}/{}".format(i, attempts))
            if i < attempts:
                time.sleep(max(0.0, float(gap_secs)))
        return False

    def update_if_due(self, state):
        """
        Periodically validate real connection state.
        If offline and enough time has passed, attempt a single reconnect.
        Updates state.wifi_connected and state.ip_address.
        """
        now = time.monotonic()

        if (now - self._last_validate) >= _VALIDATE_INTERVAL:
            self._last_validate = now
            self._validate_connection_state()

        if not self._connected and (now - self._last_attempt) >= _RECONNECT_INTERVAL:
            self._last_attempt = now
            self.connect()

        state.wifi_connected = self._connected
        state.ip_address     = self._ip
        if not self._connected and state.offline_since is None:
            state.offline_since = now
        elif self._connected:
            state.offline_since = None

    def get(self, url, timeout=8):
        """HTTP GET. Returns parsed JSON dict or raises. Failed requests invalidate connection state."""
        if not self._requests:
            self._mark_disconnected()
            raise OSError("No network session")
        try:
            r = self._requests.get(url, timeout=timeout)
            data = r.json()
            r.close()
            self._connected = True
            self._update_ip_address()
            return data
        except Exception:
            self._mark_disconnected()
            raise

    @property
    def connected(self):
        return self._connected

    @property
    def ip(self):
        return self._ip
