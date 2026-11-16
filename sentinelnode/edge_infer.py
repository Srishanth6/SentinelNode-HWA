"""Edge inference: threshold rules + int8 autoencoder -> 0-100 health score and a 3-level status.

Same logic as ae_infer()/classify() in firmware/sentinelnode/sentinelnode.ino.
  ok     : no rule fired and reconstruction error below the healthy threshold
  watch  : the autoencoder sees a pattern unlike the learned healthy baseline (early warning)
  alert  : a hard limit tripped, or health fell below ALERT_HEALTH ("replace soon")
An optional IsolationForest (model.py) is kept as a secondary check for comparison only.
"""
from .autoencoder import QuantAE, to_matrix
from .rules import check

ALERT_HEALTH = 25


def infer(ae: QuantAE, r: dict, iforest=None) -> dict:
    X = to_matrix([r])
    err = float(ae.error(X)[0])
    health = int(ae.health(X)[0])
    rules = check(r)
    anomaly = err > ae.threshold
    status = "alert" if rules or health < ALERT_HEALTH else ("watch" if anomaly else "ok")
    out = {"node_id": r.get("node_id"), "health": health, "recon_error": round(err, 4),
           "ml_anomaly": bool(anomaly), "rules": rules, "status": status}
    if iforest is not None:
        from .model import to_matrix as m
        out["iforest_anomaly"] = bool(iforest.predict(m([r]))[0] == -1)
    return out


class Debouncer:
    """Raise a status only after `n` consecutive windows agree, so one noisy window pages nobody."""
    ORDER = {"ok": 0, "watch": 1, "alert": 2}

    def __init__(self, n: int = 3):
        self.n, self.hist, self.state = n, [], "ok"

    def update(self, status: str) -> str:
        self.hist = (self.hist + [status])[-self.n:]
        if len(self.hist) == self.n:
            self.state = min(self.hist, key=self.ORDER.get)   # weakest of the last n windows
        return self.state
