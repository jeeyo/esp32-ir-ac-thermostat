# ESP32 IR Remote — Project Guide

## What This Is

ESPHome firmware for M5StickC-Plus that acts as a Trane AC IR remote with acoustic beep confirmation, exposed as a Home Assistant binary switch. The device sends IR on/off commands, then listens via the built-in PDM microphone for the AC's confirmation beep using a Goertzel single-frequency detector.

## Project Structure

- `ac-remote.yaml` — Main ESPHome config. Contains everything: board setup, AXP192 PMU, ST7789V display, I2S PDM mic, IR TX/RX, template switch, retry scripts, button handlers, display lambda, all HA entities.
- `secrets.yaml` — WiFi/API/OTA credentials (gitignored).
- `components/beep_detector/` — Custom ESPHome component:
  - `__init__.py` — Config schema and codegen (registers `beep_detector:` YAML block).
  - `beep_detector.h` — C++ header. `BeepDetector` class, `CalibrationResult` struct, `BeepDetectedTrigger`.
  - `beep_detector.cpp` — Goertzel algorithm, onset/offset tracking with duration validation, amplitude window filtering, calibration sweep (1–8 kHz), cooldown logic.
- `fonts/roboto.ttf` — Display font.

## Architecture

### HA Entities
- `switch.ac_power` — Binary switch, `optimistic: false`. State only updates after beep confirmation.
- `binary_sensor.ac_beep_confirmed` — Last command was acoustically confirmed.
- `binary_sensor.ac_command_failed` — Last command failed after 3 retries.
- `sensor.beep_frequency` / `sensor.beep_amplitude` — Calibration results.
- `text_sensor.last_action` — Human-readable status.

### Command Flow
HA/Button A → IR transmit → listen 5s for beep → if no beep, retry up to 3x → on failure, set `command_failed`, do NOT update switch state.

### Passive Monitoring
Mic runs continuously. Beep detected while `self_triggered=false` → external remote used → toggle switch state to sync HA. Cooldown prevents double-counting.

### Modes (stored in `current_mode` global: 0=normal, 1=ir_learn, 2=calibrate)
- **Normal**: AC control + passive beep monitoring.
- **IR Learn** (Button B): Pauses beep detector, enables IR receiver raw+pronto dump to logs.
- **Calibration** (Button A long press 3s): Pauses beep detector, sweeps 1–8 kHz for 10s, reports peak frequency + amplitude + suggested ±30% window.

## Hardware Pins (M5StickC-Plus)

| Function | Pin |
|---|---|
| IR LED TX | GPIO32 (M5Stack IR Unit, Grove pin 1) |
| PDM Mic CLK | GPIO0 |
| PDM Mic DATA | GPIO34 |
| Display SPI | CLK=13, MOSI=15, CS=5, DC=23, RST=18 |
| AXP192 I2C | SDA=21, SCL=22 |
| Button A | GPIO37 (inverted) |
| Button B | GPIO39 (inverted) |
| IR Receiver (M5Stack IR Unit, Grove pin 2) | GPIO33 |

## Key Design Decisions

- **Amplitude window (min+max), not just threshold**: Multiple identical AC units in adjacent rooms produce the same frequency beep. The window rejects quieter beeps from distant units.
- **Goertzel over FFT**: Only need one frequency bin. O(N) per frequency, very low CPU.
- **3 Goertzel bins** (center ± tolerance): Handles slight frequency drift between AC units.
- **IR codes are placeholders**: Must be learned from the actual Trane remote via IR Learn mode, then pasted into the YAML raw code arrays in `send_ac_on_attempt` and `send_ac_off_attempt` scripts.
- **`optimistic: false`**: Switch state never updates unless beep-confirmed or externally detected.

## Development Notes

- External dependency: `axp192` from `github://airy10/esphome-m5stickC` for power management.
- IR receiver buffer is 10KB (`buffer_size: 10000b`) because Trane AC protocols can be 100+ pulses.
- The I2S config uses `allow_other_uses: true` on GPIO0 because PDM mode reuses the LRCLK pin for clock (no separate BCLK).
- Build/flash: `esphome run ac-remote.yaml`.
- If ESPHome's I2S component doesn't handle PDM correctly, fallback is to initialize I2S directly in `beep_detector.cpp` using ESP-IDF APIs.
