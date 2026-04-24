# ESP32 IR Remote — Claude Session Context

ESPHome firmware for M5StickC-Plus acting as a Trane AC IR remote with acoustic beep confirmation and a smart thermostat, exposed as a `climate` entity in Home Assistant.

## Files

- `ac-remote.yaml` — entire ESPHome config (board, display, mic, IR, thermostat, sensors, scripts, automations)
- `secrets.yaml` — WiFi/API/OTA credentials (gitignored)
- `components/beep_detector/` — custom ESPHome component: `__init__.py` (schema/codegen), `beep_detector.h`, `beep_detector.cpp` (Goertzel detector, calibration sweep)
- `fonts/roboto.ttf` — display font
- `.github/workflows/build.yml` — CI build on push/PR via `esphome/workflows`
- `.github/workflows/release.yml` — build + publish firmware to GH release on `v*` tag

## Hardware Pins (M5StickC-Plus)

| Function | Pin |
|---|---|
| IR LED TX | GPIO32 (Grove pin 1) |
| IR Receiver | GPIO33 (Grove pin 2) |
| PDM Mic CLK | GPIO0 |
| PDM Mic DATA | GPIO34 |
| Display SPI | CLK=13, MOSI=15, CS=5, DC=23, RST=18 |
| AXP192 / ENV HAT I2C | SDA=21, SCL=22 |
| Button A | GPIO37 (inverted) |
| Button B | GPIO39 (inverted) |

## Modes (`current_mode` global)

| Value | Mode | Entry |
|---|---|---|
| 0 | Normal | default |
| 1 | IR Learn | Button B short press |
| 2 | Calibrate | Button A long press 3s |

## Non-obvious constraints

- **IR codes are placeholders** — must be learned via IR Learn mode and pasted into `send_ac_on_attempt` / `send_ac_off_attempt` raw arrays before the AC will respond.
- **`optimistic: false` on `ac_power_switch`** — state only updates after beep confirmation or external-remote detection. Never publish state optimistically.
- **I2S PDM** — `allow_other_uses: true` on GPIO0 because PDM reuses the LRCLK pin for clock; BCLK is unused but required by ESPHome's schema.
- **Amplitude window (min+max)** — rejects beeps from adjacent-room AC units at lower volume. Calibration finds the right window for this install.
- **`beep_detector` fetched from GitHub** — `external_components` uses `github://jeeyo/esp32-ir-remote@main`; pin to a release tag once CI produces one.
- **Thermostat disables itself on IR failure** — `command_failed` binary sensor `on_press` forces `climate.ac_thermostat` to OFF; user must re-enable in HA.
- **AC internal setpoint is independent** — the thermostat only sends ON/OFF IR; the AC's own setpoint must be set cold (e.g. 18 °C) via its physical remote.

## Build

```bash
esphome run ac-remote.yaml
```
