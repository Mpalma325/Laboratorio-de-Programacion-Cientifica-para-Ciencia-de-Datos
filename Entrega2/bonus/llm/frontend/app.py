import os
import json
import requests
import gradio as gr

BACKEND_URL = os.getenv("BACKEND_URL", "http://llm-backend:8002")

WELCOME_MESSAGE = """
# 🤖 Chatbot Conversacional - SodAI Drinks

¡Hola! Soy tu asistente virtual para consultar datos sobre clientes, productos y transacciones.

## 💬 Ejemplos de preguntas que puedes hacer:

- ¿Cuántos clientes únicos hay en el dataset?
- ¿Cuántas transacciones ha realizado el cliente 12345?
- ¿Cuántos productos únicos se encuentran en los datos?
- ¿Cuántas predicciones hay?

---
"""


def _safe_request(method, url, **kwargs):
    """Realiza petición HTTP de forma segura."""
    try:
        print(f"Haciendo {method} a {url}")
        response = requests.request(method, url, timeout=10, **kwargs)
        print(f"Status: {response.status_code}")
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        print(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        return None, error_msg


def chat_with_bot(message, history):
    """Procesa mensaje del usuario y obtiene respuesta del bot."""
    if not message or not message.strip():
        return history, ""
    
    # Agregar mensaje del usuario al historial
    history = history or []
    history.append((message, None))
    
    # Hacer petición al backend
    payload = {
        "question": message,
        "use_context": True,
    }
    
    data, err = _safe_request("POST", f"{BACKEND_URL}/chat", json=payload)
    
    if err:
        bot_response = f" Error al procesar tu pregunta: {err}"
    else:
        bot_response = data.get("answer", "No obtuve respuesta del servidor.")
    
    # Actualizar historial con respuesta del bot
    history[-1] = (message, bot_response)
    
    return history, ""


def get_data_summary():
    """Obtiene resumen de datos disponibles."""
    data, err = _safe_request("GET", f"{BACKEND_URL}/data-summary")
    
    if err:
        return f"❌ Error: {err}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


def get_customer_stats(customer_id):
    """Obtiene estadísticas de un cliente específico."""
    if not customer_id or not customer_id.strip():
        return "⚠️ Por favor ingresa un Customer ID"
    
    customer_id = customer_id.strip()
    
    try:
        customer_id_int = int(customer_id)
    except ValueError:
        return "⚠️ El Customer ID debe ser un número entero"
    
    data, err = _safe_request("GET", f"{BACKEND_URL}/customers/{customer_id_int}/stats")
    
    if err:
        return f"❌ Error: {err}"
    
    return f"""
### 📊 Estadísticas del Cliente {data['customer_id']}

- **Total de transacciones:** {data['total_transactions']:,}
- **Total de items comprados:** {data['total_items']:,.0f} unidades
- **Productos únicos comprados:** {data['unique_products']:,}
- **Promedio de items por orden:** {data['avg_items_per_order']:,.2f}
- **Primera compra:** {data['first_purchase']}
- **Última compra:** {data['last_purchase']}
    """


def list_available_customers(limit):
    """Lista los customer IDs disponibles."""
    data, err = _safe_request("GET", f"{BACKEND_URL}/customers?limit={int(limit)}")
    
    if err:
        return f"❌ Error: {err}", ""
    
    total = data.get("total_customers", 0)
    showing = data.get("showing", 0)
    customers = data.get("customers", [])
    
    info = f"""
### 👥 Customer IDs Disponibles

- **Total de clientes en el sistema:** {total:,}
- **Mostrando:** {showing:,} clientes
    """
    

    customers_json = json.dumps(customers, indent=2, ensure_ascii=False)
    
    return info, customers_json


def check_health():
    """Verifica estado del backend."""
    data, err = _safe_request("GET", f"{BACKEND_URL}/health")
    
    if err:
        return f"❌ Error: {err}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


with gr.Blocks(title="SodAI LLM Chatbot") as demo:
    gr.Markdown(WELCOME_MESSAGE)
    
    with gr.Tabs():
        # TAB 1: Chat
        with gr.Tab("💬 Chat"):
            chatbot = gr.Chatbot(
                label="Conversación",
                height=500,
            )
            
            msg = gr.Textbox(
                label="Tu pregunta",
                placeholder="Escribe tu pregunta aquí...",
            )
            
            with gr.Row():
                submit_btn = gr.Button("📤 Enviar", variant="primary")
                clear_btn = gr.Button("🗑️ Limpiar Chat")
            
            
            gr.Examples(
                examples=[
                    ["¿Cuántos clientes únicos hay en el dataset?"],
                    ["¿Cuántos productos únicos se encuentran en los datos?"],
                    ["¿Cuántas predicciones hay?"],
                    ["¿Cuántas transacciones ha realizado el cliente 100001?"],
                ],
                inputs=msg,
            )
            
            # Eventos
            submit_btn.click(
                chat_with_bot,
                inputs=[msg, chatbot],
                outputs=[chatbot, msg],
            )
            
            msg.submit(
                chat_with_bot,
                inputs=[msg, chatbot],
                outputs=[chatbot, msg],
            )
            
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])
        
        # TAB 2: Consulta de Cliente
        with gr.Tab("👤 Consulta de Cliente"):
            gr.Markdown("### Obtén estadísticas detalladas de un cliente específico")
            
            with gr.Row():
                customer_input = gr.Textbox(
                    label="Customer ID",
                    placeholder="Ejemplo: 100001",
                )
                stats_btn = gr.Button("📊 Ver Estadísticas", variant="primary")
            
            stats_output = gr.Markdown()
            
            stats_btn.click(
                get_customer_stats,
                inputs=[customer_input],
                outputs=[stats_output],
            )
        
        # TAB 3: Resumen de Datos
        with gr.Tab("📈 Resumen de Datos"):
            gr.Markdown("### Visualiza un resumen general de todos los datos disponibles")
            
            with gr.Row():
                summary_btn = gr.Button("📊 Ver Resumen de Datos", variant="primary")
                health_btn = gr.Button("🏥 Health Check")
            
            with gr.Row():
                with gr.Column():
                    summary_output = gr.Code(language="json", label="Resumen de Datos")
                    summary_btn.click(get_data_summary, outputs=[summary_output])
                
                with gr.Column():
                    health_output = gr.Code(language="json", label="Estado del Backend")
                    health_btn.click(check_health, outputs=[health_output])
            
            gr.Markdown("---")
            gr.Markdown("### 👥 Lista de Customer IDs Disponibles")
            
            with gr.Row():
                limit_slider = gr.Slider(
                    minimum=10,
                    maximum=500,
                    value=100,
                    step=10,
                    label="Cantidad de clientes a mostrar"
                )
                list_customers_btn = gr.Button("📋 Ver Customer IDs")
            
            customers_info = gr.Markdown()
            customers_list = gr.Code(language="json", label="Customer IDs")
            
            list_customers_btn.click(
                list_available_customers,
                inputs=[limit_slider],
                outputs=[customers_info, customers_list],
            )
    
    gr.Markdown("---")
    gr.Markdown("**SodAI Drinks LLM Chatbot** - Sistema Conversacional v1.0")


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7862")),
    )