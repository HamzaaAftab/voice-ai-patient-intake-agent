import gradio as gr
import uvicorn
from app.main import app

# Minimal Gradio interface for HF Space preview
with gr.Blocks(title="Valley Health Clinical Voice AI") as demo:
    gr.Markdown("# 🎙️ Valley Health System — Voice AI Clinical Intake")
    gr.Markdown("""
    Welcome to the **Valley Health Voice AI Clinical Intake** live service.
    
    ### 🔗 Live Portals & Endpoints:
    * **Executive Companion Dashboard:** [Open /dashboard](/dashboard)
    * **Interactive Swagger / OpenAPI Docs:** [Open /docs](/docs)
    * **Vapi Webhook Endpoint:** `/webhooks/vapi`
    * **System Health Probe:** [Open /health](/health)
    """)

# Mount Gradio onto the existing production FastAPI application
# All FastAPI endpoints (/dashboard, /docs, /webhooks/vapi, /api/v1/...) are fully preserved!
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

