import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime


def _safe_read(path):
    try:
        if os.path.exists(path):
            return pd.read_parquet(path)
    except Exception:
        pass
    return pd.DataFrame()


def predict_next_week(**kwargs):
    raw_dir = "/opt/airflow/data/raw"
    new_dir = "/opt/airflow/data/new_data"
    proc_dir = "/opt/airflow/data/processed"
    model_dir = "/opt/airflow/data/models"
    out_dir = "/opt/airflow/data/predictions"
    
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    
    new_trans_path = f"{new_dir}/transacciones.parquet"
    
    if os.path.exists(new_trans_path):
        trans_old = pd.read_parquet(f"{raw_dir}/transacciones.parquet")
        trans_new = pd.read_parquet(new_trans_path)
        
        df_cli = _safe_read(f"{raw_dir}/clientes.parquet")
        df_prod = _safe_read(f"{raw_dir}/productos.parquet")
        
        trans_all = pd.concat([trans_old, trans_new], ignore_index=True)
        
        trans_all["week_date"] = trans_all["purchase_date"].dt.to_period("W").apply(
            lambda r: r.start_time
        )
        trans_all = trans_all.sort_values("week_date")
        trans_all["week"] = pd.factorize(trans_all["week_date"])[0] + 1
        
        weekly = (
            trans_all.groupby(["customer_id", "product_id", "week"], as_index=False)
            .agg(items=("items", "sum"), n_orders=("order_id", "nunique"))
        )
        
        weeks_total = weekly["week"].unique()
        customers_total = weekly["customer_id"].unique()
        products_total = weekly["product_id"].unique()
        
        idx = pd.MultiIndex.from_product(
            [customers_total, products_total, weeks_total],
            names=["customer_id", "product_id", "week"]
        )
        full = pd.DataFrame(index=idx).reset_index()
        weekly_full = full.merge(
            weekly, on=["customer_id", "product_id", "week"], how="left"
        )
        
        if not df_cli.empty:
            weekly_full = weekly_full.merge(df_cli, on="customer_id", how="left")
        if not df_prod.empty:
            weekly_full = weekly_full.merge(df_prod, on="product_id", how="left")
        
        weekly_full["items"] = weekly_full["items"].fillna(0).astype("int32")
        weekly_full["n_orders"] = weekly_full["n_orders"].fillna(0).astype("int32")
        weekly_full["compra"] = (weekly_full["items"] > 0).astype("int8")
        
        feat_pipe = joblib.load(f"{model_dir}/feature_pipeline.pkl")
        df_feat_all = feat_pipe.transform(weekly_full)
        
        target_week = df_feat_all["week"].max()
        
    else:
        df_feat_all = pd.read_parquet(f"{proc_dir}/features.parquet")
        target_week = df_feat_all["week"].max()
    
    df_target = df_feat_all[df_feat_all["week"] == target_week].copy()
    
    preproc = joblib.load(f"{model_dir}/preprocessor.pkl")
    model = joblib.load(f"{model_dir}/model_xgb.pkl")
    
    thr = 0.5
    thr_path = f"{model_dir}/threshold.txt"
    if os.path.exists(thr_path):
        with open(thr_path, "r") as f:
            thr = float(f.read().strip())
    
    X_next = preproc.transform(df_target)
    proba = model.predict_proba(X_next)[:, 1]
    pred = (proba >= thr).astype("int8")
    
    out = df_target[["customer_id", "product_id", "week"]].copy()
    out["score"] = proba
    out["pred_compra"] = pred
    
    stamp = datetime.now().strftime("%Y%m%d")
    out_path = f"{out_dir}/preds_week_{int(target_week)}_{stamp}.parquet"
    out.to_parquet(out_path)
