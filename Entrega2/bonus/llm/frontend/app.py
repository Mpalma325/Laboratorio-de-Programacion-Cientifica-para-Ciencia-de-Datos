<<<<<<< HEAD
import os
import json
import requests
import gradio as gr
import time

BACKEND_URL = os.getenv("BACKEND_URL", "http://llm-backend:8002")

HELP_TEXT = """
# 💬 Chatbot Conversacional - SodAI Drinks

Este chatbot puede responder preguntas sobre los datos del sistema de forma conversacional.

## 🤖 Preguntas que puedo responder:

### Sobre clientes:
- *"¿Cuántos clientes únicos hay en el dataset?"*
- *"¿Cuántas transacciones ha realizado el cliente 12345?"*

### Sobre productos:
- *"¿Cuántos productos únicos se encuentran en los datos?"*

### Sobre transacciones:
- *"¿Cuántas transacciones hay en total?"*

### Estadísticas generales:
- *"Muestra las estadísticas del sistema"*
- *"Dame un resumen de los datos"*

---

## 💡 Consejos de uso:
1. Escribe tu pregunta de forma natural
2. El chatbot analizará tu consulta y buscará la información
3. Si no entiende la pregunta, te sugerirá formas alternativas de preguntar

"""

def wait_for_backend(max_retries=30, delay=2):
    """Espera a que el backend esté disponible"""
    print(f"Esperando conexión con backend en {BACKEND_URL}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ Backend conectado en intento {i+1}")
                return True
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(delay)
    print(f"❌ No se pudo conectar al backend después de {max_retries} intentos")
    return False

def _safe_post_json(url, payload):
    """Realiza petición POST de forma segura"""
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
    except requests.exceptions.ConnectionError:
        return None, "No se puede conectar al backend. Verifica que el servicio esté corriendo."
    except requests.exceptions.Timeout:
        return None, "Timeout: El backend tardó demasiado en responder."
    except Exception as e:
        return None, f"Error: {str(e)}"

def _safe_get_json(url):
    """Realiza petición GET de forma segura"""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "No se puede conectar al backend. Verifica que el servicio esté corriendo."
    except requests.exceptions.Timeout:
        return None, "Timeout: El backend tardó demasiado en responder."
    except Exception as e:
        return None, str(e)

def chat_response(message, history):
    """
    Función que procesa el mensaje del usuario y retorna la respuesta del chatbot.
    
    Args:
        message: Mensaje actual del usuario
        history: Historial de mensajes [[user_msg, bot_msg], ...]
    
    Returns:
        str: Respuesta del chatbot
    """
    if not message or message.strip() == "":
        return "Por favor escribe una pregunta."
    
    # Convertir historial al formato esperado por el backend
    chat_history = []
    if history:
        for user_msg, bot_msg in history:
            if user_msg:
                chat_history.append({"role": "user", "content": user_msg})
            if bot_msg:
                chat_history.append({"role": "assistant", "content": bot_msg})
    
    # Enviar mensaje al backend
    payload = {
        "message": message,
        "history": chat_history
    }
    
    data, err = _safe_post_json(f"{BACKEND_URL}/chat", payload)
    
    if err:
        return f"❌ Error de conexión: {err}"
    
    response = data.get("response", "No recibí respuesta del servidor.")
    
    return response

def get_statistics():
    """Obtiene estadísticas del sistema"""
    data, err = _safe_get_json(f"{BACKEND_URL}/statistics")
    if err:
        return f"Error: {err}"
    return json.dumps(data, indent=2, ensure_ascii=False)

def check_health():
    """Verifica estado del backend"""
    data, err = _safe_get_json(f"{BACKEND_URL}/health")
    if err:
        return f"Error: {err}"
    return json.dumps(data, indent=2, ensure_ascii=False)

