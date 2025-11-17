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
