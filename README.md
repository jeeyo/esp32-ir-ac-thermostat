# ESP32 IR Remote — Smart AC Controller

ESPHome firmware for M5StickC-Plus that controls an AC unit via IR with acoustic beep confirmation, and acts as a standalone smart thermostat using the onboard temperature sensor. Works with any AC that responds to an IR remote and emits a confirmation beep. Exposed as a full `climate` entity in Home Assistant — no cloud, no subscription.

## Features

- **Smart Thermostat** — maintains a target temperature by toggling the AC on/off; hysteresis and compressor-protection timers built in
- **Acoustic Confirmation** — listens for the AC's confirmation beep after each IR command; retries up to 3× before reporting failure
- **Passive Monitoring** — detects beeps from a physical remote and syncs Home Assistant state automatically
- **IR Learning** — capture raw IR codes from your original remote directly on the device
- **Beep Calibration** — sweep 1–8 kHz to find your AC's exact beep frequency and amplitude
- **Temperature / Humidity / Pressure** — onboard ENV HAT sensors exposed to Home Assistant
- **On-device Display** — shows AC state, thermostat mode + setpoint, current temperature, and status

## Hardware

### Bill of Materials

| Item | SKU / Notes |
|------|-------------|
| M5StickC-Plus | ESP32-PICO, built-in display + PDM mic |
| M5Stack IR Unit | U002 — IR TX + demodulating RX in one Grove module |
| M5Stack ENV III HAT | SHT30 temp/humidity + QMP6988 pressure — **required for thermostat** |

The ENV III HAT attaches directly to the M5StickC-Plus HAT port (no wiring). The IR Unit connects via the Grove port.

### Wiring: M5Stack IR Unit → Grove Port

```
IR Unit (Grove)    M5StickC-Plus
───────────────    ─────────────
  Yellow (TX) ──── GPIO32 (Grove pin 1)
  White  (RX) ──── GPIO33 (Grove pin 2)
  Red   (5V)  ──── 5V
  Black (GND) ──── GND
```

---

## Quick Start — Flash Pre-built Firmware

No toolchain needed. Download and flash in 2 minutes.

