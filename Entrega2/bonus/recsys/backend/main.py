from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import glob
import pandas as pd

APP_NAME = "SodAI RecSys Backend"
DESCRIPTION = "Sistema de recomendación que genera 5 productos sugeridos para cualquier cliente"

# Estos valores los sobreescribes en docker-compose:
# PREDICTIONS_DIR=/mnt/preds, PRODUCTS_DIR=/mnt/products, TRANSACTIONS_DIR=/mnt/transactions
PREDICTIONS_DIR = os.getenv("PREDICTIONS_DIR", "/opt/airflow/data/predictions")
PRODUCTS_DIR = os.getenv("PRODUCTS_DIR", "/opt/airflow/data/products")
TRANSACTIONS_DIR = os.getenv("TRANSACTIONS_DIR", "/opt/airflow/data/transactions")

app = FastAPI(title=APP_NAME, description=DESCRIPTION, version="1.0.0")

# CORS para comunicación con frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendationItem(BaseModel):
    product_id: str
    score: float
    rank: int


class RecommendationResponse(BaseModel):
    customer_id: str
    recommendations: List[RecommendationItem]
    week: int
    total_products: int


class CustomerInfo(BaseModel):
    customer_id: str
    exists: bool
    total_predictions: int
    week: int


def _get_latest_preds_path() -> str:
    """Obtiene el archivo de predicciones más reciente."""
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    files = sorted(
        glob.glob(os.path.join(PREDICTIONS_DIR, "*.parquet")),
        key=os.path.getmtime,
        reverse=True,
    )
    if not files:
        raise FileNotFoundError(
            f"No se encontraron archivos .parquet en {PREDICTIONS_DIR}"
        )
    return files[0]


def _read_latest_preds() -> tuple[pd.DataFrame, str]:
    """Lee el archivo de predicciones más reciente y retorna (df, path)."""
    path = _get_latest_preds_path()
    df = pd.read_parquet(path)

    # Asegurar tipos de datos
    if "customer_id" in df.columns:
        df["customer_id"] = df["customer_id"].astype(str)
    if "product_id" in df.columns:
        df["product_id"] = df["product_id"].astype(str)

    return df, path


def _load_product_catalog() -> pd.DataFrame:
    """
    Carga el catálogo de productos si existe.
    Si no existe, retorna un DataFrame vacío.
    (Actualmente no se usa, pero se mantiene por si lo quieres agregar después.)
    """
    try:
        catalog_path = os.path.join(PRODUCTS_DIR, "products.parquet")
        if os.path.exists(catalog_path):
            df = pd.read_parquet(catalog_path)
            df["product_id"] = df["product_id"].astype(str)
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["product_id", "product_name", "category"])


def _get_latest_transactions_path() -> str:
    """Obtiene el archivo de transacciones más reciente."""
    os.makedirs(TRANSACTIONS_DIR, exist_ok=True)
    files = sorted(
        glob.glob(os.path.join(TRANSACTIONS_DIR, "*.parquet")),
        key=os.path.getmtime,
        reverse=True,
    )
    if not files:
        return None
    return files[0]


def _read_latest_transactions() -> tuple[pd.DataFrame, str]:
    """
    Lee el archivo de transacciones más reciente.
    Las columnas esperadas son:
    - customer_id (int32)
    - product_id (int32)
    - order_id (int32)
    - purchase_date (datetime64[ns])
    - items (float32)
    """
    path = _get_latest_transactions_path()
    if not path:
        return None, None
    
    df = pd.read_parquet(path)
    
    # Asegurar tipos de datos correctos
    if "customer_id" in df.columns:
        df["customer_id"] = df["customer_id"].astype(str)
    if "product_id" in df.columns:
        df["product_id"] = df["product_id"].astype(str)
    if "order_id" in df.columns:
        df["order_id"] = df["order_id"].astype(str)
    if "purchase_date" in df.columns:
        df["purchase_date"] = pd.to_datetime(df["purchase_date"])
    if "items" in df.columns:
        df["items"] = df["items"].astype(float)
    
    return df, path


@app.get("/health")
def health():
    """Health check del servicio."""
    return {
        "status": "ok",
        "service": APP_NAME,
        "predictions_dir": PREDICTIONS_DIR,
        "transactions_dir": TRANSACTIONS_DIR,
    }


