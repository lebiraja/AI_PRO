import gradio as gr
import requests
import google.generativeai as genai

# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "llama3.2"
GEMINI_API_KEY = "AIzaSyDtlItcSiiPnio7QKFy_oimOuzgLrAC9yI"

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

def chat_with_ollama(message, chat_history, model_name):
    """Chat with Ollama local model"""
    # Build prompt using chat history
    prompt = ""
    for user_msg, bot_msg in chat_history:
        prompt += f"You: {user_msg}\nBot: {bot_msg}\n"
    prompt += f"You: {message}\nBot:"

    try:
        response = requests.post(OLLAMA_API_URL, json={
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }, timeout=30)

        if response.status_code == 200:
            bot_reply = response.json()["response"].strip()
        else:
            bot_reply = f"⚠️ Error from Ollama: {response.text}"
    except Exception as e:
        bot_reply = f"❌ Could not connect to Ollama: {e}"

    chat_history.append((message, bot_reply))
    return chat_history, chat_history, ""

def chat_with_gemini(message, chat_history):
    """Chat with Gemini API"""
    try:
        # Build context from chat history
        context = ""
        for user_msg, bot_msg in chat_history[-3:]:  # Keep last 3 exchanges for context
            context += f"Human: {user_msg}\nAssistant: {bot_msg}\n"
        
        full_prompt = f"{context}Human: {message}\nAssistant:"
        
        response = gemini_model.generate_content(full_prompt)
        bot_reply = response.text.strip()
        
    except Exception as e:
        bot_reply = f"❌ Gemini API Error: {str(e)}"

    chat_history.append((message, bot_reply))
    return chat_history, chat_history, ""

def get_ollama_models():
    """Get available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models] if models else [DEFAULT_OLLAMA_MODEL]
    except:
        pass
    return [DEFAULT_OLLAMA_MODEL]

# ---------------- UI ---------------- #
with gr.Blocks(theme=gr.themes.Soft(), title="AI Chatbot") as demo:
    gr.HTML("""
    <div style="text-align: center; margin: 20px;">
        <h1 style="color: #2563eb;">🤖 AI Chatbot</h1>
        <p style="color: #64748b;">Choose between Ollama (Local) or Gemini (API)</p>
    </div>
    """)
    
    # Mode Selection
    with gr.Row():
        mode_selector = gr.Radio(
            choices=["🤖 Ollama (Local)", "🌟 Gemini (API)"],
            value="🤖 Ollama (Local)",
            label="Select AI Mode"
        )
        
        ollama_model = gr.Dropdown(
            choices=get_ollama_models(),
            value=DEFAULT_OLLAMA_MODEL,
            label="Ollama Model",
            visible=True
        )
    
    # Status
    status = gr.Markdown("**Status:** 🤖 Ollama mode selected")
    
    # Chat Interface
    chatbot = gr.Chatbot(label="Chat History", height=400)
    
    # Input
    with gr.Row():
        user_input = gr.Textbox(
            placeholder="Type your message...",
            label="Your Message",
            scale=4
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)
    
    clear_btn = gr.Button("Clear Chat")
    
    # State
    chat_state = gr.State([])
    
    # Functions
    def update_status(mode):
        if mode == "🤖 Ollama (Local)":
            return "**Status:** 🤖 Ollama mode selected", gr.update(visible=True)
        else:
            return "**Status:** 🌟 Gemini mode selected", gr.update(visible=False)
    
    def process_chat(message, history, mode, model):
        if not message.strip():
            return history, history, ""
        
        if mode == "🤖 Ollama (Local)":
            return chat_with_ollama(message, history, model)
        else:
            return chat_with_gemini(message, history)
    
    # Events
    mode_selector.change(
        update_status,
        inputs=[mode_selector],
        outputs=[status, ollama_model]
    )
    
    user_input.submit(
        process_chat,
        inputs=[user_input, chat_state, mode_selector, ollama_model],
        outputs=[chatbot, chat_state, user_input]
    )
    
    send_btn.click(
        process_chat,
        inputs=[user_input, chat_state, mode_selector, ollama_model],
        outputs=[chatbot, chat_state, user_input]
    )
    
    clear_btn.click(
        lambda: ([], []),
        outputs=[chatbot, chat_state]
    )
    
    gr.HTML("""
    <div style="text-align: center; margin-top: 20px; color: #6b7280;">
        Made with ❤️ by Lebi | Powered by Ollama + Gemini + Gradio
    </div>
    """)

# Run the application
if __name__ == "__main__":
    print("🚀 Starting AI Chatbot...")
    demo.launch(share=True)
