import os
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def detect_drift(**kwargs):
    proc_dir = "/opt/airflow/data/processed"
    ref_path = "/opt/airflow/data/reference/features.parquet"
    cur_path = f"{proc_dir}/features.parquet"
    model_path = "/opt/airflow/data/models/model_xgb.pkl"
    art_dir = "/opt/airflow/data/artifacts"
    Path(art_dir).mkdir(parents=True, exist_ok=True)

    report = {}

    if not os.path.exists(cur_path):
        report["note"] = "No current features found. Skipping retrain."
        with open(f"{art_dir}/drift_report.json", "w") as f:
            json.dump(report, f, indent=2)
        return "skip_retrain"

    if not os.path.exists(model_path) and not os.path.exists(ref_path):
        report["note"] = "No model and no reference found. Forcing first training."
        with open(f"{art_dir}/drift_report.json", "w") as f:
            json.dump(report, f, indent=2)
        return "retrain_xgb"

    if os.path.exists(model_path) and not os.path.exists(ref_path):
        report["note"] = "Model found but no reference dataset. Forcing training to rebuild reference."
        with open(f"{art_dir}/drift_report.json", "w") as f:
            json.dump(report, f, indent=2)
        return "retrain_xgb"

    ref = pd.read_parquet(ref_path)
    cur = pd.read_parquet(cur_path)

    exclude_cols = ["y", "customer_id", "product_id", "week"]
    common = [c for c in ref.columns if c in cur.columns and c not in exclude_cols]
    drift = {}

    for c in common:
        r = ref[c].to_numpy()
        k = cur[c].to_numpy()
        r = r[~np.isnan(r)]
        k = k[~np.isnan(k)]
        if len(r) > 0 and len(k) > 0:
            _, p = ks_2samp(r, k)
            drift[c] = float(p)

    drift_detected = any(p < 0.05 for p in drift.values()) if drift else False

    report["ks_pvalues"] = drift
    report["drift_detected"] = drift_detected

    with open(f"{art_dir}/drift_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return "retrain_xgb" if drift_detected else "skip_retrain"