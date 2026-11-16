import random
from fastapi.testclient import TestClient
from sim.simulator import dataset, reading
from sentinelnode.autoencoder import train
from sentinelnode.edge_infer import infer, Debouncer
from sentinelnode.rules import check
from sentinelnode.api import app

AE = train(dataset(3000, seed=0))

def test_rules_healthy_clean(): assert check(reading(rng=random.Random(3))) == []
def test_rules_capacitor(): assert "high_ripple" in check(reading(fault="capacitor", rng=random.Random(3)))
def test_rules_vibration(): assert "high_vibration" in check(reading(fault="loose_mount", rng=random.Random(3)))
def test_ml_flags_most_faults():
    for f in ("overload", "capacitor", "loose_mount"):
        bad = dataset(100, fault=f, seed=5)
        assert sum(infer(AE, r)["ml_anomaly"] for r in bad) >= 90, f
def test_ml_healthy_mostly_ok():
    good = dataset(200, seed=9)
    assert sum(infer(AE, r)["status"] == "ok" for r in good) >= 190
def test_debouncer():
    d = Debouncer(3)
    assert [d.update(s) for s in ["watch", "ok", "watch", "watch", "watch", "alert"]] == ["ok"] * 4 + ["watch", "watch"]
def test_api_flow():
    c = TestClient(app)
    assert c.post("/api/readings", json=reading(fault="capacitor", rng=random.Random(1))).json()["status"] == "alert"
    assert c.get("/api/nodes").json()[0]["node_id"] == "node-01"
    assert len(c.get("/api/alerts").json()) >= 1
