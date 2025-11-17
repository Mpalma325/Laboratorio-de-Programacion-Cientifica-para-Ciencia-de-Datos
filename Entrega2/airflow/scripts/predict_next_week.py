import os
import joblib
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
    out_dir = "/opt/airflow/data/predictions"
    model_dir = "/opt/airflow/data/models"

    Path(out_dir).mkdir(parents=True, exist_ok=True)

    df_hist = pd.read_parquet(f"{raw_dir}/transacciones.parquet")
    df_new  = _safe_read(f"{new_dir}/transacciones.parquet")
    df_cli = _safe_read(f"{raw_dir}/clientes.parquet")
    df_prod = _safe_read(f"{raw_dir}/productos.parquet")

    if not df_cli.empty:
        df_hist = df_hist.merge(df_cli, on="customer_id", how="left")
        if not df_new.empty:
            df_new = df_new.merge(df_cli, on="customer_id", how="left")
    if not df_prod.empty:
        df_hist = df_hist.merge(df_prod, on="product_id", how="left")
        if not df_new.empty:
            df_new = df_new.merge(df_prod, on="product_id", how="left")

    if not df_new.empty and "compra" not in df_new.columns:
        df_new["compra"] = 0

    df_all = pd.concat([df_hist, df_new], ignore_index=True, sort=False)

    wmax_hist = int(df_hist["week"].max())
    wmax_new  = int(df_new["week"].max()) if ("week" in df_new.columns and len(df_new)) else wmax_hist
    target_week = max(wmax_hist, wmax_new) + 1
    feat_pipe = joblib.load(f"{model_dir}/feature_pipeline.pkl")
    preproc   = joblib.load(f"{model_dir}/preprocessor.pkl")
    model     = joblib.load(f"{model_dir}/model_xgb.pkl")

    thr = 0.5
    thr_path = f"{model_dir}/threshold.txt"
    if os.path.exists(thr_path):
        try:
            with open(thr_path, "r") as f:
                thr = float(f.read().strip())
        except Exception:
            pass


    df_feat_all = feat_pipe.transform(df_all)
    if "week" not in df_feat_all.columns:
        raise ValueError("La tabla de features no contiene la columna 'week'.")

    df_target = df_feat_all[df_feat_all["week"] == target_week].copy()
    if df_target.empty:
        raise ValueError(
            f"No hay filas para la semana objetivo {target_week}. "
            "Verifica que 'week' avance secuencialmente y que t/t+1 estén cargados correctamente."
        )


    X_next = preproc.transform(df_target)
    proba  = model.predict_proba(X_next)[:, 1]
    pred   = (proba >= thr).astype("int8")

    keys = [c for c in ["customer_id", "product_id", "week"] if c in df_target.columns]
    out = df_target[keys].copy()
    out["score"] = proba
    out["pred_compra"] = pred

    stamp = datetime.now().strftime("%Y%m%d")
    out_path = f"{out_dir}/preds_week_{int(target_week)}_{stamp}.parquet"
    out.to_parquet(out_path)
