import os
import uuid
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.models.schemas import Document
from typing import List
import aiofiles
import shutil


class DocumentService:
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    async def save_document(self, file: UploadFile) -> str:
        """Save an uploaded document and return its ID."""
        # Validate file extension
        ext = file.filename.split('.')[-1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
            )

        # Generate unique ID and path
        document_id = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.{ext}")

        try:
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                if len(content) > settings.MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes"
                    )
                await f.write(content)

            return document_id

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_document_path(self, document_id: str) -> str:
        """Get the file path for a document ID."""
        for ext in settings.ALLOWED_EXTENSIONS:
            path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.{ext}")
            if os.path.exists(path):
                return path
        raise HTTPException(status_code=404, detail="Document not found")

    async def list_documents(self) -> List[Document]:
        """List all uploaded documents."""
        documents = []
        for filename in os.listdir(settings.UPLOAD_DIR):
            if any(filename.endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
                path = os.path.join(settings.UPLOAD_DIR, filename)
                doc_id = filename.split('.')[0]
                stat = os.stat(path)
                documents.append(
                    Document(
                        id=doc_id,
                        filename=filename,
                        size=stat.st_size,
                        content_type=self._get_content_type(filename)
                    )
                )
        return documents

    def _get_content_type(self, filename: str) -> str:
        """Get MIME type for a filename."""
        ext = filename.split('.')[-1].lower()
        content_types = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return content_types.get(ext, 'application/octet-stream') 