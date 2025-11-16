import os
import json
import requests
import gradio as gr
import pandas as pd

# URL del backend (por defecto el servicio 'backend' del docker-compose)
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

HELP_TEXT = """
# 🥤 SodAI Drinks — Interfaz de Recomendación

Esta aplicación permite consultar el **modelo de predicción** desplegado mediante el pipeline de Airflow.

### Cómo usar:
1. **Top-K por cliente:** ingresa un `customer_id`, selecciona `top_k` y (opcionalmente) un `min_score`.
2. **Cliente + Producto:** consulta una predicción específica.
3. **Estado:** revisa el estado del servicio backend y las últimas predicciones disponibles.
"""

def _safe_get_json(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json(), None
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
        return f"❌ Error: {err}"
    return json.dumps(data, indent=2, ensure_ascii=False)

def check_metadata():
    data, err = _safe_get_json(f"{BACKEND_URL}/metadata")
    if err:
        return f"❌ Error: {err}"
    return json.dumps(data, indent=2, ensure_ascii=False)

def predict_topk(customer_id, top_k, min_score):
    payload = {"customer_id": customer_id, "top_k": int(top_k)}
    if min_score is not None:
        payload["min_score"] = float(min_score)
    data, err = _safe_post_json(f"{BACKEND_URL}/predict", payload)
    if err:
        return f"❌ Error: {err}", None
    items = data.get("items", [])
    if not items:
        return "⚠️ Sin resultados.", None
    df = pd.DataFrame(items)[["customer_id", "product_id", "week", "score", "pred_compra"]]
    return f"✅ Semana: {data.get('week')} | Resultados: {data.get('n_returned')}", df

def predict_pair(customer_id, product_id):
    payload = {"customer_id": customer_id, "product_id": product_id}
    data, err = _safe_post_json(f"{BACKEND_URL}/predict_pair", payload)
    if err:
        return f"❌ Error: {err}", None
    df = pd.DataFrame([data])[["customer_id", "product_id", "week", "score", "pred_compra"]]
    return "✅ OK", df

with gr.Blocks(title="SodAI Drinks Recomendador") as demo:
    gr.Markdown(HELP_TEXT)

    with gr.Tabs():
        with gr.Tab("🔎 Top-K por cliente"):
            with gr.Row():
                customer_id_topk = gr.Textbox(label="customer_id", placeholder="Ej: 12345")
                topk = gr.Slider(label="top_k", minimum=1, maximum=50, value=10, step=1)
                min_score = gr.Number(label="min_score (opcional, 0-1)", value=None, precision=3)
            btn_topk = gr.Button("Consultar Top-K")
            status_topk = gr.Markdown()
            table_topk = gr.Dataframe(headers=["customer_id","product_id","week","score","pred_compra"], interactive=False)
            btn_topk.click(predict_topk, inputs=[customer_id_topk, topk, min_score], outputs=[status_topk, table_topk])

        with gr.Tab("🎯 Cliente + Producto"):
            with gr.Row():
                customer_id_pair = gr.Textbox(label="customer_id", placeholder="Ej: 12345")
                product_id_pair = gr.Textbox(label="product_id", placeholder="Ej: A-001")
            btn_pair = gr.Button("Consultar Par")
            status_pair = gr.Markdown()
            table_pair = gr.Dataframe(headers=["customer_id","product_id","week","score","pred_compra"], interactive=False)
            btn_pair.click(predict_pair, inputs=[customer_id_pair, product_id_pair], outputs=[status_pair, table_pair])

        with gr.Tab("🛠 Estado"):
            btn_health = gr.Button("Ver /health")
            health_out = gr.Code(label="health", language="json")
            btn_meta = gr.Button("Ver /metadata")
            meta_out = gr.Code(label="metadata", language="json")
            btn_health.click(lambda: check_health(), outputs=health_out)
            btn_meta.click(lambda: check_metadata(), outputs=meta_out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
