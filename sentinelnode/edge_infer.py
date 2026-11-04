"""Edge inference: combine threshold rules + IsolationForest into a 0-100 health score."""
from .model import to_matrix
from .rules import check

def infer(model, r: dict) -> dict:
    s = float(model.decision_function(to_matrix([r]))[0])   # >0 normal, <0 anomalous
    health = max(0, min(100, round(50 + s * 250)))
    rules = check(r)
    anomaly = bool(model.predict(to_matrix([r]))[0] == -1)
    status = "alert" if rules or (anomaly and health < 40) else ("watch" if anomaly else "ok")
    return {"node_id": r.get("node_id"), "health": health, "ml_anomaly": anomaly, "rules": rules, "status": status}