@app.get("/customers")
def list_customers():
    """Lista todos los customer_ids disponibles."""
    df, _ = _read_latest_preds()
    customers = df["customer_id"].unique().tolist()
    return {
        "total_customers": len(customers),
        "customers": customers[:100],  # Limitar a 100 para no saturar
    }


@app.get("/customer/{customer_id}", response_model=CustomerInfo)
def get_customer_info(customer_id: str):
    """Obtiene información de un cliente específico."""
    df, _ = _read_latest_preds()
    customer_df = df[df["customer_id"] == customer_id]

    if customer_df.empty:
        return CustomerInfo(
            customer_id=customer_id,
            exists=False,
            total_predictions=0,
            week=0,
        )

    week = int(customer_df["week"].mode().iloc[0]) if "week" in customer_df.columns else 0

    return CustomerInfo(
        customer_id=customer_id,
        exists=True,
        total_predictions=len(customer_df),
        week=week,
    )


@app.get("/recommend/{customer_id}", response_model=RecommendationResponse)
def recommend_products(customer_id: str, top_n: int = 5):
    """
    Genera top N recomendaciones para un cliente.
    Ordena por score descendente y retorna los mejores productos.
    """
    if top_n < 1 or top_n > 20:
        raise HTTPException(
            status_code=400,
            detail="top_n debe estar entre 1 y 20",
        )

    # Leer predicciones
    df, _ = _read_latest_preds()
    customer_df = df[df["customer_id"] == customer_id].copy()

    if customer_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No hay predicciones para customer_id={customer_id}",
        )

    if "score" not in customer_df.columns:
        raise HTTPException(
            status_code=500,
            detail="La columna 'score' no existe en las predicciones",
        )

    # Ordenar por score descendente y tomar top N
    customer_df = customer_df.sort_values("score", ascending=False).head(top_n)

    # Crear recomendaciones (solo Rank, Product ID y Score)
    recommendations: list[RecommendationItem] = []
    for idx, (_, row) in enumerate(customer_df.iterrows(), start=1):
        product_id = str(row["product_id"])
        recommendations.append(
            RecommendationItem(
                product_id=product_id,
                score=float(row["score"]),
                rank=idx,
            )
        )

    week = int(customer_df["week"].mode().iloc[0]) if "week" in customer_df.columns else 0

    return RecommendationResponse(
        customer_id=customer_id,
        recommendations=recommendations,
        week=week,
        total_products=len(customer_df),
    )


@app.get("/statistics")
def get_statistics():
    """
    Obtiene estadísticas generales del sistema de recomendación
    en el formato que espera el frontend de Recsys.
    """
    try:
        df, path = _read_latest_preds()
    except FileNotFoundError:
        # No hay archivos de predicciones: devolvemos estadísticas vacías,
        # pero con el mismo formato que usa el frontend.
        return {
            "predictions": {
                "total": 0,
                "unique_customers": 0,
                "unique_products": 0,
            },
            "transactions": None,
            "latest_file": None,
            "message": f"No se encontraron archivos .parquet en {PREDICTIONS_DIR}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al leer predicciones: {e}",
        )

    total_predictions = len(df)
    unique_customers = df["customer_id"].nunique() if "customer_id" in df.columns else 0
    unique_products = df["product_id"].nunique() if "product_id" in df.columns else 0

    # Leer estadísticas de transacciones
    transactions_stats = None
    try:
        trans_df, trans_path = _read_latest_transactions()
        if trans_df is not None and not trans_df.empty:
            transactions_stats = {
                "total": len(trans_df),
                "unique_customers": trans_df["customer_id"].nunique() if "customer_id" in trans_df.columns else 0,
                "unique_products": trans_df["product_id"].nunique() if "product_id" in trans_df.columns else 0,
                "unique_orders": trans_df["order_id"].nunique() if "order_id" in trans_df.columns else 0,
                "total_items": float(trans_df["items"].sum()) if "items" in trans_df.columns else 0,
                "latest_file": os.path.basename(trans_path) if trans_path else None,
            }
    except Exception as e:
        # Si hay error leyendo transacciones, no fallar todo el endpoint
        transactions_stats = {"error": str(e)}

    return {
        "predictions": {
            "total": total_predictions,
            "unique_customers": unique_customers,
            "unique_products": unique_products,
        },
        "latest_file": os.path.basename(path),
    }