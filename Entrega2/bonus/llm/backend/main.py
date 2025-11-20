<<<<<<< HEAD
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import glob
import pandas as pd
import re

APP_NAME = "SodAI LLM Chatbot Backend"
DESCRIPTION = "Chatbot conversacional que responde preguntas sobre los datos del sistema"

DATA_DIR = os.getenv("DATA_DIR", "/opt/airflow/data")
PREDICTIONS_DIR = os.path.join(DATA_DIR, "predictions")
TRANSACTIONS_DIR = os.path.join(DATA_DIR, "transactions")

app = FastAPI(title=APP_NAME, description=DESCRIPTION, version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str


# Cache para datos
_cache = {
    "predictions": None,
    "transactions": None,
    "stats": None
}

def _load_predictions() -> pd.DataFrame:
    """Carga el archivo de predicciones más reciente"""
    if _cache["predictions"] is not None:
        return _cache["predictions"]
    
    try:
        files = sorted(
            glob.glob(os.path.join(PREDICTIONS_DIR, "*.parquet")),
            key=os.path.getmtime,
            reverse=True
        )
        if files:
            df = pd.read_parquet(files[0])
            _cache["predictions"] = df
            return df
    except Exception:
        pass
    
    return pd.DataFrame()

def _load_transactions() -> pd.DataFrame:
    """Carga datos de transacciones si existen"""
    if _cache["transactions"] is not None:
        return _cache["transactions"]
    
    try:
        files = glob.glob(os.path.join(TRANSACTIONS_DIR, "*.parquet"))
        if files:
            df = pd.read_parquet(files[0])
            _cache["transactions"] = df
            return df
    except Exception:
        pass
    
    return pd.DataFrame()

def _get_statistics():
    """Calcula estadísticas del sistema"""
    if _cache["stats"] is not None:
        return _cache["stats"]
    
    preds_df = _load_predictions()
    trans_df = _load_transactions()
    
    stats = {
        "predictions": {
            "total": int(len(preds_df)),
            "unique_customers": int(preds_df["customer_id"].nunique()) if not preds_df.empty else 0,
            "unique_products": int(preds_df["product_id"].nunique()) if not preds_df.empty else 0,
        },
        "transactions": {
            "total": int(len(trans_df)),
            "unique_customers": int(trans_df["customer_id"].nunique()) if not trans_df.empty else 0,
            "unique_products": int(trans_df["product_id"].nunique()) if not trans_df.empty else 0,
        } if not trans_df.empty else None
    }
    
    _cache["stats"] = stats
    return stats

def _process_question(question: str) -> str:
    """
    Procesa la pregunta del usuario y genera una respuesta.
    """
    question_lower = question.lower()
    
    # Cargar datos
    preds_df = _load_predictions()
    trans_df = _load_transactions()
    stats = _get_statistics()
    
    # Pregunta: ¿Cuántos clientes únicos?
    if re.search(r'cu[aá]ntos?\s+clientes?\s+[úu]nicos?', question_lower):
        if not preds_df.empty:
            n_customers = stats["predictions"]["unique_customers"]
            response = f"Hay **{n_customers:,}** clientes únicos en el dataset de predicciones."
            
            if stats["transactions"]:
                n_trans_customers = stats["transactions"]["unique_customers"]
                response += f"\n\nEn el dataset de transacciones hay **{n_trans_customers:,}** clientes únicos."
            
            return response
        else:
            return "No hay datos de predicciones disponibles."
    
    # Pregunta: ¿Cuántos productos únicos?
    if re.search(r'cu[aá]ntos?\s+productos?\s+[úu]nicos?', question_lower):
        if not preds_df.empty:
            n_products = stats["predictions"]["unique_products"]
            response = f"Hay **{n_products:,}** productos únicos en el dataset de predicciones."
            
            if stats["transactions"]:
                n_trans_products = stats["transactions"]["unique_products"]
                response += f"\n\nEn el dataset de transacciones hay **{n_trans_products:,}** productos únicos."
            
            return response
        else:
            return "No hay datos de predicciones disponibles."
    
    # Pregunta: Transacciones de un cliente específico
    customer_match = re.search(r'cliente\s+(\w+)', question_lower)
    if customer_match and any(word in question_lower for word in ['transacciones', 'transacción', 'compras', 'realizado']):
        customer_id = customer_match.group(1)
        
        if not trans_df.empty:
            customer_trans = trans_df[trans_df["customer_id"].astype(str) == customer_id]
            n_trans = len(customer_trans)
            
            if n_trans > 0:
                response = f"El cliente **{customer_id}** ha realizado **{n_trans:,}** transacciones."
                
                if "week" in customer_trans.columns:
                    weeks = customer_trans["week"].unique()
                    response += f"\n\nEstas transacciones abarcan **{len(weeks)}** semanas diferentes."
                
                return response
            else:
                return f"No se encontraron transacciones para el cliente **{customer_id}**."
        else:
            if not preds_df.empty:
                customer_preds = preds_df[preds_df["customer_id"].astype(str) == customer_id]
                n_preds = len(customer_preds)
                
                if n_preds > 0:
                    return f"El cliente **{customer_id}** tiene **{n_preds:,}** predicciones en el sistema. (No hay datos de transacciones históricas disponibles)"
                else:
                    return f"No se encontró información para el cliente **{customer_id}**."
            
            return "No hay datos de transacciones disponibles."
    
    # Pregunta: Total de transacciones
    if re.search(r'cu[aá]ntas?\s+transacciones?', question_lower):
        if not trans_df.empty:
            n_trans = len(trans_df)
            response = f"Hay un total de **{n_trans:,}** transacciones en el dataset."
            return response
        else:
            return "No hay datos de transacciones disponibles."
    
    # Pregunta: Total de predicciones
    if re.search(r'cu[aá]ntas?\s+predicciones?', question_lower):
        if not preds_df.empty:
            n_preds = len(preds_df)
            response = f"Hay un total de **{n_preds:,}** predicciones en el dataset."
            return response
        else:
            return "No hay datos de predicciones disponibles."
    
    # Pregunta: Estadísticas generales
    if re.search(r'estad[ií]sticas?|resumen|overview', question_lower):
        response = "### 📊 Estadísticas del Sistema\n\n"
        
        if stats["predictions"]["total"] > 0:
            response += f"**Predicciones:**\n"
            response += f"- Total de registros: {stats['predictions']['total']:,}\n"
            response += f"- Clientes únicos: {stats['predictions']['unique_customers']:,}\n"
            response += f"- Productos únicos: {stats['predictions']['unique_products']:,}\n\n"
        
        if stats["transactions"]:
            response += f"**Transacciones:**\n"
            response += f"- Total de registros: {stats['transactions']['total']:,}\n"
            response += f"- Clientes únicos: {stats['transactions']['unique_customers']:,}\n"
            response += f"- Productos únicos: {stats['transactions']['unique_products']:,}\n"
        
        return response
    
    # Respuesta por defecto
    return """No entendí tu pregunta. Puedo ayudarte con información como:

- ¿Cuántos clientes únicos hay en el dataset?
- ¿Cuántos productos únicos existen?
- ¿Cuántas transacciones ha realizado el cliente X?
- ¿Cuántas transacciones/predicciones hay en total?
- Muestra las estadísticas del sistema

Intenta reformular tu pregunta."""


@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok", "service": APP_NAME}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Endpoint principal del chatbot.
    Procesa la pregunta del usuario y retorna una respuesta.
    """
    try:
        response_text = _process_question(request.message)
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando pregunta: {str(e)}")

@app.get("/statistics")
def get_stats():
    """Obtiene estadísticas del sistema"""
    return _get_statistics()

@app.post("/reset_cache")
def reset_cache():
    """Limpia el cache de datos"""
    global _cache
    _cache = {"predictions": None, "transactions": None, "stats": None}
    return {"status": "cache cleared"}
=======
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
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b