# Ejemplos de preguntas
examples = [
    "¿Cuántos clientes únicos hay en el dataset?",
    "¿Cuántos productos únicos existen?",
    "¿Cuántas transacciones ha realizado el cliente 12345?",
    "Muestra las estadísticas del sistema",
    "¿Cuántas predicciones hay en total?"
]

# Esperar a que el backend esté disponible
wait_for_backend()

# Crear interfaz con Gradio
with gr.Blocks(title="SodAI LLM Chatbot", theme=gr.themes.Soft()) as demo:
    gr.Markdown(HELP_TEXT)
    
    with gr.Tabs():
        # TAB 1: Chat
        with gr.Tab("💬 Chat"):
            chatbot = gr.Chatbot(
                label="Conversación",
                height=400,
                show_label=True
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="Tu pregunta",
                    placeholder="Escribe tu pregunta aquí...",
                    lines=2,
                    scale=4
                )
                submit_btn = gr.Button("📤 Enviar", variant="primary", scale=1)
            
            # Botón para limpiar chat
            clear_btn = gr.Button("🗑️ Limpiar conversación", variant="secondary")
            
            # Ejemplos
            gr.Examples(
                examples=examples,
                inputs=msg_input,
                label="💡 Ejemplos de preguntas"
            )
            
            # Función para procesar y actualizar el chat
            def respond(message, chat_history):
                if not message:
                    return "", chat_history
                
                bot_response = chat_response(message, chat_history)
                chat_history.append((message, bot_response))
                return "", chat_history
            
            # Eventos
            submit_btn.click(
                respond,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            msg_input.submit(
                respond,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            clear_btn.click(
                lambda: None,
                outputs=[chatbot]
            )
        
        # TAB 2: Estadísticas
        with gr.Tab("📊 Estadísticas"):
            gr.Markdown("### Estadísticas del sistema")
            
            stats_btn = gr.Button("🔄 Obtener Estadísticas", variant="primary")
            stats_output = gr.Code(
                label="Estadísticas en JSON",
                language="json",
                lines=15
            )
            
            stats_btn.click(get_statistics, outputs=[stats_output])
        
        # TAB 3: Estado
        with gr.Tab("⚙️ Estado"):
            gr.Markdown("### Verifica el estado del backend")
            
            health_btn = gr.Button("🏥 Health Check", variant="primary")
            health_output = gr.Code(
                label="Estado del Backend",
                language="json",
                lines=10
            )
            
            health_btn.click(check_health, outputs=[health_output])
    
    gr.Markdown("---")
    gr.Markdown("**SodAI Drinks LLM Chatbot** v1.0 | Chatbot conversacional sobre datos del sistema")

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7862")),
        share=False
    )
=======
import os, requests, gradio as gr

BACKEND_URL = os.getenv("BACKEND_URL", "http://llm-backend:8200")

def chat_fn(message, history):
    try:
        r = requests.post(f"{BACKEND_URL}/ask", json={"message": message}, timeout=15)
        if r.status_code >= 400:
            return history + [[message, f"Error {r.status_code}: {r.text}"]]
        ans = r.json().get("answer", "")
        return history + [[message, ans]]
    except Exception as e:
        return history + [[message, f"❌ Error: {e}"]]

with gr.Blocks(title="Bonus LLM-lite") as demo:
    gr.Markdown("# Chat de preguntas sobre el dataset\nPregunta cosas como:\n- ¿Cuántos clientes únicos hay en el dataset?\n- ¿Cuántas transacciones ha realizado el cliente 123?\n- ¿Cuántos productos únicos se encuentran en los datos?\n")
    chat = gr.Chatbot(height=400)
    ipt = gr.Textbox(placeholder="Escribe tu pregunta...")
    btn = gr.Button("Enviar")
    def _click(msg, hist): 
        return chat_fn(msg, hist), ""
    btn.click(_click, inputs=[ipt, chat], outputs=[chat, ipt])
    ipt.submit(_click, inputs=[ipt, chat], outputs=[chat, ipt])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7862")))
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b
