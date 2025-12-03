import os
import json
import shutil
import numpy as np
import joblib
import mlflow
from pathlib import Path
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, average_precision_score, roc_auc_score
from xgboost import XGBClassifier
from mlflow_setup import get_mlflow_client
import scipy.sparse as sp

CONFIG_FILE = "/opt/airflow/data/config/xgb_best_params.json"


def _load_config():
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
    env = os.getenv("XGB_BEST_PARAMS", None)
    if env:
        try:
            cfg.update(json.loads(env))
        except Exception:
            pass
    return cfg


def _load_Xy():
    proc_dir = "/opt/airflow/data/processed"
    X_npz = f"{proc_dir}/X_trainval.npz"
    X_npy = f"{proc_dir}/X_trainval.npy"
    y = np.load(f"{proc_dir}/y_trainval.npy")
    if os.path.exists(X_npz):
        X = sp.load_npz(X_npz)
    else:
        X = np.load(X_npy, allow_pickle=True)
    return X, y


def _best_threshold(y_true, proba):
    grid = np.linspace(0.2, 0.8, 13)
    f1s = [f1_score(y_true, (proba >= t).astype(int)) for t in grid]
    i = int(np.argmax(f1s))
    return float(grid[i]), float(f1s[i])


def train_model(**kwargs):
    ml = get_mlflow_client()
    ml.xgboost.autolog()

    X, y = _load_Xy()
    params = _load_config()

    default = dict(
        objective="binary:logistic",
        eval_metric=params.get("eval_metric", "aucpr"),
        tree_method=params.get("tree_method", "hist"),
        random_state=params.get("random_state", 19),
        n_jobs=params.get("n_jobs", -1)
    )
    all_params = {**default, **params}

    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=19)
    oof = np.zeros_like(y, dtype=float)
    for tr, vl in skf.split(np.zeros(len(y)), y):
        model = XGBClassifier(**all_params)
        model.fit(X[tr], y[tr], eval_set=[(X[vl], y[vl])], verbose=False)
        oof[vl] = model.predict_proba(X[vl])[:, 1]

    thr, _ = _best_threshold(y, oof)

    with ml.start_run(run_name="xgb_retrain"):
        final = XGBClassifier(**all_params)
        final.fit(X, y, verbose=False)

        proba = final.predict_proba(X)[:, 1]
        y_pred = (proba >= thr).astype(int)

        metrics = {
            "roc_auc": float(roc_auc_score(y, proba)),
            "pr_auc": float(average_precision_score(y, proba)),
            "f1_at_thr": float(f1_score(y, y_pred)),
            "chosen_thr": thr
        }
        for k, v in metrics.items():
            ml.log_metric(k, v)
        ml.log_dict(all_params, "xgb_params_used.json")

        Path("/opt/airflow/data/models").mkdir(parents=True, exist_ok=True)
        joblib.dump(final, "/opt/airflow/data/models/model_xgb.pkl")
        with open("/opt/airflow/data/models/threshold.txt", "w") as f:
            f.write(str(thr))

        ml.sklearn.log_model(final, "xgb_model")
        ml.log_text(str(thr), "chosen_threshold.txt")

        ref_dir = Path("/opt/airflow/data/reference")
        ref_dir.mkdir(parents=True, exist_ok=True)
        
        proc_features = "/opt/airflow/data/processed/features.parquet"
        
        if os.path.exists(proc_features):
            # Guardar con timestamp para no sobrescribir
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ref_features_new = f"/opt/airflow/data/reference/features_{timestamp}.parquet"
            
            shutil.copyfile(proc_features, ref_features_new)
            ml.log_artifact(ref_features_new)