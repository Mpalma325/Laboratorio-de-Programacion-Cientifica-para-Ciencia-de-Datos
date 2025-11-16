import os, json, requests
import gradio as gr
import pandas as pd

BACKEND_URL = os.getenv("BACKEND_URL", "http://recsys-backend:8100")

HELP = """
# 🧠 Sistema de Recomendación (Bonus)
Ingresa un `customer_id` y obtén **5 recomendaciones** basadas en co-ocurrencia + popularidad.
"""

def _post(url, payload):
    try:
        r = requests.post(url, data=json.dumps(payload), headers={"Content-Type":"application/json"}, timeout=15)
        if r.status_code >= 400:
            return None, f"{r.status_code}: {r.text}"
        return r.json(), None
    except Exception as e:
        return None, str(e)

def rec(customer_id, k):
    data, err = _post(f"{BACKEND_URL}/recommend", {"customer_id": customer_id, "k": int(k)})
    if err:
        return f"❌ Error: {err}", None
    items = data.get("items", [])
    if not items:
        return "⚠️ Sin candidatos.", None
    df = pd.DataFrame(items)
    return f"✅ Recomendaciones para {data['customer_id']} (k={data['n_candidates']})", df

with gr.Blocks(title="Bonus Recsys") as demo:
    gr.Markdown(HELP)
    with gr.Row():
        cid = gr.Textbox(label="customer_id", placeholder="Ej: 12345")
        k = gr.Slider(1, 20, value=5, step=1, label="k")
    btn = gr.Button("Recomendar")
    status = gr.Markdown()
    table = gr.Dataframe(interactive=False)
    btn.click(rec, inputs=[cid, k], outputs=[status, table])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7861")))
