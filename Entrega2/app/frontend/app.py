import os
import json
import requests
import gradio as gr
import pandas as pd


BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

HELP_TEXT = """
<<<<<<< HEAD
# 🥤 Recomendador de SodAI Drinks  
Esta aplicación permite consultar el modelo desplegado mediante el pipeline de Airflow.

### 📋 Instrucciones de Uso:

#### 1️⃣ Top-K por cliente
- Ingresa un **customer_id** (identificador del cliente)
- Selecciona el número de productos a recomendar (**top_k**)
- Opcionalmente, filtra por un **score mínimo** (Probabilidad/Confianza de la predicción. 0-1)
- Presiona "Consultar Top-K" para obtener las mejores recomendaciones

#### 2️⃣ Cliente + Producto
- Ingresa un **customer_id** y un **product_id**
- Consulta la predicción específica para ese par
- Presiona "Consultar Par" para ver el resultado

#### 3️⃣ Estado del Sistema
- Verifica el estado del backend con el botón "Ver /health"
- Consulta los metadatos de las predicciones con "Ver /metadata"
- Revisa la semana de las predicciones y cantidad de registros disponibles

"""

def _safe_get_json(url):
    """Realiza una petición GET al backend de forma segura"""
=======
#  Recomendador de SodAI Drinks  
Esta aplicación permite consultar el modelo  desplegado mediante el pipeline de Airflow.

