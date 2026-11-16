# SentinelNode: features and limitations

HackWithAditya 2026 Level 1 · Team Silicon Sentinels (HWA26-LMNB) · Robotics, IoT & Smart Manufacturing

> Status (16 Nov 2026): software prototype runs end to end on **simulated** sensor data. The hardware node is
> still being built, so **no bench or field measurements exist yet**. Every number below comes from the simulator.

## Working now (software)

| Feature | Where | How to check |
|---|---|---|
| Sensor simulator with healthy, capacitor, overload and loose-mount modes; load-coupled self-heating and ripple; 72 h capacitor-ageing runs | `sim/simulator.py` | `python -m sim.simulator` |
| Threshold rules: hot-spot over-temperature, temperature rise over ambient, vibration, ripple | `sentinelnode/rules.py` and the firmware | `pytest -q` |
| Tiny autoencoder (6-8-3-8-6, ReLU), int8 weights (144 bytes), threshold at the 99.5th percentile of healthy error | `sentinelnode/autoencoder.py` | `python -m sentinelnode.autoencoder` |
| Export of the model to a C header, and plain-C inference that matches Python (checked by compiling it with gcc in the tests) | `firmware/sentinelnode/ae_model.h`, `ae_infer.h` | `pytest -q tests/test_autoencoder.py` |
| Health score 0–100 and three levels (OK / Watch / Replace soon), debounced over consecutive windows | `sentinelnode/edge_infer.py` and the firmware | `pytest -q` |
| Early-warning evaluation on simulated capacitor ageing | `scripts/eval_aging.py` → `docs/eval_aging.json` | `python -m scripts.eval_aging` |
| FastAPI backend: readings, nodes, history, alerts | `sentinelnode/api.py` | `uvicorn sentinelnode.api:app` |
| ESP32 firmware: sensor reads, on-device autoencoder, local LED/buzzer alarm without Wi-Fi, HTTP JSON upload, optional ThingsBoard MQTT telemetry | `firmware/sentinelnode/sentinelnode.ino` | compiles for `esp32:esp32:esp32` with arduino-cli and ESP32 core 3.3.12, both with and without ThingsBoard (checked 16 Nov 2026) |
| UI design for desktop and mobile | `docs/figma/` | Figma prototype link in README |

### Simulated result (not a measurement)
On 5 simulated 72-hour capacitor-ageing runs, the autoencoder raised a debounced **Watch** on average
**about 6.4 hours before** the first fixed-limit rule tripped (range 3.0–8.4 h), with **0 false Watch events**
on 5 healthy 72-hour runs. See `docs/eval_aging.json`. These numbers only show the pipeline works as intended
on synthetic data; they say nothing yet about real boards.

## Limitations (honest list)
1. **No hardware results.** Sensors have not been brought up; thresholds, the healthy baseline and the model must be re-learned on the real board.
2. **Simulated training data.** The simulator's physics (I²R heating, ripple vs load, ESR growth) is simplified. The NASA PCoE capacitor-ageing data is planned for validation and is not used yet.
3. **Weight-only int8.** Weights are int8 and activations are float32 in plain C. A full-integer TensorFlow Lite Micro build is the next step.
4. **One board type.** The model is per-board: each node learns its own board's healthy baseline. Transfer between board types has not been studied.
5. **Ripple input** is a simple AC-coupled peak-to-peak reading on the ESP32 ADC. Its accuracy is limited by ADC noise and non-linearity, and it has not been calibrated against an oscilloscope.
6. **Low-voltage DC only** (rails up to 26 V, the INA219 limit). Mains-side monitoring is out of scope for safety reasons.
7. **SMS alerts** need a DLT-registered gateway account; this is not set up yet, so alerts currently go to the LED/buzzer, the serial log and the API.
8. **No authentication** on the demo API; it is meant for a local network only.

## Next steps (before the 18–20 Dec on-site round, if shortlisted)
- Bring up INA219, MLX90614, DS18B20, MPU6050 and the ripple input on the bench; log a healthy baseline on a 12 V buck-converter board.
- Retrain the autoencoder on that baseline, then demo an aged or heated capacitor and show the health score fall.
- Swap in a full-integer TFLite Micro model; add ThingsBoard dashboards and SMS.
