"""Synthetic sensor simulator for SentinelNode. All data is SIMULATED, not measured.

Healthy model (a 12 V DC rail feeding a load board, sampled once per 1-minute window):
  * load current wanders between ~650 and ~950 mA
  * hot-spot temperature = ambient + I^2-dependent self-heating (couples temp to load)
  * ripple scales with load current
These couplings are what the autoencoder learns, so it can flag a broken relationship
(e.g. a hot-spot that is hotter than the present load explains) before any fixed limit trips.
"""
import math
import random

NOMINAL_MA = 800.0


def _healthy(rng, node_id, current_ma=None, temp_amb_c=None):
    i = current_ma if current_ma is not None else min(950.0, max(650.0, rng.gauss(NOMINAL_MA, 70)))
    amb = temp_amb_c if temp_amb_c is not None else rng.gauss(32, 1)
    load = i / NOMINAL_MA
    return {"node_id": node_id,
            "voltage_v": rng.gauss(12.0 - 0.0002 * (i - NOMINAL_MA), 0.03),
            "current_ma": rng.gauss(i, 8),
            "temp_hot_c": amb + 18.0 * load ** 2 + rng.gauss(0, 0.8),
            "temp_amb_c": amb,
            "vibration_g": abs(rng.gauss(0.2, 0.05)),
            "ripple_mv": abs(rng.gauss(60.0 * load, 5))}


def reading(node_id="node-01", fault=None, rng=None):
    rng = rng or random.Random()
    r = _healthy(rng, node_id)
    if fault == "capacitor":  # aged electrolytic: ESR up -> ripple + self-heating
        r["ripple_mv"] += rng.uniform(220, 400); r["temp_hot_c"] += rng.uniform(15, 35)
    elif fault == "overload":
        r["current_ma"] += rng.uniform(400, 800); r["temp_hot_c"] += rng.uniform(10, 25)
    elif fault == "loose_mount":
        r["vibration_g"] += rng.uniform(1.5, 3.0)
    return r


def dataset(n=500, fault=None, seed=0):
    rng = random.Random(seed)
    return [reading(fault=fault, rng=rng) for _ in range(n)]


def aging_run(hours=72.0, onset_h=12.0, fail_h=60.0, seed=0, node_id="node-01", fault="capacitor"):
    """One reading per simulated minute.

    capacitor: from onset_h, ESR grows smoothly so that at fail_h the extra ripple is +300 mV and
    the extra hot-spot heating is +30 C (roughly 6x ripple, typical of an electrolytic near end of life).
    fault=None gives a healthy run of the same length (used for false-alarm counting).
    Returns (rows, t_hours)."""
    rng = random.Random(seed)
    rows, ts = [], []
    n = int(hours * 60)
    for k in range(n):
        t = k / 60.0
        amb = 32 + 2.5 * math.sin(2 * math.pi * (t - 9) / 24)          # daily ambient swing
        r = _healthy(rng, node_id, temp_amb_c=amb)
        if fault == "capacitor" and t > onset_h:
            x = min(1.0, (t - onset_h) / (fail_h - onset_h))
            g = x ** 2                                                  # slow start, faster near end of life
            r["ripple_mv"] += 300 * g
            r["temp_hot_c"] += 30 * g
        rows.append(r); ts.append(t)
    return rows, ts


if __name__ == "__main__":
    import json, sys, time, urllib.request
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api/readings"
    rng = random.Random()
    while True:
        r = reading(fault=rng.choice([None] * 9 + ["capacitor"]), rng=rng)
        req = urllib.request.Request(url, json.dumps(r).encode(), {"Content-Type": "application/json"})
        print(urllib.request.urlopen(req).read().decode()); time.sleep(1)
