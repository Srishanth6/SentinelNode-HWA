"""IsolationForest anomaly model trained on SIMULATED healthy data."""
import joblib, numpy as np
from sklearn.ensemble import IsolationForest
from . import FEATURES

def to_matrix(rows): return np.array([[r[f] for f in FEATURES] for r in rows])

def train(rows, seed=0):
    return IsolationForest(n_estimators=100, contamination=0.01, random_state=seed).fit(to_matrix(rows))

def save(m, path="model.joblib"): joblib.dump(m, path)
def load(path="model.joblib"): return joblib.load(path)

if __name__ == "__main__":
    from sim.simulator import dataset
    save(train(dataset(2000))); print("saved model.joblib (trained on simulated data)")
