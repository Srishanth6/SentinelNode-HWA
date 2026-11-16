import re, subprocess, shutil, json
from pathlib import Path
import numpy as np, pytest
from sim.simulator import dataset, aging_run
from sentinelnode.autoencoder import train, export_header, to_matrix
from scripts.eval_aging import evaluate

AE = train(dataset(3000, seed=0))

def test_weights_are_int8_and_small():
    assert all(w.dtype == np.int8 for w in AE.w_q)
    assert AE.meta["weight_bytes"] < 512

def test_header_roundtrip(tmp_path):
    h = export_header(AE, tmp_path / "ae_model.h").read_text()
    assert "AE_THRESHOLD" in h and "int8_t AE_W0" in h

@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc not installed")
def test_c_inference_matches_python(tmp_path):
    """Compile the firmware's ae_infer() on the host and compare with the Python reference."""
    export_header(AE, tmp_path / "ae_model.h")
    src = Path("firmware/sentinelnode/ae_infer.h").read_text()
    rows = dataset(20, seed=11) + dataset(5, fault="capacitor", seed=12)
    X = to_matrix(rows)
    body = "\n".join("{%s}," % ",".join(f"{v:.6f}f" for v in x) for x in X)
    (tmp_path / "ae_infer.h").write_text(src)
    (tmp_path / "t.c").write_text('#include <stdio.h>\n#include "ae_model.h"\n#include "ae_infer.h"\n'
        f"static const float X[{len(X)}][6]={{{body}}};\n"
        'int main(){for(int i=0;i<%d;i++)printf("%%.6f\\n",ae_error(X[i]));}\n' % len(X))
    subprocess.run(["gcc", "-O2", "-o", tmp_path / "t", tmp_path / "t.c", "-lm"], check=True)
    c = np.array([float(v) for v in subprocess.run([tmp_path / "t"], capture_output=True, text=True).stdout.split()])
    assert np.allclose(c, AE.error(X), rtol=1e-3, atol=1e-4)

def test_aging_early_warning():
    res = evaluate(seeds=[0, 1, 2], ae=AE)
    assert res["capacitor"]["mean_lead_time_h"] > 0         # warns before the hard ripple limit
    assert res["healthy"]["false_watch_events_per_day"] < 1.0
