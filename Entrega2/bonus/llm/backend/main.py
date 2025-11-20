from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import glob
import pandas as pd
import json
from typing import Optional

APP_NAME = "SodAI LLM Chatbot Backend"
DESCRIPTION = "Chatbot conversacional que responde preguntas sobre los datos"

DATA_DIR = os.getenv("DATA_DIR", "/mnt/data")

app = FastAPI(title=APP_NAME, description=DESCRIPTION, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    use_context: bool = True


class ChatResponse(BaseModel):
    answer: str
    context_used: Optional[dict] = None
    data_summary: Optional[dict] = None


def _load_transactions() -> pd.DataFrame:
    """Carga las transacciones desde raw/transacciones.parquet."""
    try:
        # Primero intenta cargar desde raw (datos originales)
        trans_path = os.path.join(DATA_DIR, "raw", "transacciones.parquet")
        print(f"Buscando transacciones en: {trans_path}")
        
        if os.path.exists(trans_path):
            df = pd.read_parquet(trans_path)
            print(f"Transacciones cargadas desde raw: {len(df)} registros")
            print(f"Columnas: {df.columns.tolist()}")
            print(f"Tipo de customer_id: {df['customer_id'].dtype if 'customer_id' in df.columns else 'N/A'}")
            print(f"Ejemplo de customer_ids: {df['customer_id'].head().tolist() if 'customer_id' in df.columns else 'N/A'}")
            
            # NO convertir customer_id a string, dejarlo como int
            if "product_id" in df.columns:
                df["product_id"] = df["product_id"].astype(str)
            return df
        
        # Si no existe en raw, busca en processed
        trans_dir = os.path.join(DATA_DIR, "processed")
        print(f"Buscando en processed: {trans_dir}")
        
        if os.path.exists(trans_dir):
            files = sorted(
                glob.glob(os.path.join(trans_dir, "*transac*.parquet")),
                key=os.path.getmtime,
                reverse=True,
            )
            print(f"Archivos encontrados: {files}")
            
            if files:
                df = pd.read_parquet(files[0])
                print(f"Transacciones cargadas: {len(df)} registros")
                print(f"Columnas: {df.columns.tolist()}")
                
                # NO convertir customer_id a string, dejarlo como int
                if "product_id" in df.columns:
                    df["product_id"] = df["product_id"].astype(str)
                return df
                
    except Exception as e:
        print(f"Error loading transactions: {e}")
        import traceback
        traceback.print_exc()
    return pd.DataFrame()


def _load_predictions() -> pd.DataFrame:
    """Carga las predicciones más recientes."""
    try:
        preds_dir = os.path.join(DATA_DIR, "predictions")
        if not os.path.exists(preds_dir):
            print(f"Directorio de predicciones no existe: {preds_dir}")
            return pd.DataFrame()
            
        files = sorted(
            glob.glob(os.path.join(preds_dir, "*.parquet")),
            key=os.path.getmtime,
            reverse=True,
        )
        if files:
            df = pd.read_parquet(files[0])
            if "customer_id" in df.columns:
                df["customer_id"] = df["customer_id"].astype(str)
            if "product_id" in df.columns:
                df["product_id"] = df["product_id"].astype(str)
            return df
    except Exception as e:
        print(f"Error loading predictions: {e}")
    return pd.DataFrame()


def _load_products() -> pd.DataFrame:
    """Carga el catálogo de productos."""
    try:
        products_path = os.path.join(DATA_DIR, "products", "products.parquet")
        if os.path.exists(products_path):
            df = pd.read_parquet(products_path)
            if "product_id" in df.columns:
                df["product_id"] = df["product_id"].astype(str)
            return df
    except Exception as e:
        print(f"Error loading products: {e}")
    return pd.DataFrame()


def _get_data_summary() -> dict:
    """Obtiene un resumen de todos los datos disponibles."""
    transactions_df = _load_transactions()
    predictions_df = _load_predictions()
    products_df = _load_products()
    
    summary = {
        "transactions": {
            "total_records": len(transactions_df),
            "unique_customers": int(transactions_df["customer_id"].nunique()) if "customer_id" in transactions_df.columns else 0,
            "unique_products": int(transactions_df["product_id"].nunique()) if "product_id" in transactions_df.columns else 0,
            "date_range": {
                "min": str(transactions_df["purchase_date"].min()) if "purchase_date" in transactions_df.columns and len(transactions_df) > 0 else None,
                "max": str(transactions_df["purchase_date"].max()) if "purchase_date" in transactions_df.columns and len(transactions_df) > 0 else None,
            } if "purchase_date" in transactions_df.columns else None,
            "total_items": float(transactions_df["items"].sum()) if "items" in transactions_df.columns else 0,
        },
        "predictions": {
            "total_records": len(predictions_df),
            "unique_customers": int(predictions_df["customer_id"].nunique()) if "customer_id" in predictions_df.columns else 0,
            "unique_products": int(predictions_df["product_id"].nunique()) if "product_id" in predictions_df.columns else 0,
        },
        "products": {
            "total_products": len(products_df),
            "categories": int(products_df["category"].nunique()) if "category" in products_df.columns else 0,
        },
    }
    
    return summary


def _answer_with_data(question: str) -> dict:
    """Responde preguntas usando los datos directamente."""
    question_lower = question.lower()
    
    # Cargar datos
    transactions_df = _load_transactions()
    predictions_df = _load_predictions()
    products_df = _load_products()
    
    answer = ""
    context = {}
    
    # Preguntas sobre clientes únicos
    if "cuántos clientes" in question_lower or "clientes únicos" in question_lower:
        unique_customers = int(transactions_df["customer_id"].nunique()) if "customer_id" in transactions_df.columns else 0
        answer = f"Hay {unique_customers:,} clientes únicos en el dataset de transacciones."
        context["unique_customers"] = unique_customers
    
    # Preguntas sobre transacciones de un cliente específico
    elif "transacciones" in question_lower and "cliente" in question_lower:
        # Intentar extraer el customer_id de la pregunta
        words = question.split()
        customer_id = None
        for i, word in enumerate(words):
            if word.lower() in ["cliente", "customer"] and i + 1 < len(words):
                potential_id = words[i + 1].strip("?,.")
                # Intentar convertir a int para validar
                try:
                    customer_id = int(potential_id)
                    break
                except ValueError:
                    continue
        
        if customer_id is not None and "customer_id" in transactions_df.columns:
            customer_trans = transactions_df[transactions_df["customer_id"] == customer_id]
            count = len(customer_trans)
            total_items = customer_trans["items"].sum() if "items" in customer_trans.columns else 0
            unique_products = customer_trans["product_id"].nunique() if "product_id" in customer_trans.columns else 0
            answer = f"El cliente {customer_id} ha realizado {count:,} transacciones, comprando un total de {total_items:,.0f} items en {unique_products:,} productos diferentes."
            context["customer_id"] = customer_id
            context["transactions_count"] = count
            context["total_items"] = float(total_items)
            context["unique_products"] = unique_products
        else:
            answer = "No pude identificar el ID del cliente en tu pregunta. Por favor, especifica el customer_id (número)."
    
    # Preguntas sobre productos únicos
    elif "cuántos productos" in question_lower or "productos únicos" in question_lower:
        unique_products_trans = int(transactions_df["product_id"].nunique()) if "product_id" in transactions_df.columns else 0
        total_products = len(products_df)
        answer = f"Hay {unique_products_trans:,} productos únicos en las transacciones y {total_products:,} productos en el catálogo."
        context["unique_products_transactions"] = unique_products_trans
        context["total_products_catalog"] = total_products
    
    # Preguntas sobre items totales
    elif "items totales" in question_lower or "total de items" in question_lower or "ventas totales" in question_lower:
        total_items = transactions_df["items"].sum() if "items" in transactions_df.columns else 0
        answer = f"El total de items vendidos es de {total_items:,.0f} unidades."
        context["total_items"] = float(total_items)
    
    # Preguntas sobre predicciones
    elif "predicciones" in question_lower or "predicción" in question_lower:
        total_preds = len(predictions_df)
        unique_customers_pred = int(predictions_df["customer_id"].nunique()) if "customer_id" in predictions_df.columns else 0
        answer = f"Hay {total_preds:,} predicciones generadas para {unique_customers_pred:,} clientes únicos."
        context["total_predictions"] = total_preds
        context["unique_customers_predictions"] = unique_customers_pred
    
    # Pregunta general o no reconocida
    else:
        summary = _get_data_summary()
        answer = f"""No entendí exactamente tu pregunta, pero aquí hay un resumen de los datos disponibles:

📊 **Transacciones:**
- Total de registros: {summary['transactions']['total_records']:,}
- Clientes únicos: {summary['transactions']['unique_customers']:,}
- Productos únicos: {summary['transactions']['unique_products']:,}
- Total de items vendidos: {summary['transactions']['total_items']:,.0f}

🎯 **Predicciones:**
- Total de predicciones: {summary['predictions']['total_records']:,}
- Clientes con predicciones: {summary['predictions']['unique_customers']:,}

📦 **Productos:**
- Total en catálogo: {summary['products']['total_products']:,}
- Categorías: {summary['products']['categories']:,}

Puedes preguntarme cosas como:
- ¿Cuántos clientes únicos hay?
- ¿Cuántas transacciones ha realizado el cliente X?
- ¿Cuántos productos únicos hay?
- ¿Cuál es el total de items vendidos?
"""
        context = summary
    
    return {
        "answer": answer,
        "context": context,
    }


@app.get("/health")
def health():
    """Health check del servicio."""
    return {
        "status": "ok",
        "service": APP_NAME,
        "data_dir": DATA_DIR,
        "data_dir_exists": os.path.exists(DATA_DIR),
    }


@app.get("/data-summary")
def get_data_summary():
    """Obtiene un resumen de los datos disponibles."""
    return _get_data_summary()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Endpoint principal del chatbot.
    Responde preguntas sobre los datos.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="La pregunta no puede estar vacía",
        )
    
    try:
        result = _answer_with_data(request.question)
        
        data_summary = None
        if request.use_context:
            data_summary = _get_data_summary()
        
        return ChatResponse(
            answer=result["answer"],
            context_used=result.get("context"),
            data_summary=data_summary,
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la pregunta: {str(e)}",
        )


