# ESP32 IR Remote — M5StickC-Plus AC Controller

ESPHome firmware for M5StickC-Plus that controls a Trane AC unit via IR, with acoustic beep confirmation via the built-in PDM microphone. Exposed as a binary switch in Home Assistant.

## Features

- **IR Control**: Send on/off commands to Trane AC via M5Stack IR Unit (GPIO32)
- **Beep Confirmation**: Listens for the AC's confirmation beep using Goertzel single-frequency detection
- **Retry Logic**: Up to 3 attempts per command if beep is not detected
- **Amplitude Window**: Rejects beeps from adjacent rooms (different volume than the target unit)
- **Passive Monitoring**: Continuously listens for beeps from the original remote to keep HA state in sync
- **IR Learning**: Capture raw IR codes from your original remote via M5Stack IR Unit receiver (GPIO33)
- **Beep Calibration**: Measures the exact beep frequency and amplitude at your installation distance
- **OLED Display**: Shows AC state, confirmation status, and current mode

## Hardware

### Required
- M5StickC-Plus (ESP32-PICO with built-in display, PDM mic)
- M5Stack IR Unit (SKU: U002)

## Wiring: M5Stack IR Unit

Connect the IR Unit to the M5StickC-Plus Grove port using the included HY2.0-4P cable:

```
IR Unit (Grove)    M5StickC-Plus
───────────────    ─────────────
  Yellow (TX) ──── GPIO32 (Grove pin 1)
  White  (RX) ──── GPIO33 (Grove pin 2)
  Red   (5V)  ──── 5V
  Black (GND) ──── GND
```

The IR Unit provides both the IR transmitter LED and demodulating IR receiver in a single Grove module — no additional wiring needed.

## Setup

### 1. Install ESPHome

```bash
pip install esphome
```

### 2. Configure Secrets

Edit `secrets.yaml` with your credentials:

```yaml
wifi_ssid: "YourWiFi"
wifi_password: "YourPassword"
api_encryption_key: "your-base64-key-here"
ota_password: "your-ota-password"
```

Generate an API key:
```bash
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

### 3. Flash Firmware

```bash
esphome run ac-remote.yaml
```

### 4. Learn IR Codes

1. Connect the M5Stack IR Unit to the Grove port (see wiring above)
2. Short press **Button B** to enter IR Learn mode (display shows "IR LEARN")
3. Point your Trane remote at the IR Unit and press the ON button
4. Check ESPHome logs for the raw code output
5. Copy the raw code into `ac-remote.yaml` under `send_ac_on_attempt`
6. Repeat for the OFF button → paste into `send_ac_off_attempt`
7. Press **Button B** again to exit IR Learn mode
8. Reflash: `esphome run ac-remote.yaml`

### 5. Calibrate Beep Detection

1. Long press **Button A** (3 seconds) to enter calibration mode
2. Display shows "Calibrating... trigger AC beep"
3. Use the original remote to trigger the AC (so it beeps)
4. Wait for the 10-second calibration window to finish
5. Check ESPHome logs for:
   - Peak frequency (update `target_frequency` in YAML)
   - Suggested amplitude window (update `amplitude_min` / `amplitude_max`)
6. Reflash with updated values

## Home Assistant Entities

| Entity | Type | Description |
|--------|------|-------------|
| `switch.ac_power` | Switch | Toggle AC on/off |
| `binary_sensor.ac_beep_confirmed` | Binary Sensor | Whether last command was acoustically confirmed |
| `binary_sensor.ac_command_failed` | Binary Sensor | Whether last command failed after 3 retries |
| `sensor.beep_frequency` | Sensor | Calibration result: detected frequency (Hz) |
| `sensor.beep_amplitude` | Sensor | Calibration result: detected amplitude |
| `text_sensor.last_action` | Text Sensor | Status text of last action |

## Button Controls

| Button | Action | Function |
|--------|--------|----------|
| Button A | Short press | Toggle AC on/off |
| Button A | Long press (3s) | Enter beep calibration mode |
| Button B | Short press | Toggle IR learn mode |

## How It Works

### Command Flow
1. HA or Button A triggers `switch.ac_power`
2. IR raw code is transmitted via M5Stack IR Unit (GPIO32)
3. Microphone listens for confirmation beep (5-second window)
4. If beep detected within amplitude window → switch state confirmed
5. If no beep → retry (up to 3 attempts)
6. After 3 failures → `command_failed` sensor activates, switch state unchanged

### Passive Monitoring
The microphone runs continuously. When a beep is detected that was NOT triggered by the device itself (no IR command sent recently), the device assumes someone used the original remote and toggles the switch state to keep HA in sync.

### Amplitude Window
Multiple identical AC units in adjacent rooms produce the same frequency beep. The amplitude window (min/max) ensures only the nearby unit's beep (at expected volume) triggers detection. Beeps from distant units arrive at lower amplitude and are rejected.

## Troubleshooting

**No beep detected:**
- Run calibration to find the correct frequency
- Check amplitude values in logs — may need wider window
- Ensure microphone is not obstructed

**False triggers from adjacent rooms:**
- Narrow the amplitude window (tighter min/max)
- Position device closer to target AC unit
- Increase `min_duration_ms` if noise causes brief false positives

**IR codes don't work:**
- Verify with phone camera that IR LED flashes when sending
- Try learning codes again from closer distance
- Some Trane models use different protocols — check raw code length

**Display not working:**
- AXP192 must initialize before display — check I2C connection
- Verify SPI pins match M5StickC-Plus hardware
