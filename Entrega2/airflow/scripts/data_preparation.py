import os
import json
import numpy as np
import pandas as pd
import joblib
import scipy.sparse as sp
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

from scripts.transformers import DatosHistoricos, RecenciaSemanal, PopularidadProductoPrev, CompraRelativa

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
    new_data_dir = "/opt/airflow/data/new_data"
    proc_dir = "/opt/airflow/data/processed"
    model_dir = "/opt/airflow/data/models"
    Path(proc_dir).mkdir(parents=True, exist_ok=True)
    Path(model_dir).mkdir(parents=True, exist_ok=True)


    transacciones = pd.read_parquet(f"{raw_dir}/transacciones.parquet")
    

    new_data_path = Path(new_data_dir)
    if new_data_path.exists():
        new_files = list(new_data_path.glob("*.parquet"))
        if new_files:
            nuevas_transacciones = [pd.read_parquet(f) for f in new_files]
            transacciones = pd.concat([transacciones] + nuevas_transacciones, ignore_index=True)
    

    path_cli = f"{raw_dir}/clientes.parquet"
    path_prod = f"{raw_dir}/productos.parquet"
    clientes = pd.read_parquet(path_cli) if os.path.exists(path_cli) else pd.DataFrame()
    productos = pd.read_parquet(path_prod) if os.path.exists(path_prod) else pd.DataFrame()

    transacciones["week_date"] = transacciones["purchase_date"].dt.to_period("W").apply(
        lambda r: r.start_time
    )
    transacciones = transacciones.sort_values("week_date")
    transacciones["week"] = pd.factorize(transacciones["week_date"])[0] + 1
    transacciones["month"] = transacciones["purchase_date"].dt.month

    weekly = (
        transacciones.groupby(["customer_id", "product_id", "week"], as_index=False)
        .agg(
            items=("items", "sum"),
            n_orders=("order_id", "nunique"),
            month=("month", "first")
        )
    )

    weeks_total = weekly["week"].unique()
    customers_total = weekly["customer_id"].unique()
    products_total = weekly["product_id"].unique()
    

    max_week = weeks_total.max()
    next_week = max_week + 1
    weeks_with_future = np.append(weeks_total, next_week)

    # Crear índice completo incluyendo semana futura
    idx = pd.MultiIndex.from_product(
        [customers_total, products_total, weeks_with_future],
        names=["customer_id", "product_id", "week"]
    )
    full = pd.DataFrame(index=idx).reset_index()
    weekly_full = full.merge(
        weekly[["customer_id", "product_id", "week", "items", "n_orders"]],
        on=["customer_id", "product_id", "week"],
        how="left"
    )


    if not clientes.empty:
        weekly_full = weekly_full.merge(clientes, on="customer_id", how="left")
    if not productos.empty:
        weekly_full = weekly_full.merge(productos, on="product_id", how="left")

    weekly_full["items"] = weekly_full["items"].fillna(0).astype("int32")
    weekly_full["n_orders"] = weekly_full["n_orders"].fillna(0).astype("int32")
    weekly_full["compra"] = (weekly_full["items"] > 0).astype("int8")


    feat_pipe = Pipeline([
        ("hist", DatosHistoricos()),
        ("rec", RecenciaSemanal(inicio=1000)),
        ("pop", PopularidadProductoPrev()),
        ("rel", CompraRelativa())
    ])
    feat_pipe.set_output(transform="pandas")
    
    df_feat = feat_pipe.fit_transform(weekly_full)

    # Definir columnas
    numeric_columns = [
        "num_deliver_per_week", "items_prev", "recencia_producto",
        "popularity_prev", "frec_producto", "size", "X", "Y"
    ]
    categorical_columns = [
        "customer_type", "brand", "sub_category", "segment", "package"
    ]
    drop_cols = [
        "customer_id", "product_id", "num_visit_per_week", "category",
        "n_orders", "items", "compra", "week"
    ]

    for c in numeric_columns + categorical_columns + drop_cols:
        if c not in df_feat.columns:
            df_feat[c] = pd.NA

    cfg = _load_config()
    ohe_min_freq = cfg.get("ohe_min_freq", None)

    num_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scale", StandardScaler())
    ])
    cat_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(
            handle_unknown="ignore",
            min_frequency=ohe_min_freq,
            dtype=float,
            sparse_output=True
        ))
    ])

    preprocessor = ColumnTransformer([
        ("num", num_pipe, numeric_columns),
        ("cat", cat_pipe, categorical_columns),
        ("drop", "drop", drop_cols),
    ], remainder="drop", verbose_feature_names_out=False)


    df_historic = df_feat[df_feat["week"] != next_week].copy()
    df_future = df_feat[df_feat["week"] == next_week].copy()
    

    X = preprocessor.fit_transform(df_historic)
    y = df_historic["compra"].astype(int).to_numpy()

    joblib.dump(preprocessor, f"{model_dir}/preprocessor.pkl")
    joblib.dump(feat_pipe, f"{model_dir}/feature_pipeline.pkl")

    sp.save_npz(f"{proc_dir}/X_trainval.npz", X)
    np.save(f"{proc_dir}/y_trainval.npy", y)

    keep_cols = numeric_columns + categorical_columns + ["customer_id", "product_id", "week"]
    df_historic_clean = df_historic[keep_cols].copy()
    df_historic_clean['y'] = y
    df_historic_clean.to_parquet(f"{proc_dir}/features.parquet")
    

    df_future_clean = df_future[keep_cols].copy()
    df_future_clean.to_parquet(f"{proc_dir}/features_future.parquet")