from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Tuple
import os
import pandas as pd
from collections import Counter, defaultdict

DATA_DIR = os.getenv("DATA_DIR", "/mnt/data")  # carpeta con clientes/productos/transacciones.parquet

app = FastAPI(title="Recsys Backend", description="Recomendador simple por co-ocurrencia + popularidad", version="1.0.0")

class RecRequest(BaseModel):
    customer_id: int | str = Field(..., description="ID del cliente")
    k: int = Field(5, ge=1, le=50, description="Cantidad de recomendaciones")

class RecItem(BaseModel):
    product_id: str
    score: float

class RecResponse(BaseModel):
    customer_id: str
    n_candidates: int
    items: List[RecItem]

def _load_transactions() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "transacciones.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró {path}. Monta bonus/recsys/docker-compose.yml al RAW de Airflow.")
    df = pd.read_parquet(path)
    if "customer_id" not in df.columns or "product_id" not in df.columns:
        raise ValueError("transacciones.parquet debe contener columnas customer_id y product_id")
    df["customer_id"] = df["customer_id"].astype(str)
    df["product_id"] = df["product_id"].astype(str)
    return df

# --------- Carga inicial (lazy) ---------
TX = None
CUST_BUYS: Dict[str, set] = {}
PROD_BUYS: Dict[str, set] = {}
POPULARITY: Counter = Counter()

def _ensure_indexed():
    global TX, CUST_BUYS, PROD_BUYS, POPULARITY
    if TX is not None:
        return
    TX = _load_transactions()
    # sets por cliente y producto
    CUST_BUYS = TX.groupby("customer_id")["product_id"].apply(lambda s: set(s.tolist())).to_dict()
    PROD_BUYS = TX.groupby("product_id")["customer_id"].apply(lambda s: set(s.tolist())).to_dict()
    POPULARITY = Counter(TX["product_id"].value_counts().to_dict())

@app.get("/health")
def health():
    try:
        _ensure_indexed()
        return {"status": "ok", "n_customers": len(CUST_BUYS), "n_products": len(PROD_BUYS)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/recommend", response_model=RecResponse)
def recommend(req: RecRequest):
    _ensure_indexed()
    cid = str(req.customer_id)
    bought = CUST_BUYS.get(cid, set())

    # Co-ocurrencia: productos que compraron otros clientes que compraron lo que tú compraste
    scores = Counter()
    for p in bought:
        neighbors = PROD_BUYS.get(p, set())
        for other_c in neighbors:
            for q in CUST_BUYS.get(other_c, set()):
                if q not in bought:
                    scores[q] += 1.0

    # si hay pocos candidatos, rellenar con populares (no comprados)
    if len(scores) < req.k:
        for q, _ in POPULARITY.most_common():
            if q not in bought:
                scores[q] += 0.0001  # pequeño empuje para ordenar
            if len(scores) >= req.k * 3:  # límite razonable
                break

    ranked: List[Tuple[str, float]] = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:req.k]
    items = [RecItem(product_id=pid, score=float(sc)) for pid, sc in ranked]
    return RecResponse(customer_id=cid, n_candidates=len(ranked), items=items)
