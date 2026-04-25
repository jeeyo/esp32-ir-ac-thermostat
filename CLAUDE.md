# ESP32 IR Remote — Claude Session Context

ESPHome firmware for M5StickC-Plus acting as an IR AC remote with acoustic beep confirmation and a smart thermostat, exposed as a `climate` entity in Home Assistant. Brand-agnostic — works with any AC whose remote can be learned and that emits a confirmation beep.

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
- **I2S PDM** — only `i2s_lrclk_pin: GPIO0` (the clock) plus `i2s_din_pin: GPIO34` (the data). Don't add `i2s_bclk_pin` — it triggers a "pin used twice" error in ESPHome 2025.11+.
- **Amplitude window (min+max)** — rejects beeps from adjacent-room AC units at lower volume. Calibration finds the right window for this install.
- **`beep_detector_source` substitution** — `external_components` source for `beep_detector` is `${beep_detector_source}`, defaulting to `components` (local path) so cloned builds and CI work as-is. No-clone users override the substitution to `github://jeeyo/esp32-ir-remote@<tag>` from a wrapper YAML. Same pattern for `ota_password` (default empty, override with `!secret`).
- **AXP192 comes from `makerwolf/esphome-axp192`** — newer ESPHome no longer has the airy10 top-level `axp192:` schema; it's now a `sensor: platform: axp192` block. Required on M5StickC-Plus or the LCD backlight stays off.
- **No `!secret` references in `ac-remote.yaml`** — keeps CI green and lets pre-built firmware be configured via captive portal. Users add secrets locally via a wrapper config or direct edit (see README § "Adding Your Secrets"). Do not re-introduce `!secret` without also adding CI handling.
- **Thermostat disables itself on IR failure** — `command_failed` binary sensor `on_press` forces `climate.ac_thermostat` to OFF; user must re-enable in HA.
- **AC internal setpoint is independent** — the thermostat only sends ON/OFF IR; the AC's own setpoint must be set cold (e.g. 18 °C) via its physical remote.

## Build

```bash
esphome run ac-remote.yaml
```