### Uso:
1. **Top-K por cliente:** ingresa un `customer_id`, selecciona `top_k` a mostrar y opcionalmente un `min_score`.
2. **Cliente + Producto:** consulta una predicción específica.
3. **Estado:** Se revisa el estado del servicio backend y las últimas predicciones disponibles.
"""

def _safe_get_json(url):
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json(), None
<<<<<<< HEAD
    except requests.exceptions.RequestException as e:
        return None, f"Error de conexión: {str(e)}"
    except Exception as e:
        return None, f"Error inesperado: {str(e)}"

def _safe_post_json(url, payload):
    """Realiza una petición POST al backend de forma segura"""
    try:
        r = requests.post(
            url, 
            json=payload,
            headers={"Content-Type": "application/json"}, 
            timeout=15
        )
        if r.status_code >= 400:
            return None, f"Error {r.status_code}: {r.text}"
        return r.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"Error de conexión: {str(e)}"
    except Exception as e:
        return None, f"Error inesperado: {str(e)}"

def check_health():
    """Verifica el estado del backend"""
    data, err = _safe_get_json(f"{BACKEND_URL}/health")
    if err:
        return f"❌ Error: {err}"
    return json.dumps(data, indent=2, ensure_ascii=False)

def check_metadata():
    """Obtiene los metadatos de las predicciones"""
    data, err = _safe_get_json(f"{BACKEND_URL}/metadata")
    if err:
        return f"❌ Error: {err}"
    return json.dumps(data, indent=2, ensure_ascii=False)

def predict_topk(customer_id, top_k, min_score):
    """Obtiene las top-K predicciones para un cliente"""
    if not customer_id:
        return "⚠️ Por favor ingresa un customer_id", None
    
    payload = {"customer_id": customer_id, "top_k": int(top_k)}
    if min_score is not None and min_score > 0:
        payload["min_score"] = float(min_score)
    
    data, err = _safe_post_json(f"{BACKEND_URL}/predict", payload)
    if err:
        return f"❌ Error: {err}", None
    
    items = data.get("items", [])
    if not items:
        return "⚠️ Sin resultados para este cliente", None
    
    df = pd.DataFrame(items)[["customer_id", "product_id", "week", "score", "pred_compra"]]
    status_msg = f"✅ Semana: {data.get('week')} | Resultados encontrados: {data.get('n_returned')}"
    return status_msg, df

def predict_pair(customer_id, product_id):
    """Obtiene la predicción para un par cliente-producto específico"""
    if not customer_id or not product_id:
        return "⚠️ Por favor ingresa tanto customer_id como product_id", None
    
    payload = {"customer_id": customer_id, "product_id": product_id}
    data, err = _safe_post_json(f"{BACKEND_URL}/predict_pair", payload)
    if err:
        return f"❌ Error: {err}", None
    
    df = pd.DataFrame([data])[["customer_id", "product_id", "week", "score", "pred_compra"]]
    return "✅ Predicción encontrada", df

# Crear la interfaz de Gradio
with gr.Blocks(title="SodAI Drinks Recomendador", theme=gr.themes.Soft()) as demo:
    gr.Markdown(HELP_TEXT)
    
    with gr.Tabs():
        # TAB 1: Top-K por Cliente
        with gr.Tab("📊 Top-K Cliente"):
            gr.Markdown("### Obtén las mejores recomendaciones para un cliente")
            with gr.Row():
                customer_id_topk = gr.Textbox(
                    label="Customer ID", 
                    placeholder="Ejemplo: 12345",
                    info="Identificador único del cliente"
                )
                topk = gr.Slider(
                    label="Top K", 
                    minimum=1, 
                    maximum=50, 
                    value=10, 
                    step=1,
                    info="Cantidad de productos a recomendar"
                )
                min_score = gr.Number(
                    label="Score mínimo (opcional)", 
                    value=None, 
                    minimum=0.0,
                    maximum=1.0,
                    precision=3,
                    info="Filtrar productos por score mínimo"
                )
            
            btn_topk = gr.Button("🔍 Consultar Top-K", variant="primary")
            status_topk = gr.Markdown()
            table_topk = gr.Dataframe(
                headers=["customer_id", "product_id", "week", "score", "pred_compra"],
                label="Resultados",
                interactive=False
            )
            
            btn_topk.click(
                predict_topk, 
                inputs=[customer_id_topk, topk, min_score], 
                outputs=[status_topk, table_topk]
            )
        
        # TAB 2: Cliente + Producto
        with gr.Tab("🔍 Cliente + Producto"):
            gr.Markdown("### Consulta una predicción específica para un par cliente-producto")
            with gr.Row():
                customer_id_pair = gr.Textbox(
                    label="Customer ID", 
                    placeholder="Ejemplo: 12345",
                    info="Identificador único del cliente"
                )
                product_id_pair = gr.Textbox(
                    label="Product ID", 
                    placeholder="Ejemplo: A-001",
                    info="Identificador único del producto"
                )
            
            btn_pair = gr.Button("🔍 Consultar Par", variant="primary")
            status_pair = gr.Markdown()
            table_pair = gr.Dataframe(
                headers=["customer_id", "product_id", "week", "score", "pred_compra"],
                label="Resultado",
                interactive=False
            )
            
            btn_pair.click(
                predict_pair, 
                inputs=[customer_id_pair, product_id_pair], 
                outputs=[status_pair, table_pair]
            )
        
        # TAB 3: Estado del Sistema
        with gr.Tab("⚙️ Estado"):
            gr.Markdown("### Verifica el estado del backend y los metadatos")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Health Check")
                    btn_health = gr.Button("🔄 Ver /health", variant="secondary")
                    health_out = gr.Code(
                        label="Respuesta de /health", 
                        language="json",
                        lines=10
                    )
                    btn_health.click(check_health, outputs=health_out)
                
                with gr.Column():
                    gr.Markdown("#### Metadata")
                    btn_meta = gr.Button("🔄 Ver /metadata", variant="secondary")
                    meta_out = gr.Code(
                        label="Respuesta de /metadata", 
                        language="json",
                        lines=10
                    )
                    btn_meta.click(check_metadata, outputs=meta_out)
    
    gr.Markdown("---")
    gr.Markdown("**SodAI Drinks** - Sistema de Recomendación | Desarrollado con Gradio + FastAPI")

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=int(os.getenv("PORT", "7860")),
        share=False
    )
=======
    except Exception as e:
        return None, str(e)

def _safe_post_json(url, payload):
    try:
        r = requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=15)
        if r.status_code >= 400:
            return None, f"{r.status_code}: {r.text}"
        return r.json(), None
    except Exception as e:
        return None, str(e)

def check_health():
    data, err = _safe_get_json(f"{BACKEND_URL}/health")
    if err:
        return f" Error: {err}"
    return json.dumps(data, indent=2, ensure_ascii=False)

def check_metadata():
    data, err = _safe_get_json(f"{BACKEND_URL}/metadata")
    if err:
        return f" Error: {err}"
    return json.dumps(data, indent=2, ensure_ascii=False)

def predict_topk(customer_id, top_k, min_score):
    payload = {"customer_id": customer_id, "top_k": int(top_k)}
    if min_score is not None:
        payload["min_score"] = float(min_score)
    data, err = _safe_post_json(f"{BACKEND_URL}/predict", payload)
    if err:
        return f" Error: {err}", None
    items = data.get("items", [])
    if not items:
        return " Sin resultados", None
    df = pd.DataFrame(items)[["customer_id", "product_id", "week", "score", "pred_compra"]]
    return f" Semana: {data.get('week')} | Resultados: {data.get('n_returned')}", df

def predict_pair(customer_id, product_id):
    payload = {"customer_id": customer_id, "product_id": product_id}
    data, err = _safe_post_json(f"{BACKEND_URL}/predict_pair", payload)
    if err:
        return f" Error: {err}", None
    df = pd.DataFrame([data])[["customer_id", "product_id", "week", "score", "pred_compra"]]
    return  "" , df

with gr.Blocks(title="SodAI Drinks Recomendador") as demo:
    gr.Markdown(HELP_TEXT)

    with gr.Tabs():
        with gr.Tab("Top-K cliente"):
            with gr.Row():
                customer_id_topk = gr.Textbox(label="customer_id", placeholder="Ej: 12345")
                topk = gr.Slider(label="top_k", minimum=1, maximum=50, value=10, step=1)
                min_score = gr.Number(label="min_score (opcional, 0-1)", value=None, precision=3)
            btn_topk = gr.Button("Consulta Top-K")
            status_topk = gr.Markdown()
            table_topk = gr.Dataframe(headers=["customer_id","product_id","week","score","pred_compra"], interactive=False)
            btn_topk.click(predict_topk, inputs=[customer_id_topk, topk, min_score], outputs=[status_topk, table_topk])

        with gr.Tab(" Cliente + Producto"):
            with gr.Row():
                customer_id_pair = gr.Textbox(label="customer_id", placeholder="Ej: 12345")
                product_id_pair = gr.Textbox(label="product_id", placeholder="Ej: A-001")
            btn_pair = gr.Button("Consultar Par")
            status_pair = gr.Markdown()
            table_pair = gr.Dataframe(headers=["customer_id","product_id","week","score","pred_compra"], interactive=False)
            btn_pair.click(predict_pair, inputs=[customer_id_pair, product_id_pair], outputs=[status_pair, table_pair])

        with gr.Tab("Estado"):
            btn_health = gr.Button("Ver /health")
            health_out = gr.Code(label="health", language="json")
            btn_meta = gr.Button("Ver /metadata")
            meta_out = gr.Code(label="metadata", language="json")
            btn_health.click(lambda: check_health(), outputs=health_out)
            btn_meta.click(lambda: check_metadata(), outputs=meta_out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b
