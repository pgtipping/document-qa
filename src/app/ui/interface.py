import gradio as gr
from typing import List, Tuple, Optional
import speech_recognition as sr
import os
from datetime import datetime
from app.core.connection import pool
from app.core.error_recovery import (
    CircuitBreaker,
    with_retry,
    resilient_operation
)


class DocumentQAInterface:
    def __init__(self, api_url: str = "http://localhost:8000") -> None:
        self.api_url = api_url
        self.current_document_id: Optional[str] = None
        self.recognizer = sr.Recognizer()
        self.circuit_breaker = CircuitBreaker()

    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface."""
        with gr.Blocks(title="Document Q&A", theme=gr.themes.Soft()) as interface:
            with gr.Row():
                with gr.Column(scale=1):
                    # Sidebar with enhanced document management
                    gr.Markdown("### Document Management")
                    upload_button = gr.UploadButton(
                        "📄 Upload Document",
                        file_types=["txt", "pdf", "doc", "docx"],
                        variant="primary"
                    )
                    
                    # Document list with details
                    gr.Markdown("### Your Documents")
                    document_list = gr.Dataframe(
                        headers=["Name", "Size", "Type", "Uploaded"],
                        datatype=["str", "str", "str", "str"],
                        col_count=(4, "fixed"),
                        interactive=True,
                        wrap=True
                    )
                    refresh_button = gr.Button(
                        "🔄 Refresh List",
                        variant="secondary"
                    )

                with gr.Column(scale=3):
                    # Main chat interface with improved styling
                    gr.Markdown("### Chat Interface")
                    chatbot = gr.Chatbot(
                        label="Chat History",
                        height=400,
                        bubble_full_width=False,
                        show_copy_button=True
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
                            label="🎤 Voice Input",
                            scale=2
                        )
                    submit_button = gr.Button(
                        "🚀 Ask Question",
                        variant="primary"
                    )

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
            
            document_list.select(
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

    async def _handle_upload(
        self,
        file: gr.UploadData
    ) -> List[List[str]]:
        """Handle document upload."""
        try:
            files = {"file": (file.name, open(file.name, "rb"))}
            async with resilient_operation(
                circuit_breaker=self.circuit_breaker,
                max_retries=3
            ):
                async with pool.get_client() as client:
                    response = await client.post(
                        f"{self.api_url}/api/upload",
                        files=files
                    )
                    response.raise_for_status()
            return await self._refresh_documents()
        except Exception as e:
            raise gr.Error(f"Upload failed: {str(e)}")

    @with_retry(max_retries=3)
    async def _refresh_documents(self) -> List[List[str]]:
        """Refresh the document list with formatted details."""
        try:
            async with resilient_operation(circuit_breaker=self.circuit_breaker):
                async with pool.get_client() as client:
                    response = await client.get(
                        f"{self.api_url}/api/documents"
                    )
                    response.raise_for_status()
                    documents = response.json()["documents"]
                    
                    # Format document details
                    return [
                        [
                            doc["filename"],
                            self._format_size(doc["size"]),
                            doc["content_type"].split("/")[-1].upper(),
                            self._format_date(doc["upload_date"])
                        ]
                        for doc in documents
                    ]
        except Exception as e:
            raise gr.Error(f"Failed to fetch documents: {str(e)}")

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} GB"

    def _format_date(self, date_str: str) -> str:
        """Format date in a readable format."""
        date = datetime.fromisoformat(date_str)
        return date.strftime("%Y-%m-%d %H:%M")

    def _select_document(self, evt: gr.SelectData) -> None:
        """Handle document selection from the list."""
        if evt.index is not None:
            self.current_document_id = evt.value

    async def _handle_question(
        self,
        question: str,
        history: List[List[str]]
    ) -> Tuple[str, List[List[str]]]:
        """Handle text questions."""
        if not self.current_document_id:
            raise gr.Error("Please select a document first")
        
        if not question.strip():
            raise gr.Error("Please enter a question")
        
        try:
            async with resilient_operation(
                circuit_breaker=self.circuit_breaker,
                max_retries=3
            ):
                async with pool.get_client() as client:
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
        self,
        audio_path: str,
        history: List[List[str]]
    ) -> Tuple[None, List[List[str]]]:
        """Handle audio questions using speech recognition."""
        if not self.current_document_id:
            raise gr.Error("Please select a document first")

        try:
            # Convert audio to text
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                question = self.recognizer.recognize_google(audio)

            # Get answer using the text question
            async with resilient_operation(
                circuit_breaker=self.circuit_breaker,
                max_retries=3
            ):
                async with pool.get_client() as client:
                    response = await client.post(
                        f"{self.api_url}/api/ask",
                        json={
                            "document_id": self.current_document_id,
                            "question": question
                        }
                    )
                    response.raise_for_status()
                    answer = response.json()["answer"]

                    history.append([f"🎤 {question}", answer])
                    return None, history

        except sr.UnknownValueError:
            raise gr.Error("Could not understand audio")
        except sr.RequestError as e:
            raise gr.Error(f"Speech recognition error: {str(e)}")
        except Exception as e:
            raise gr.Error(f"Failed to process audio question: {str(e)}")
        finally:
            # Clean up the temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)


# Create and launch the interface
def create_app():
    interface = DocumentQAInterface()
    return interface.create_interface() 