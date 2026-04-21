# docs/hardware-wiring.md — Hardware & Wiring

## PyPortal Titano

| Spec | Value |
|------|-------|
| MCU | ATSAMD51J20 (120 MHz Cortex-M4) |
| Display | 3.5" IPS TFT, 480×320 px |
| Wi-Fi | ESP32 AirLift (SPI coprocessor) |
| Speaker | Built-in mono speaker |
| Light sensor | Built-in analog light sensor |
| USB | Micro-USB (power + CIRCUITPY drive) |
| GPIO | Accessible via JST connectors on rear |

---

## Button Wiring

The dashboard supports both 2-button and 3-button setups. For PyPortal Titano,
the recommended default is 2-button mode:

```
PyPortal D3 ──── [BACK button] ──── GND
PyPortal D4 ──── [NEXT button] ──── GND
```

`HOME` can be mapped to an optional third button if your hardware exposes one.
In 2-button mode, pressing both buttons together emits `HOME`.

### Available GPIO breakouts on the Titano

The Titano has three JST-PH connectors on the rear that expose GPIO:

| Connector | Pins available |
|-----------|---------------|
| JST #1 | D3, D4, GND |
| JST #2 | D5, A1, GND |
| JST #3 | A2, A3, GND |

D3 and D4 are on JST #1 and are the safest default for this project.

### Alternative pin options

If your pinout differs, set button pins in `settings.toml`:

```toml
PIN_BACK="A1"   # or any available digital GPIO
PIN_HOME="A2"   # optional
PIN_NEXT="A3"
```

---

## Speaker

The PyPortal Titano has a built-in speaker driven by the `SPEAKER` pin. The `audio.py` module uses `audiopwmio.PWMAudioOut(board.SPEAKER)` directly — no additional wiring required.

Speaker volume is controlled by `_AMPLITUDE` in `app/audio.py` (range 0–32767). Default is 28000 (~85% volume). Lower this value if the click sound is too loud.

---

## Light Sensor

The onboard ambient light sensor is read from `board.LIGHT` via `AnalogIn`. No wiring required. Auto-brightness is enabled by default (`AUTO_DIM = True` in `app/config.py`). To disable and use a fixed brightness level:

```python
AUTO_DIM = False
FIXED_BRIGHTNESS = 0.75   # 0.0–1.0
```

---

## Enclosure / Mounting

The PyPortal Titano has two M3 mounting holes on the rear PCB. Common desk mounting options:

- **3D-printed stand** — portrait orientation, tilted 15–20° for comfortable viewing
- **Flush wall mount** — flat against wall, useful for hallway dashboards
- **Acrylic frame** — laser-cut surround with cutout for JST connectors

Display rotation is set in `app/config.py`. If the image appears upside-down for your mount, change `DISPLAY_ROTATION = 270` to `DISPLAY_ROTATION = 90`.

---

## Power

The PyPortal Titano draws approximately 200–350 mA at full brightness. Use a 5V/1A (or better) USB power supply. A standard phone charger works well. The device is not designed for battery-only operation without sleep-mode firmware modifications.

---

## No Touchscreen Required

While the Titano has a resistive touchscreen, this firmware uses physical buttons only. The touchscreen is not initialized or polled. This is intentional — physical buttons are more reliable for an ambient appliance that may be touched without looking.