1. Download the latest `ac-remote.bin` from [GitHub Releases](https://github.com/jeeyo/esp32-ir-remote/releases/latest)
2. Open [ESPHome Web Installer](https://web.esphome.io/) in Chrome or Edge
3. Click **Install** → select the `.bin` file → connect your M5StickC-Plus via USB-C
4. On first boot, the device exposes a WiFi network named **AC-Remote-Fallback** (password `fallback123`). Connect to it with your phone; a captive portal opens where you enter your home WiFi credentials
5. Once the device joins your network, open Home Assistant → **Settings → Devices & Services → Add Integration → ESPHome**
6. Enter the device IP or hostname `ac-remote.local`. On first adoption, HA generates an API encryption key and stores it

> After adopting, the device shows up with all entities. You'll need to learn your IR codes before the thermostat can actually control the AC — see [Learn IR Codes](#learn-ir-codes) below.
>
> The pre-built firmware does not hard-code WiFi, API encryption, or OTA credentials — those are configured post-install via the captive portal and Home Assistant. If you want to bake them in at build time, see [Setup from Source](#setup-from-source).

---

## Setup from Source

Build your own firmware with WiFi / API / OTA credentials baked in. **You do not need to clone this repo** — a small wrapper YAML pulls everything from GitHub.

You only create two files: `secrets.yaml` and `my-ac-remote.yaml`.

### 1. Install ESPHome

```bash
pip install esphome
```

### 2. Pick a release tag

Browse [Releases](https://github.com/jeeyo/esp32-ir-remote/releases) and pick the version you want to build (e.g. `v0.1.0`). Use the same tag in **both** places below so the upstream YAML and the bundled `beep_detector` component come from the same commit.

### 3. Create `secrets.yaml`

```yaml
wifi_ssid: "YourWiFi"
wifi_password: "YourWiFiPassword"
api_encryption_key: "base64-32-bytes"
ota_password: "your-ota-password"
```

Generate the API key:

```bash
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

`secrets.yaml` should stay out of version control — add it to `.gitignore` if you keep your wrapper config in a repo.

### 4. Create `my-ac-remote.yaml`

This is the only config file you build with. It pulls `ac-remote.yaml` and the `beep_detector` component straight from GitHub at the tag you picked, and layers your secrets on top.

```yaml
substitutions:
  # Tell the upstream config to fetch beep_detector from GitHub at the same tag.
  beep_detector_source: github://jeeyo/esp32-ir-remote@v0.1.0
  ota_password: !secret ota_password

packages:
  upstream:
    url: https://github.com/jeeyo/esp32-ir-remote
    ref: v0.1.0
    files: [ac-remote.yaml]
    refresh: 1d

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

api:
  encryption:
    key: !secret api_encryption_key
```

The wrapper:

- **`packages.upstream`** pulls `ac-remote.yaml` from GitHub at the chosen tag.
- **`substitutions.beep_detector_source`** redirects the upstream's local-path component reference to GitHub, so no clone is needed.
- **`substitutions.ota_password`** fills in the OTA password (the upstream defaults to empty).
- **`wifi`** / **`api`** are dict-merged with the upstream blocks: your station credentials and API encryption key get added without removing the captive-portal AP fallback.

> Bump the tag in **both** `beep_detector_source` and `packages.upstream.ref` together when you want to upgrade.

### 5. Build and flash

USB:

```bash
esphome run my-ac-remote.yaml
```

OTA (subsequent updates, no cable needed):

```bash
esphome run my-ac-remote.yaml --device ac-remote.local
```

ESPHome downloads the upstream YAML and the `beep_detector` source on first build and caches them; pass `--cache off` if you ever need to force a re-fetch.

### Developer / contributor build

If you're modifying this repo itself, clone it and build `ac-remote.yaml` directly — the substitutions default to the local `components/` path, so no wrapper is needed. Drop `wifi:` / `api:` / `ota_password:` overrides into a sibling `secrets.yaml` and patch the YAML, or create a wrapper that points `packages.upstream: !include ac-remote.yaml` at the local file.

---

## Learn IR Codes

The firmware ships with **placeholder IR codes**. You must replace them with codes learned from your actual AC remote before the AC will respond.

1. Short-press **Button B** — display shows `IR LEARN`
2. Point your AC remote at the IR Unit and press the **power ON** button
3. Open ESPHome logs (`esphome logs ac-remote.yaml`) and copy the `raw:` array
4. Paste it into `ac-remote.yaml` under `send_ac_on_attempt` → `remote_transmitter.transmit_raw: code:`
5. Repeat for the **power OFF** button → paste into `send_ac_off_attempt`
6. Press **Button B** again to exit IR Learn mode
7. Reflash: `esphome run ac-remote.yaml`

---

## Calibrate Beep Detection

If the thermostat never confirms commands (check `binary_sensor.ac_beep_confirmed`), the beep detector needs calibrating for your specific AC unit and room.

1. Long-press **Button A** for 3 seconds — display shows `CALIBRATE`
2. Use the physical remote to trigger your AC so it beeps
3. Wait for the 10-second calibration window to complete
4. Open logs and note:
   - `Peak frequency` → update `target_frequency` in `beep_detector:` block
   - `Suggested amplitude_min` / `amplitude_max` → update those fields
5. Reflash with updated values

---

## Adopting in Home Assistant

### Step 1 — Add the ESPHome Integration

1. **Settings → Devices & Services → Add Integration → ESPHome**
2. Enter `ac-remote.local` (or device IP)
3. Enter the API encryption key from your `secrets.yaml`
4. The device appears with ~12 entities across sensors, switches, binary sensors, and a climate entity

### Step 2 — Add a Thermostat Card to Lovelace

Paste this into a dashboard card (YAML mode):

```yaml
type: thermostat
entity: climate.ac_thermostat
name: AC Thermostat
```

Or use the visual card editor: **Add Card → Thermostat → Entity: climate.ac_thermostat**.

The card lets you set target temperature and switch between `off` and `cool` modes. The device handles the rest.

### Step 3 — Example Automations

**Away mode — raise setpoint when nobody is home:**

```yaml
automation:
  - alias: "AC away mode"
    trigger:
      - platform: state
        entity_id: group.household
        to: not_home
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.ac_thermostat
        data:
          temperature: 28
          hvac_mode: cool
```

**Night schedule — lower setpoint at bedtime:**

```yaml
automation:
  - alias: "AC night cooling"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.ac_thermostat
        data:
          temperature: 22
          hvac_mode: cool

  - alias: "AC morning off"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.ac_thermostat
        data:
          hvac_mode: "off"
```

**Alert on IR failure:**

```yaml
automation:
  - alias: "AC command failed alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.ac_command_failed
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "AC IR remote failed after 3 attempts — check device placement"
```

### Step 4 — Full Entity Reference

| Entity | Type | Description |
|--------|------|-------------|
| `climate.ac_thermostat` | Climate | Thermostat — set target temp and mode (off/cool) |
| `number.cool_deadband` | Number | Tuning: °C above setpoint before cooling engages (default 0.5) |
| `number.cool_overrun` | Number | Tuning: °C below setpoint before cooling disengages (default 0.5) |
| `switch.ac_power` | Switch | Direct AC toggle (bypasses thermostat) |
| `button.re_sync_ac_state` | Button | Flip the tracked AC state **without sending IR** — use when HA and the real AC have drifted out of sync |
| `sensor.temperature` | Sensor | Room temperature from ENV HAT (°C) |
| `sensor.humidity` | Sensor | Relative humidity (%) |
| `sensor.pressure` | Sensor | Barometric pressure (hPa) |
| `sensor.battery_level` | Sensor | M5StickC-Plus battery charge (%) from AXP192 |
| `binary_sensor.ac_beep_confirmed` | Binary Sensor | Last IR command was acoustically confirmed |
| `binary_sensor.ac_command_failed` | Binary Sensor | Last command failed after 3 retries |
| `sensor.beep_frequency` | Sensor | Calibration: detected peak frequency (Hz) |
| `sensor.beep_amplitude` | Sensor | Calibration: detected peak amplitude |
| `text_sensor.last_action` | Text Sensor | Human-readable status of last action |

---

## Button Controls

| Button | Action | Function |
|--------|--------|----------|
| Button A | Short press | Toggle AC on/off (normal mode only) |
| Button A | Long press 3s | Enter beep calibration mode |
| Button B | Short press | Toggle IR learn mode |

Thermostat setpoint is adjusted via Home Assistant, not the device buttons.

---

## How It Works

### Thermostat Control

The `climate.ac_thermostat` entity runs a bang-bang controller with a configurable hysteresis band (default 1.0 °C total: 0.5 °C deadband + 0.5 °C overrun):

- When room temp exceeds `target + cool_deadband` → sends AC ON via IR (with beep confirmation)
- When room temp drops below `target − cool_overrun` → sends AC OFF via IR
- Compressor protection: minimum 3-minute run time, 5-minute off time before cycling
- If 3 consecutive IR commands fail to get a beep confirmation, the thermostat forces itself to `off` mode and alerts via `binary_sensor.ac_command_failed`

Tune the band live in HA via `number.cool_deadband` and `number.cool_overrun` — settings persist across reboots. Tighter bands hit the setpoint more precisely but may cycle the compressor more often (the min-run/off timers remain a hard floor).

> **Important:** The thermostat sets the AC on/off, but cannot change the AC's internal setpoint. Leave the AC's own remote set to a cold temperature (e.g. 18 °C) so the thermostat's "on" bursts actually cool the room.

### Command Flow

1. HA (thermostat or switch) triggers IR send
2. IR raw code transmitted via M5Stack IR Unit (GPIO32)
3. PDM microphone listens for confirmation beep (5-second window)
4. Beep detected within amplitude window → command confirmed, state updated
5. No beep → retry (up to 3 attempts, 1 second apart)
6. After 3 failures → `command_failed` sensor activates, thermostat disables itself

### Passive Monitoring

The microphone runs continuously. A beep that wasn't triggered by the device itself means someone used the physical remote — the device toggles the HA switch state to stay in sync.

### Amplitude Window

Multiple identical AC units in adjacent rooms produce the same beep frequency. The `amplitude_min` / `amplitude_max` window ensures only the nearby unit's beep (at expected volume) triggers detection. Calibration finds the right window for your installation.

---

## Troubleshooting

**Thermostat not switching the AC:**
- Check that IR codes have been learned (placeholders do nothing)
- Verify `binary_sensor.ac_beep_confirmed` — if always off, run calibration
- Confirm the AC's own internal setpoint is low enough (e.g. 18 °C)

**No beep detected / always unconfirmed:**
- Run calibration (Button A long press) to find correct frequency
- Check amplitude values in logs — may need a wider `amplitude_min/max` window
- Ensure the ENV HAT is not blocking the M5 microphone port

**False triggers from adjacent rooms:**
- Narrow the amplitude window (tighter `amplitude_min` / `amplitude_max`)
- Position the device closer to your target AC unit

**IR codes don't work:**
- Verify with a phone camera that the IR LED flashes when a command is sent
- Try learning codes from a closer distance to the IR receiver
- Some AC protocols are long — the receiver buffer is 10 KB which handles 100+ pulses

**Temperature reading seems off:**
- The SHT30 on the ENV HAT can read 1–2 °C high due to heat from the M5 body
- Apply a fixed offset in the YAML under `env_temperature` sensor: add `filters: - offset: -1.5`
- Calibrate against a reference thermometer after running the device for 30 minutes

**Display not working:**
- AXP192 must initialise before the display — check I2C connection at GPIO21/22
- Verify the ENV HAT is seated correctly (it shares the I2C bus)
