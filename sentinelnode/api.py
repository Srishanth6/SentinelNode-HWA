"""FastAPI dashboard backend. Run: uvicorn sentinelnode.api:app"""
from collections import defaultdict, deque
from fastapi import FastAPI
from pydantic import BaseModel
from .model import train
from .edge_infer import infer
from sim.simulator import dataset

app = FastAPI(title="SentinelNode")
MODEL = train(dataset(2000))
HISTORY = defaultdict(lambda: deque(maxlen=500))

class Reading(BaseModel):
    node_id: str; voltage_v: float; current_ma: float; temp_hot_c: float
    temp_amb_c: float; vibration_g: float; ripple_mv: float

@app.post("/api/readings")
def post_reading(r: Reading):
    res = infer(MODEL, r.model_dump()); HISTORY[r.node_id].append({**r.model_dump(), **res}); return res

@app.get("/api/nodes")
def nodes(): return [{"node_id": k, **{x: v[-1][x] for x in ("health", "status")}} for k, v in HISTORY.items()]

@app.get("/api/nodes/{node_id}/history")
def history(node_id: str): return list(HISTORY.get(node_id, []))

@app.get("/api/alerts")
def alerts(): return [h for v in HISTORY.values() for h in v if h["status"] == "alert"]
