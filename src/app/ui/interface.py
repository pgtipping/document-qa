"""Gradio interface for the Document Q&A application."""

import os
from typing import Any, Dict, Optional

import gradio as gr
from fastapi import UploadFile
from app.services.document import DocumentService
from app.services.llm import LLMService
from app.core.logger import error_logger


document_service = DocumentService()
llm_service = LLMService()


def handle_error(exception: Exception) -> str:
    """Handle and log errors, returning a user-friendly message.
    
    Args:
        exception: The exception that occurred
        
    Returns:
        A user-friendly error message
    """
    error_logger.log_error(
        exception,
        {"function": "process_file_and_question"},
        "interface"
    )
    return (
        f"An error occurred while processing your request: "
        f"{str(exception)}"
    )


async def process_file_and_question(
    file_obj: Optional[Any],
    question: str
) -> str:
    """Process uploaded file and answer question.
    
    Args:
        file_obj: The uploaded file object from Gradio
        question: The question to answer about the document
        
    Returns:
        The answer to the question or an error message
    """
    if not file_obj:
        return "Please upload a document first."
    if not question:
        return "Please ask a question."
    
    try:
        # Convert to UploadFile
        temp_path = file_obj.name
        upload_file = UploadFile(
            filename=os.path.basename(temp_path),
            file=open(temp_path, "rb")
        )
        
        # Save document
        document_id = await document_service.save_document(upload_file)
        
        # Get answer
        answer = await llm_service.get_answer(document_id, question)
        return answer
    except Exception as e:
        return handle_error(e)


async def create_app() -> Dict[str, str]:
    """Create and return the application instance.
    
    Returns:
        A dictionary containing the application status
    """
    return {"message": "App created"}


def demo_function(text: str) -> str:
    """Simple demo function.
    
    Args:
        text: The input text to echo
        
    Returns:
        The echoed text
    """
    return f"You said: {text}"


def launch_interface() -> None:
    """Launch the Gradio interface."""
    with gr.Blocks() as demo:
        gr.Markdown("# Document Q&A")
        with gr.Row():
            file_input = gr.File()
            text_input = gr.Textbox(placeholder="Ask a question...")
        text_output = gr.Textbox()
        gr.Interface(
            fn=process_file_and_question,
            inputs=[file_input, text_input],
            outputs=text_output
        )
    
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)

    demo = gr.Interface(
        fn=demo_function,
        inputs="text",
        outputs="text",
        title="Simple Demo"
    )
    
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860) 