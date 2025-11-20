import os
import json
import requests
import gradio as gr
import pandas as pd

BACKEND_URL = os.getenv("BACKEND_URL", "http://recsys-backend:8001")

HELP_TEXT = """
# 🎯 Sistema de Recomendación - SodAI Drinks

Este sistema genera **5 recomendaciones personalizadas** de productos para cualquier cliente basándose en predicciones del modelo.

## 📋 Cómo usar:

1. **Ingresa un Customer ID** en el campo de texto
2. Presiona el botón **"Generar Recomendaciones"**
3. El sistema te mostrará:
   - Los 5 productos con mayor probabilidad de compra
   - Score de cada producto (0-1)
   - Ranking de recomendaciones

### 💡 Otros:
- Puedes explorar diferentes clientes usando la pestaña "Explorar Clientes"
- Revisa las estadísticas del sistema en "Estadísticas"
- Los productos se ordenan por score descendente.
---
"""

def _safe_get_json(url):
    """Realiza petición GET de forma segura"""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

def get_recommendations(customer_id, top_n=5):
    """Obtiene recomendaciones para un cliente"""
    if customer_id is None:
        customer_id = ""
    customer_id = str(customer_id).strip()

    if not customer_id:
        return "⚠️ Por favor ingresa un Customer ID", None, ""
    
    data, err = _safe_get_json(f"{BACKEND_URL}/recommend/{customer_id}?top_n={top_n}")
    
    if err:
        return f"❌ Error: {err}", None, ""
    
    recommendations = data.get("recommendations", [])
    
    if not recommendations:
        return "⚠️ No se encontraron recomendaciones para este cliente", None, ""
    

    df = pd.DataFrame([
        {
            "Rank": rec["rank"],
            "Product ID": rec["product_id"],
            "Score": f"{rec['score']:.4f}",
        }
        for rec in recommendations
    ])
    
    
    week = data.get("week", "N/A")
    total = data.get("total_products", 0)
    
    summary = f"""
### ✅ Recomendaciones Generadas
- **Customer ID:** {customer_id}
- **Semana de predicción:** {week}
- **Total de productos analizados:** {total}
- **Top recomendaciones mostradas:** {len(recommendations)}
    """
    

    json_output = json.dumps(data, indent=2, ensure_ascii=False)
    
    return summary, df, json_output

def get_customer_info(customer_id):
    """Obtiene información de un cliente"""
    if customer_id is None:
        customer_id = ""
    customer_id = str(customer_id).strip()

    if not customer_id:
        return "⚠️ Por favor ingresa un Customer ID"
    
    data, err = _safe_get_json(f"{BACKEND_URL}/customer/{customer_id}")
    
    if err:
        return f"❌ Error: {err}"
    
    if not data.get("exists"):
        return f"⚠️ El cliente {customer_id} no existe en las predicciones"
    
    return f"""
### 📊 Información del Cliente
- **Customer ID:** {data['customer_id']}
- **Existe en sistema:** ✅ Sí
- **Total de predicciones:** {data['total_predictions']}
- **Semana:** {data['week']}
    """

def list_sample_customers():
    """Lista clientes de ejemplo"""
    data, err = _safe_get_json(f"{BACKEND_URL}/customers")
    
    if err:
        return f"❌ Error: {err}", None
    
    customers = data.get("customers", [])
    total = data.get("total_customers", 0)
    
    summary = f"### 👥 Total de clientes en sistema: {total}\n\n"
    summary += f"Mostrando primeros {len(customers)} clientes:"
    
    
    df = pd.DataFrame({
        "Customer ID": customers
    })
    
    return summary, df

def get_statistics():
    """Obtiene estadísticas del sistema"""
    data, err = _safe_get_json(f"{BACKEND_URL}/statistics")
    
    if err:
        return f"❌ Error: {err}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)

def check_health():
    """Verifica estado del backend"""
    data, err = _safe_get_json(f"{BACKEND_URL}/health")
    
    if err:
        return f"❌ Error: {err}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


with gr.Blocks(title="SodAI RecSys", theme=gr.themes.Soft()) as demo:
    gr.Markdown(HELP_TEXT)
    
    with gr.Tabs():
        
        with gr.Tab("🎯 Recomendaciones"):
            gr.Markdown("### Genera recomendaciones personalizadas para un cliente")
            
            with gr.Row():
                customer_input = gr.Textbox(
                    label="Customer ID",
                    placeholder="Ejemplo: 12345",
                    info="Ingresa el identificador del cliente"
                )
                top_n_slider = gr.Slider(
                    label="Número de recomendaciones",
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    info="¿Cuántas recomendaciones quieres ver?"
                )
            
            recommend_btn = gr.Button("🚀 Generar Recomendaciones", variant="primary", size="lg")
            
            status_output = gr.Markdown()
            recommendations_table = gr.Dataframe(
                headers=["Rank", "Product ID", "Score"],
                label="Productos Recomendados"
            )
            
            with gr.Accordion("Ver JSON completo", open=False):
                json_output = gr.Code(language="json", label="Respuesta JSON")
            
            recommend_btn.click(
                get_recommendations,
                inputs=[customer_input, top_n_slider],
                outputs=[status_output, recommendations_table, json_output]
            )
        

        with gr.Tab("👥 Explorar Clientes"):
            gr.Markdown("### Explora los clientes disponibles en el sistema")
            
            with gr.Row():
                customer_search = gr.Textbox(
                    label="Buscar Customer ID",
                    placeholder="Ejemplo: 12345"
                )
                search_btn = gr.Button("🔍 Buscar", variant="secondary")
            
            customer_info_output = gr.Markdown()
            
            search_btn.click(
                get_customer_info,
                inputs=[customer_search],
                outputs=[customer_info_output]
            )
            
            gr.Markdown("---")
            gr.Markdown("### Lista de clientes disponibles")
            
            list_customers_btn = gr.Button("📋 Ver Clientes", variant="secondary")
            
            customers_summary = gr.Markdown()
            customers_table = gr.Dataframe(
                headers=["Customer ID"],
                label="Clientes en Sistema"
            )
            
            list_customers_btn.click(
                list_sample_customers,
                outputs=[customers_summary, customers_table]
            )
        
        
        with gr.Tab("📊 Estadísticas"):
            gr.Markdown("### Estadísticas generales del sistema de recomendación")
            
            with gr.Row():
                with gr.Column():
                    stats_btn = gr.Button("📈 Ver Estadísticas", variant="secondary")
                    stats_output = gr.Code(language="json", label="Estadísticas del Sistema")
                    stats_btn.click(get_statistics, outputs=[stats_output])
                
                with gr.Column():
                    health_btn = gr.Button("🏥 Health Check", variant="secondary")
                    health_output = gr.Code(language="json", label="Estado del Backend")
                    health_btn.click(check_health, outputs=[health_output])
    
    gr.Markdown("---")
    gr.Markdown("**SodAI Drinks RecSys** - Sistema de Recomendación v1.0 | Gradio + FastAPI")

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7861")),
        share=False
    )
