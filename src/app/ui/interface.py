import gradio as gr
import httpx
from typing import Dict, List
import json
import os


class DocumentQAInterface:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.current_document_id = None

    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface."""
        with gr.Blocks(title="Document Q&A") as interface:
            with gr.Row():
                with gr.Column(scale=1):
                    # Sidebar
                    upload_button = gr.UploadButton(
                        "Upload Document",
                        file_types=["txt", "pdf", "doc", "docx"]
                    )
                    document_list = gr.Dropdown(
                        label="Select Document",
                        choices=[],
                        interactive=True
                    )
                    refresh_button = gr.Button("Refresh Documents")

                with gr.Column(scale=3):
                    # Main chat interface
                    chatbot = gr.Chatbot(
                        label="Chat History",
                        height=400
                    )
                    with gr.Row():
                        question_input = gr.Textbox(
                            label="Ask a question",
                            placeholder="Type your question here...",
                            scale=8
                        )
                        audio_input = gr.Audio(
                            source="microphone",
                            type="filepath",
                            label="Or speak your question",
                            scale=2
                        )
                    submit_button = gr.Button("Ask")

            # Event handlers
            upload_button.upload(
                self._handle_upload,
                inputs=[upload_button],
                outputs=[document_list]
            )
            
            refresh_button.click(
                self._refresh_documents,
                outputs=[document_list]
            )
            
            document_list.change(
                self._select_document,
                inputs=[document_list]
            )
            
            submit_button.click(
                self._handle_question,
                inputs=[question_input, chatbot],
                outputs=[question_input, chatbot]
            )
            
            audio_input.stop_recording(
                self._handle_audio_question,
                inputs=[audio_input, chatbot],
                outputs=[audio_input, chatbot]
            )

        return interface

    async def _handle_upload(self, file: gr.UploadData) -> List[str]:
        """Handle document upload."""
        try:
            files = {"file": (file.name, open(file.name, "rb"))}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/upload",
                    files=files
                )
                response.raise_for_status()
            return await self._refresh_documents()
        except Exception as e:
            raise gr.Error(f"Upload failed: {str(e)}")

    async def _refresh_documents(self) -> List[str]:
        """Refresh the document list."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/api/documents")
                response.raise_for_status()
                documents = response.json()["documents"]
                return [doc["filename"] for doc in documents]
        except Exception as e:
            raise gr.Error(f"Failed to fetch documents: {str(e)}")

    def _select_document(self, filename: str):
        """Handle document selection."""
        self.current_document_id = filename.split(".")[0]

    async def _handle_question(
        self, question: str, history: List[List[str]]
    ) -> tuple[str, List[List[str]]]:
        """Handle text questions."""
        if not self.current_document_id:
            raise gr.Error("Please select a document first")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/ask",
                    json={
                        "document_id": self.current_document_id,
                        "question": question
                    }
                )
                response.raise_for_status()
                answer = response.json()["answer"]
                
                history.append([question, answer])
                return "", history
        except Exception as e:
            raise gr.Error(f"Failed to get answer: {str(e)}")

    async def _handle_audio_question(
        self, audio_path: str, history: List[List[str]]
    ) -> tuple[None, List[List[str]]]:
        """Handle audio questions."""
        # TODO: Implement speech-to-text conversion
        raise gr.Error("Audio input not implemented yet")


# Create and launch the interface
def create_app():
    interface = DocumentQAInterface()
    return interface.create_interface() 