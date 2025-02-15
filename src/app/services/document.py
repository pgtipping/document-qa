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
from typing import List, Dict, Optional, Tuple, cast
import aiofiles
import hashlib
from pathlib import Path
import asyncio
import time
from functools import lru_cache


class DocumentService:
    def __init__(self) -> None:
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        self.content_cache: Dict[str, Tuple[bytes, float]] = {}
        self.cache_ttl = 300  # Cache TTL in seconds (5 minutes)
        self.path_cache: Dict[str, Tuple[Path, float]] = {}
        self.batch_size = 10  # Number of files to process in parallel

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
            if not await self._verify_file_hash(file_path, content_hash):
                await self._remove_file(file_path)
                raise FileSizeLimitError("File verification failed")

            # Cache the content
            self._cache_content(document_id, cast(bytes, content))
            self._cache_path(document_id, file_path)

            return document_id

        except Exception as e:
            if file_path.exists():
                await self._remove_file(file_path)
            raise e

    async def get_document_path(self, document_id: str) -> Path:
        """Get the file path for a document ID."""
        # Check path cache
        cached_path = self._get_cached_path(document_id)
        if cached_path:
            return cached_path

        # Search for the file
        for ext in settings.ALLOWED_EXTENSIONS:
            path = self.upload_dir / f"{document_id}.{ext}"
            if path.exists():
                self._cache_path(document_id, path)
                return path
        raise DocumentNotFoundError(document_id)

    async def get_document_content(self, document_id: str) -> bytes:
        """Get document content with caching."""
        # Check content cache
        cached_content = self._get_cached_content(document_id)
        if cached_content:
            return cached_content

        # Read from disk
        path = await self.get_document_path(document_id)
        async with aiofiles.open(path, 'rb') as f:
            content = await f.read()
            self._cache_content(document_id, cast(bytes, content))
            return cast(bytes, content)

    async def list_documents(self) -> List[Document]:
        """List all uploaded documents with parallel processing."""
        files = [
            f for f in self.upload_dir.glob('*')
            if any(f.name.endswith(ext) for ext in settings.ALLOWED_EXTENSIONS)
        ]
        
        # Process files in batches
        documents = []
        for i in range(0, len(files), self.batch_size):
            batch = files[i:i + self.batch_size]
            tasks = [self._process_document(file_path) for file_path in batch]
            batch_results = await asyncio.gather(*tasks)
            documents.extend(batch_results)
        
        return documents

    async def _process_document(self, file_path: Path) -> Document:
        """Process a single document file."""
        doc_id = file_path.stem
        stat = file_path.stat()
        return Document(
            id=doc_id,
            filename=file_path.name,
            size=stat.st_size,
            content_type=self._get_content_type(file_path.name)
        )

    def _cache_content(self, document_id: str, content: bytes) -> None:
        """Cache document content with timestamp."""
        self.content_cache[document_id] = (content, time.time())

    def _get_cached_content(self, document_id: str) -> Optional[bytes]:
        """Get cached content if not expired."""
        if document_id in self.content_cache:
            content, timestamp = self.content_cache[document_id]
            if time.time() - timestamp < self.cache_ttl:
                return content
            else:
                del self.content_cache[document_id]
        return None

    def _cache_path(self, document_id: str, path: Path) -> None:
        """Cache document path with timestamp."""
        self.path_cache[document_id] = (path, time.time())

    def _get_cached_path(self, document_id: str) -> Optional[Path]:
        """Get cached path if not expired."""
        if document_id in self.path_cache:
            path, timestamp = self.path_cache[document_id]
            if time.time() - timestamp < self.cache_ttl:
                return path
            else:
                del self.path_cache[document_id]
        return None

    @lru_cache(maxsize=128)
    def _get_content_type(self, filename: str) -> str:
        """Get MIME type for a filename (cached)."""
        ext = filename.split('.')[-1].lower()
        content_types = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': (
                'application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.document'
            )
        }
        return content_types.get(ext, 'application/octet-stream')

    def _is_valid_mime_type(self, mime_type: str) -> bool:
        """Validate MIME type against allowed types."""
        allowed_mimes = {
            'text/plain': ['txt'],
            'application/pdf': ['pdf'],
            'application/msword': ['doc'],
            'application/vnd.openxmlformats-officedocument.'
            'wordprocessingml.document': ['docx']
        }
        return any(
            ext in settings.ALLOWED_EXTENSIONS
            for ext in allowed_mimes.get(mime_type, [])
        )

    async def _verify_file_hash(
        self,
        file_path: Path,
        expected_hash: str
    ) -> bool:
        """Verify file content hash asynchronously."""
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
            return hashlib.sha256(content).hexdigest() == expected_hash

    async def _remove_file(self, file_path: Path) -> None:
        """Remove a file asynchronously."""
        try:
            os.remove(file_path)  # os.remove is fast enough to not need async
        except Exception:
            pass  # Ignore errors in cleanup 