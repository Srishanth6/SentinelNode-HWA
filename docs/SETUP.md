# Setup

## 1. Software (any laptop, Python 3.10+)
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q                                   # 11 tests, including a gcc build of the C inference
python -m sentinelnode.autoencoder          # retrain + regenerate firmware/sentinelnode/ae_model.h
python -m scripts.eval_aging                # simulated early-warning evaluation -> docs/eval_aging.json
uvicorn sentinelnode.api:app --reload       # backend on http://127.0.0.1:8000 (docs at /docs)
python -m sim.simulator                     # in a second terminal: stream simulated readings
```

## 2. Firmware (ESP32-WROOM-32 DevKit)
Arduino IDE 2 or arduino-cli with the **esp32 by Espressif** core. Libraries: Adafruit INA219,
Adafruit MLX90614 Library, OneWire, DallasTemperature, Adafruit MPU6050, ArduinoJson, PubSubClient.
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/sentinelnode
arduino-cli upload  --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 firmware/sentinelnode
```
Edit `WIFI_SSID`, `WIFI_PASS`, `SERVER` and `NODE_ID` at the top of `sentinelnode.ino`. Set
`USE_THINGSBOARD 1` and fill `TB_HOST` / `TB_TOKEN` to publish to ThingsBoard
(topic `v1/devices/me/telemetry`).

## 3. Wiring

| Part | Pin(s) on the part | ESP32 pin | Notes |
|---|---|---|---|
| INA219 | VCC, GND, SDA, SCL | 3V3, GND, GPIO21, GPIO22 | Address 0x40. VIN+ / VIN− in series with the monitored DC rail (max 26 V) |
| MLX90614 (GY-906) | VIN, GND, SDA, SCL | 3V3, GND, GPIO21, GPIO22 | Address 0x5A. Aim at the hottest part (e.g. the output capacitor or MOSFET) |
| MPU6050 | VCC, GND, SDA, SCL | 3V3, GND, GPIO21, GPIO22 | Address 0x68. Fixed to the board or chassis |
| DS18B20 | VDD, GND, DQ | 3V3, GND, GPIO4 | 4.7 kΩ pull-up from DQ to 3V3. Measures ambient air near the board |
| Ripple input | — | GPIO34 (ADC1) | Rail → 1 µF film cap → mid-rail bias (2× 100 kΩ from 3V3 to GND) → 1 kΩ → GPIO34; keep the signal under 3.3 V |
| Status LED | anode via 330 Ω | GPIO25 | |
| Buzzer (active, 3.3 V) | + | GPIO26 | Via an NPN transistor if it draws more than about 12 mA |
| HLK-PM01 | 5 V out | 5V/VIN | Or USB power on the bench |
