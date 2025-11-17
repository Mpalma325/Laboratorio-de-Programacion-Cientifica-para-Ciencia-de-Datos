import os, json
import pandas as pd
import joblib
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

from transformers import DatosHistoricos, RecenciaSemanal, PopularidadProductoPrev, CompraRelativa

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

def prepare_data(**kwargs):
    raw_dir = "/opt/airflow/data/raw"
    proc_dir = "/opt/airflow/data/processed"
    model_dir = "/opt/airflow/data/models"
    Path(proc_dir).mkdir(parents=True, exist_ok=True)
    Path(model_dir).mkdir(parents=True, exist_ok=True)

    df_tx = pd.read_parquet(f"{raw_dir}/transacciones.parquet")
    path_cli = f"{raw_dir}/clientes.parquet"
    path_prod = f"{raw_dir}/productos.parquet"
    df_cli = pd.read_parquet(path_cli) if os.path.exists(path_cli) else pd.DataFrame()
    df_prod = pd.read_parquet(path_prod) if os.path.exists(path_prod) else pd.DataFrame()


    if not df_cli.empty:
        df_tx = df_tx.merge(df_cli, on="customer_id", how="left", validate="many_to_one")
    if not df_prod.empty:
        df_tx = df_tx.merge(df_prod, on="product_id", how="left", validate="many_to_one")
    feat_pipe = Pipeline([
        ("hist", DatosHistoricos()),
        ("rec",  RecenciaSemanal(inicio=1000)),
        ("pop",  PopularidadProductoPrev()),
        ("rel",  CompraRelativa())
    ])
    feat_pipe.set_output(transform="pandas")
    df_feat = feat_pipe.fit_transform(df_tx)

    if "compra" not in df_feat.columns:
        raise ValueError("Se requiere la columna 'compra' en los datos históricos.")


    numeric_columns = ["num_deliver_per_week", "items_prev", "recencia_producto",
                       "popularity_prev", "frec_producto", "size", "X", "Y"]
    categorical_columns = ["customer_type", "brand", "sub_category", "segment", "package"]
    drop_cols = ["customer_id","product_id","num_visit_per_week","category","n_orders","items","compra","week"]

    for c in numeric_columns + categorical_columns + drop_cols:
        if c not in df_feat.columns:
            df_feat[c] = pd.NA

    cfg = _load_config()
    ohe_min_freq = cfg.get("ohe_min_freq", None)

    num_pipe = Pipeline([
        ("imp",   SimpleImputer(strategy="median")),
        ("scale", StandardScaler())
    ])
    cat_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", min_frequency=ohe_min_freq,
                              dtype=float, sparse_output=True))
    ])

    preprocessor = ColumnTransformer([
        ("num", num_pipe, numeric_columns),
        ("cat", cat_pipe, categorical_columns),
        ("drop", "drop", drop_cols),
    ], remainder="drop", verbose_feature_names_out=False)

    X = preprocessor.fit_transform(df_feat)
    y = df_feat["compra"].astype(int).to_numpy()


    joblib.dump(preprocessor, f"{model_dir}/preprocessor.pkl")
    joblib.dump(feat_pipe,    f"{model_dir}/feature_pipeline.pkl")


    import numpy as np, scipy.sparse as sp
    if sp.issparse(X):
        sp.save_npz(f"{proc_dir}/X_trainval.npz", X)
    else:
        np.save(f"{proc_dir}/X_trainval.npy", X)
    np.save(f"{proc_dir}/y_trainval.npy", y)


    df_out = pd.DataFrame.sparse.from_spmatrix(X) if sp.issparse(X) else pd.DataFrame(X)
    df_out["y"] = y
    df_out.to_parquet(f"{proc_dir}/features.parquet")
