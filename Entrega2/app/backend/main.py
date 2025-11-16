from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import os, glob
import pandas as pd

APP_NAME = "SodAI Drinks Backend"
DESCRIPTION = (
    "Backend FastAPI que expone predicciones generadas por el pipeline de Airflow.\n"
    "Lee el último archivo .parquet de predicciones y permite consultarlas."
)

# === Configuración ===
PREDICTIONS_DIR = os.getenv("PREDICTIONS_DIR", "/opt/airflow/data/predictions")

app = FastAPI(title=APP_NAME, description=DESCRIPTION, version="1.0.0")


# --------- Modelos de entrada/salida ---------
class PredictRequest(BaseModel):
    customer_id: int | str = Field(..., description="ID del cliente")
    top_k: int = Field(10, ge=1, le=100, description="Cantidad de productos a recomendar")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Filtrar por score mínimo (opcional)")

class PredictPairRequest(BaseModel):
    customer_id: int | str
    product_id: int | str

class PredictionItem(BaseModel):
    customer_id: str
    product_id: str
    week: int
    score: float
    pred_compra: int

class PredictResponse(BaseModel):
    week: int
    n_returned: int
    items: List[PredictionItem]

class MetaResponse(BaseModel):
    latest_file: str
    week: int
    n_rows: int


# --------- Funciones auxiliares ---------
def _coerce_str(v) -> str:
    return str(v)

def _get_latest_preds_path() -> str:
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(PREDICTIONS_DIR, "*.parquet")), key=os.path.getmtime, reverse=True)
    if not files:
        raise FileNotFoundError(
            f"No se encontraron archivos .parquet en {PREDICTIONS_DIR}. "
            "Ejecuta el pipeline de Airflow para generar predicciones."
        )
    return files[0]

def _read_latest_preds() -> pd.DataFrame:
    path = _get_latest_preds_path()
    df = pd.read_parquet(path)
    missing = {"customer_id", "product_id", "week", "score", "pred_compra"} - set(df.columns)
    if missing:
        raise ValueError(f"El archivo {path} no contiene columnas {missing}")
    df["customer_id"] = df["customer_id"].apply(_coerce_str)
    df["product_id"]  = df["product_id"].apply(_coerce_str)
    return df, path


# --------- Endpoints ---------
@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "predictions_dir": PREDICTIONS_DIR}

@app.get("/metadata", response_model=MetaResponse)
def metadata():
    df, path = _read_latest_preds()
    week = int(df["week"].mode().iloc[0]) if "week" in df.columns else -1
    return MetaResponse(latest_file=os.path.basename(path), week=week, n_rows=int(len(df)))

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    df, path = _read_latest_preds()
    df_c = df[df["customer_id"] == _coerce_str(req.customer_id)].copy()
    if df_c.empty:
        raise HTTPException(status_code=404, detail=f"No hay predicciones para customer_id={req.customer_id}")

    if req.min_score is not None:
        df_c = df_c[df_c["score"] >= req.min_score]

    df_c = df_c.sort_values("score", ascending=False).head(req.top_k)
    if df_c.empty:
        raise HTTPException(status_code=404, detail=f"Sin productos tras aplicar filtros.")

    week = int(df_c["week"].mode().iloc[0])
    items = [
        PredictionItem(
            customer_id=str(r["customer_id"]),
            product_id=str(r["product_id"]),
            week=int(r["week"]),
            score=float(r["score"]),
            pred_compra=int(r["pred_compra"])
        )
        for _, r in df_c.iterrows()
    ]
    return PredictResponse(week=week, n_returned=len(items), items=items)

@app.post("/predict_pair", response_model=PredictionItem)
def predict_pair(req: PredictPairRequest):
    df, path = _read_latest_preds()
    m = (
        (df["customer_id"] == _coerce_str(req.customer_id)) &
        (df["product_id"] == _coerce_str(req.product_id))
    )
    row = df[m]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"No hay predicción para ese par de IDs")
    r = row.iloc[0]
    return PredictionItem(
        customer_id=str(r["customer_id"]),
        product_id=str(r["product_id"]),
        week=int(r["week"]),
        score=float(r["score"]),
        pred_compra=int(r["pred_compra"])
    )
