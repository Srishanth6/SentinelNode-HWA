"""Early-warning evaluation on SIMULATED capacitor-ageing runs.

For each run: when does the autoencoder raise a debounced 'watch', and when does the fixed
ripple/temperature rule first trip? Lead time = rule time - watch time (hours of simulated time).
Healthy runs of the same length count false 'watch' events per day.
Results go to docs/eval_aging.json. They are SIMULATED, not bench measurements.
"""
import json
from pathlib import Path
from sim.simulator import aging_run, dataset
from sentinelnode.autoencoder import train
from sentinelnode.edge_infer import infer, Debouncer


def _first(ts, flags):
    return next((t for t, f in zip(ts, flags) if f), None)


def evaluate(seeds=(0, 1, 2, 3, 4), ae=None, hours=72.0, onset_h=12.0, fail_h=60.0, debounce=5):
    ae = ae or train(dataset(3000, seed=0))
    cap, healthy = [], []
    for s in seeds:
        rows, ts = aging_run(hours, onset_h, fail_h, seed=100 + s)
        d = Debouncer(debounce)
        st = [d.update(infer(ae, r)["status"]) for r in rows]
        t_watch = _first(ts, [x != "ok" for x in st])
        t_rule = _first(ts, [bool(infer(ae, r)["rules"]) for r in rows])
        cap.append({"seed": s, "watch_h": t_watch, "rule_h": t_rule,
                    "lead_h": None if t_watch is None or t_rule is None else round(t_rule - t_watch, 2)})
        rows, ts = aging_run(hours, seed=200 + s, fault=None)
        d = Debouncer(debounce); prev = "ok"; events = 0
        for r in rows:
            cur = d.update(infer(ae, r)["status"])
            events += cur != "ok" and prev == "ok"; prev = cur
        healthy.append(events)
    leads = [c["lead_h"] for c in cap if c["lead_h"] is not None]
    return {"note": "SIMULATED data (sim/simulator.py aging_run); not bench measurements",
            "setup": {"hours": hours, "onset_h": onset_h, "end_of_life_h": fail_h,
                      "debounce_windows": debounce, "window": "1 min"},
            "capacitor": {"runs": cap, "mean_lead_time_h": round(sum(leads) / len(leads), 2) if leads else None},
            "healthy": {"false_watch_events": healthy,
                        "false_watch_events_per_day": round(sum(healthy) / (len(seeds) * hours / 24), 3)}}


if __name__ == "__main__":
    res = evaluate()
    Path("docs/eval_aging.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