@app.get("/customers/{customer_id}/stats")
def get_customer_stats(customer_id: int):
    """Obtiene estadísticas detalladas de un cliente específico."""
    transactions_df = _load_transactions()
    
    if transactions_df.empty or "customer_id" not in transactions_df.columns:
        raise HTTPException(
            status_code=404,
            detail="No hay datos de transacciones disponibles",
        )
    
    print(f"=== DEBUG GET_CUSTOMER_STATS ===")
    print(f"Buscando cliente: {customer_id}, tipo: {type(customer_id)}")
    print(f"Tipo de customer_id en df: {transactions_df['customer_id'].dtype}")
    print(f"Total de registros en df: {len(transactions_df)}")
    print(f"Primeros 5 customer_ids: {transactions_df['customer_id'].head().tolist()}")
    print(f"Customer IDs únicos (primeros 10): {sorted(transactions_df['customer_id'].unique()[:10].tolist())}")
    
    # Intentar la búsqueda
    print(f"¿{customer_id} en valores? {customer_id in transactions_df['customer_id'].values}")
    
    # Convertir a numpy int32 para asegurar compatibilidad
    import numpy as np
    customer_id_np = np.int32(customer_id)
    print(f"Buscando como np.int32: {customer_id_np}")
    
    customer_data = transactions_df[transactions_df["customer_id"] == customer_id_np]
    print(f"Registros encontrados: {len(customer_data)}")
    
    if customer_data.empty:
        # Ver si existe con alguna variación
        mask = transactions_df["customer_id"] == customer_id
        print(f"Registros con mask directo: {mask.sum()}")
        
        # Buscar valores cercanos
        unique_customers = sorted(transactions_df["customer_id"].unique()[:20].tolist())
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron transacciones para el cliente {customer_id}. Primeros IDs válidos: {unique_customers}",
        )
    
    stats = {
        "customer_id": int(customer_id),
        "total_transactions": len(customer_data),
        "total_items": float(customer_data["items"].sum()) if "items" in customer_data.columns else 0,
        "unique_products": int(customer_data["product_id"].nunique()) if "product_id" in customer_data.columns else 0,
        "avg_items_per_order": float(customer_data["items"].mean()) if "items" in customer_data.columns else 0,
        "first_purchase": str(customer_data["purchase_date"].min()) if "purchase_date" in customer_data.columns else None,
        "last_purchase": str(customer_data["purchase_date"].max()) if "purchase_date" in customer_data.columns else None,
    }
    
    return stats


@app.get("/customers")
def list_customers(limit: int = 100):
    """Lista los customer IDs disponibles."""
    transactions_df = _load_transactions()
    
    if transactions_df.empty or "customer_id" not in transactions_df.columns:
        raise HTTPException(
            status_code=404,
            detail="No hay datos de transacciones disponibles",
        )
    
    # Obtener clientes únicos y ordenarlos
    customers = sorted(transactions_df["customer_id"].unique().tolist())
    total_customers = len(customers)
    
    # Limitar la cantidad de resultados
    customers_sample = customers[:limit]
    
    return {
        "total_customers": total_customers,
        "showing": len(customers_sample),
        "customers": customers_sample,
    }