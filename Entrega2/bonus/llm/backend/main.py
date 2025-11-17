from fastapi import FastAPI
from pydantic import BaseModel
import os, re
import pandas as pd

DATA_DIR = os.getenv("DATA_DIR", "/mnt/data")  
app = FastAPI(title="LLM-lite Backend", description="Chatbot de preguntas sobre el dataset (rule-based)", version="1.0.0")

CLIENTES = None
PRODUCTOS = None
TRANSACCIONES = None

def _load():
    global CLIENTES, PRODUCTOS, TRANSACCIONES
    cp = os.path.join(DATA_DIR, "clientes.parquet")
    pp = os.path.join(DATA_DIR, "productos.parquet")
    tp = os.path.join(DATA_DIR, "transacciones.parquet")
    CLIENTES = pd.read_parquet(cp) if os.path.exists(cp) else pd.DataFrame()
    PRODUCTOS = pd.read_parquet(pp) if os.path.exists(pp) else pd.DataFrame()
    TRANSACCIONES = pd.read_parquet(tp) if os.path.exists(tp) else pd.DataFrame()
    for col in ["customer_id", "product_id"]:
        if col in TRANSACCIONES.columns:
            TRANSACCIONES[col] = TRANSACCIONES[col].astype(str)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str

@app.on_event("startup")
def startup():
    _load()

@app.get("/health")
def health():
    return {
        "status": "ok",
        "clientes": len(CLIENTES) if CLIENTES is not None else 0,
        "productos": len(PRODUCTOS) if PRODUCTOS is not None else 0,
        "transacciones": len(TRANSACCIONES) if TRANSACCIONES is not None else 0
    }

def _answer(msg: str) -> str:
    m = msg.lower()


    if "clientes únicos" in m or ("clientes" in m and "únicos" in m):
        if "customer_id" in TRANSACCIONES.columns:
            n = TRANSACCIONES["customer_id"].nunique()
            return f"Hay {n} clientes únicos en el dataset (basado en transacciones)."
        return "No encuentro la columna customer_id en las transacciones."


    if "transacciones" in m and "cliente" in m:
        m_id = re.search(r"cliente\s+([A-Za-z0-9\-\_]+)", m)
        if m_id and "customer_id" in TRANSACCIONES.columns:
            cid = m_id.group(1)
            cnt = int((TRANSACCIONES["customer_id"] == cid).sum())
            return f"El cliente {cid} tiene {cnt} transacciones registradas."
        return "No pude identificar el ID del cliente o falta la columna customer_id."

    if "productos únicos" in m or ("productos" in m and "únicos" in m):
        if "product_id" in TRANSACCIONES.columns:
            n = TRANSACCIONES["product_id"].nunique()
            return f"Hay {n} productos únicos en las transacciones."
        return "No encuentro la columna product_id en las transacciones."
    if "semanas" in m and "únicas" in m and "week" in TRANSACCIONES.columns:
        n = TRANSACCIONES["week"].nunique()
        return f"Hay {n} semanas únicas en las transacciones."

    return "Puedo responder preguntas como: '¿Cuántos clientes únicos hay?', '¿Cuántas transacciones ha realizado el cliente X?', '¿Cuántos productos únicos hay?'."

@app.post("/ask", response_model=ChatResponse)
def ask(req: ChatRequest):
    return ChatResponse(answer=_answer(req.message))
