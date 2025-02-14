import os
import uuid
import magic
from fastapi import UploadFile
from app.core.config import settings
from app.models.schemas import Document
from app.core.exceptions import (
    DocumentNotFoundError,
    InvalidFileTypeError,
    FileSizeLimitError
)
from typing import List
import aiofiles
import hashlib
from pathlib import Path


class DocumentService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

    async def save_document(self, file: UploadFile) -> str:
        """Save an uploaded document and return its ID."""
        # Validate file extension
        ext = file.filename.split('.')[-1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise InvalidFileTypeError(settings.ALLOWED_EXTENSIONS)

        # Read file content for validation
        content = await file.read()
        
        # Validate file size
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise FileSizeLimitError(settings.MAX_UPLOAD_SIZE)

        # Validate file type using libmagic
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(content)
        if not self._is_valid_mime_type(file_type):
            raise InvalidFileTypeError(settings.ALLOWED_EXTENSIONS)

        # Generate unique ID and path
        document_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{document_id}.{ext}"

        try:
            # Save file with content hash validation
            content_hash = hashlib.sha256(content).hexdigest()
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Verify written content
            if not self._verify_file_hash(file_path, content_hash):
                os.remove(file_path)
                raise FileSizeLimitError("File verification failed")

            return document_id

        except Exception as e:
            if file_path.exists():
                os.remove(file_path)
            raise e

    async def get_document_path(self, document_id: str) -> Path:
        """Get the file path for a document ID."""
        for ext in settings.ALLOWED_EXTENSIONS:
            path = self.upload_dir / f"{document_id}.{ext}"
            if path.exists():
                return path
        raise DocumentNotFoundError(document_id)

    async def list_documents(self) -> List[Document]:
        """List all uploaded documents."""
        documents = []
        for file_path in self.upload_dir.glob('*'):
            if any(file_path.name.endswith(ext) 
                  for ext in settings.ALLOWED_EXTENSIONS):
                doc_id = file_path.stem
                stat = file_path.stat()
                documents.append(
                    Document(
                        id=doc_id,
                        filename=file_path.name,
                        size=stat.st_size,
                        content_type=self._get_content_type(file_path.name)
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
            'docx': ('application/vnd.openxmlformats-officedocument.'
                    'wordprocessingml.document')
        }
        return content_types.get(ext, 'application/octet-stream')

    def _is_valid_mime_type(self, mime_type: str) -> bool:
        """Validate MIME type against allowed types."""
        allowed_mimes = {
            'text/plain': ['txt'],
            'application/pdf': ['pdf'],
            'application/msword': ['doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx']
        }
        return any(ext in settings.ALLOWED_EXTENSIONS 
                  for ext in allowed_mimes.get(mime_type, []))

    def _verify_file_hash(self, file_path: Path, expected_hash: str) -> bool:
        """Verify file content hash."""
        with open(file_path, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest() == expected_hash 