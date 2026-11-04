"""Synthetic sensor simulator for SentinelNode. All data is SIMULATED."""
import random

def reading(node_id="node-01", fault=None, rng=None):
    rng = rng or random.Random()
    r = {"node_id": node_id, "voltage_v": rng.gauss(12.0, 0.05), "current_ma": rng.gauss(800, 20),
         "temp_hot_c": rng.gauss(55, 2), "temp_amb_c": rng.gauss(32, 1),
         "vibration_g": abs(rng.gauss(0.2, 0.05)), "ripple_mv": abs(rng.gauss(60, 8))}
    if fault == "capacitor":  # aging cap: ESR up -> ripple + heat
        r["ripple_mv"] += rng.uniform(220, 400); r["temp_hot_c"] += rng.uniform(15, 35)
    elif fault == "overload":
        r["current_ma"] += rng.uniform(400, 800); r["temp_hot_c"] += rng.uniform(10, 25)
    elif fault == "loose_mount":
        r["vibration_g"] += rng.uniform(1.5, 3.0)
    return r

def dataset(n=500, fault=None, seed=0):
    rng = random.Random(seed)
    return [reading(fault=fault, rng=rng) for _ in range(n)]

if __name__ == "__main__":
    import json, sys, time, urllib.request
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api/readings"
    rng = random.Random()
    while True:
        r = reading(fault=rng.choice([None]*9 + ["capacitor"]), rng=rng)
        req = urllib.request.Request(url, json.dumps(r).encode(), {"Content-Type": "application/json"})
        print(urllib.request.urlopen(req).read().decode()); time.sleep(1)
