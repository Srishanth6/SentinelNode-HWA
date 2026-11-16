# SentinelNode — low-cost AI edge node for early electronic component failure detection

**HackWithAditya 2026 · Team Silicon Sentinels (HWA26-LMNB) · Track: Robotics, IoT & Smart Manufacturing**

> **Status:** prototype software. Hardware build is in progress, and **no bench or field results exist yet**. All data in this repo comes from the simulator, and any metric here is **simulated**, not measured.

SentinelNode is a retrofit ESP32 node that watches a power/control board's rail voltage and current, supply ripple, hot-spot and ambient temperature, and vibration. It flags degradation (for example, an aging capacitor, an overload or a loose mount) before the part fails.

## Architecture
```
 Sensors ──► ESP32 firmware ──(Wi-Fi, JSON/HTTP or MQTT)──► FastAPI backend / ThingsBoard ──► Dashboard / alerts
 INA219 (V,I)      threshold rules + int8 autoencoder     history, alerts API
 MLX90614 (hot)    LED / buzzer local alarm              health score 0–100
 DS18B20 (amb)                                           /api/nodes, /api/alerts
 MPU6050 (vib)
 Ripple → ADC1
```
![Architecture](docs/figma/09_architecture.png)

| Path | What it is |
|---|---|
| `firmware/sentinelnode/sentinelnode.ino` | ESP32 Arduino firmware. Reads the sensors, applies the threshold rules, drives the LED and buzzer, and POSTs JSON |
| `sim/simulator.py` | Synthetic sensor simulator with healthy, capacitor, overload and loose_mount modes |
| `sentinelnode/autoencoder.py` | Tiny 6-8-3-8-6 autoencoder, int8 weight export to `firmware/sentinelnode/ae_model.h` |
| `firmware/sentinelnode/ae_infer.h` | Plain-C inference used on the ESP32 (tested against Python with gcc) |
| `scripts/eval_aging.py` | Early-warning evaluation on simulated 72 h capacitor-ageing runs → `docs/eval_aging.json` |
| `sentinelnode/model.py` | IsolationForest baseline, kept for comparison only (it missed most out-of-range faults in our simulated tests) |
| `sentinelnode/rules.py` | Threshold rules: hot-spot, temperature rise, vibration, ripple |
| `sentinelnode/edge_infer.py` | Rules + autoencoder → health score 0–100 and OK / Watch / Replace soon, with debouncing |
| `sentinelnode/api.py` | FastAPI dashboard backend |
| `tests/` | pytest suite |

Pin map: I²C on GPIO21/22, 1-Wire on GPIO4, ripple on ADC1 GPIO34, LED on GPIO25, buzzer on GPIO26.

## Simulated result (not a measurement)
On 5 simulated 72 h capacitor-ageing runs the autoencoder raised a debounced **Watch** on average **~6.4 h before**
the first fixed-limit rule tripped, with 0 false Watch events on 5 healthy runs (`docs/eval_aging.json`).

More: [features and limitations](docs/FEATURES_AND_LIMITATIONS.md) · [setup and wiring](docs/SETUP.md) · [AI disclosure](docs/AI_DISCLOSURE.md)

## Run
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
python -m sentinelnode.autoencoder          # retrain, regenerate ae_model.h
python -m scripts.eval_aging                # simulated early-warning eval
uvicorn sentinelnode.api:app --reload      # backend on :8000
python -m sim.simulator                    # stream simulated readings
```

## Bill of materials (approximate INR, **estimates**)
| Part | Est. ₹ |
|---|---|
| ESP32 DevKit v1 | ~322 |
| INA219 current/voltage module | ~99 |
| MLX90614 (GY-906) IR temperature sensor | ~709 |
| DS18B20 temperature probe | ~48 |
| MPU6050 accelerometer (vibration) | ~150 (estimate) |
| HLK-PM01 AC-DC supply | ~198 |
| IP65 enclosure | ~121 |
| PCB, passives, terminals, LED, buzzer, fuse | ~250 (estimate) |
| **Total** | **~₹1,900 (estimate)** |

Prices are indicative online listings (checked Oct 2026) and will vary.

## UI prototype (Figma)
- Prototype: https://www.figma.com/proto/J23b6PiV1w5VIlobLrInS0
- Design file: https://www.figma.com/design/J23b6PiV1w5VIlobLrInS0

| | |
|---|---|
| ![](docs/figma/01_desktop_fleet_overview.png) | ![](docs/figma/02_desktop_node_detail.png) |
| ![](docs/figma/03_desktop_alert_detail.png) | ![](docs/figma/04_desktop_settings.png) |
| ![](docs/figma/05_mobile_alert_notification.png) | ![](docs/figma/06_mobile_node_health.png) |
| ![](docs/figma/07_mobile_alert_detail.png) | ![](docs/figma/08_mobile_onboarding_pair.png) |
| ![](docs/figma/00_component_library.png) | |

The project document is in `docs/`.

## Team: Silicon Sentinels (CBIT Hyderabad, B.E. ECE)
- Bankiti Srishanth Reddy (Team Lead)
- Vedanidhi Kothur
- Sanneella Ashmitha
- Lavudya Chandrapathi
- Vasam Sai Varshini

## License

MIT, see [LICENSE](LICENSE). Copyright (c) 2026 Bankiti Srishanth Reddy and contributors.
