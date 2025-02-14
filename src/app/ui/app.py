import gradio as gr
from app.ui.interface import create_app
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Launch the Gradio interface."""
    interface = create_app()
    interface.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", 7860)),
        share=False
    )

if __name__ == "__main__":
    main() 