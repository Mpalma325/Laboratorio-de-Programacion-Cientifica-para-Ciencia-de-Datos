import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from pathlib import Path
import json

def detect_drift(**kwargs):
    proc_dir = "/opt/airflow/data/processed"
    art_dir = "/opt/airflow/data/artifacts"
    Path(art_dir).mkdir(parents=True, exist_ok=True)

    ref_path = "/opt/airflow/data/reference/features.parquet"
    cur_path = f"{proc_dir}/features.parquet"

    ref = pd.read_parquet(ref_path)
    cur = pd.read_parquet(cur_path)

    common = [c for c in ref.columns if c in cur.columns and c != "y"]
    drift = {}
    for c in common:
        r = ref[c].to_numpy()
        k = cur[c].to_numpy()
        r = r[~np.isnan(r)]
        k = k[~np.isnan(k)]
        if len(r) > 0 and len(k) > 0:
            _, p = ks_2samp(r, k)
            drift[c] = float(p)

    drift_detected = any(p < 0.05 for p in drift.values())
    with open(f"{art_dir}/drift_report.json", "w") as f:
        json.dump({"ks_pvalues": drift, "drift_detected": drift_detected}, f, indent=2)

    print(f"🔍 drift: {drift_detected}")
    return "retrain" if drift_detected else "skip_retrain"
