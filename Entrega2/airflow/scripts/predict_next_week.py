import os
import joblib
import pandas as pd
from pathlib import Path
from datetime import datetime


def predict_next_week(**kwargs):
    proc_dir = "/opt/airflow/data/processed"
    model_dir = "/opt/airflow/data/models"
    out_dir = "/opt/airflow/data/predictions"
    
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    
    df_future = pd.read_parquet(f"{proc_dir}/features_future.parquet")
    target_week = df_future["week"].iloc[0]
    
    preproc = joblib.load(f"{model_dir}/preprocessor.pkl")
    model = joblib.load(f"{model_dir}/model_xgb.pkl")
    
    thr = 0.5
    thr_path = f"{model_dir}/threshold.txt"
    if os.path.exists(thr_path):
        with open(thr_path, "r") as f:
            thr = float(f.read().strip())
    
    X_next = preproc.transform(df_future)
    proba = model.predict_proba(X_next)[:, 1]
    pred = (proba >= thr).astype("int8")
    
    out = df_future[["customer_id", "product_id", "week"]].copy()
    out["score"] = proba
    out["pred_compra"] = pred
    
    stamp = datetime.now().strftime("%Y%m%d")
    out_path = f"{out_dir}/preds_week_{int(target_week)}_{stamp}.parquet"
    out.to_parquet(out_path)
    
    submission = out[out["pred_compra"] == 1][["customer_id", "product_id"]]
    submission_path = f"{out_dir}/submission_week_{int(target_week)}_{stamp}.csv"
    submission.to_csv(submission_path, index=False, header=False)