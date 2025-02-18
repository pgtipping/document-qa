"""Document service module for handling file operations and caching."""

import asyncio
import hashlib
import os
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import io
import logging

import aiofiles
import magic
from fastapi import UploadFile
import PyPDF2

from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundError,
    InvalidFileTypeError,
    FileSizeLimitError,
)
from app.models.schemas import Document

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DocumentService:
    """Service for managing document operations with caching."""

    def __init__(self) -> None:
        """Initialize document service with caching."""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        self.content_cache: Dict[str, Tuple[bytes, float]] = {}
        self.cache_ttl = 300  # Cache TTL in seconds (5 minutes)
        self.path_cache: Dict[str, Tuple[Path, float]] = {}
        self.batch_size = 10  # Number of files to process in parallel

    async def save_document(self, file: UploadFile) -> str:
        """Save an uploaded document and return its ID."""
        if not file.filename:
            raise InvalidFileTypeError(set(settings.ALLOWED_EXTENSIONS))

        # Validate file extension
        ext = file.filename.split('.')[-1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise InvalidFileTypeError(set(settings.ALLOWED_EXTENSIONS))

        # Read file content for validation
        content = await file.read()
        await file.seek(0)  # Reset file pointer for later use

        # Validate file size
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise FileSizeLimitError(settings.MAX_UPLOAD_SIZE)

        # Validate file type using libmagic
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(content)
        logger.debug(f"Detected MIME type: {file_type}")
        if not self._is_valid_mime_type(file_type):
            raise InvalidFileTypeError(set(settings.ALLOWED_EXTENSIONS))

        # Generate unique ID and path
        document_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{document_id}.{ext}"
        logger.debug(f"Saving file to: {file_path}")

        try:
            # Save file with content hash validation
            content_hash = hashlib.sha256(content).hexdigest()

            # Ensure upload directory exists
            self.upload_dir.mkdir(parents=True, exist_ok=True)

            # Save file in chunks to handle large files
            async with aiofiles.open(file_path, 'wb') as f:
                chunk_size = 1024 * 1024  # 1MB chunks
                while chunk := await file.read(chunk_size):
                    await f.write(chunk)

            # Verify written content
            if not await self._verify_file_hash(file_path, content_hash):
                await self._remove_file(file_path)
                raise FileSizeLimitError(settings.MAX_UPLOAD_SIZE)

            # Cache the content
            self._cache_content(document_id, content)
            self._cache_path(document_id, file_path)

            return document_id

        except (OSError, IOError) as e:
            logger.error(f"Error saving file: {str(e)}")
            if file_path.exists():
                await self._remove_file(file_path)
            raise FileSizeLimitError(settings.MAX_UPLOAD_SIZE)

    async def get_document_path(self, document_id: str) -> Path:
        """Get the file path for a document ID."""
        cached_path = self._get_cached_path(document_id)
        if cached_path:
            return cached_path

        for ext in settings.ALLOWED_EXTENSIONS:
            path = self.upload_dir / f"{document_id}.{ext}"
            if path.exists():
                self._cache_path(document_id, path)
                return path
        raise DocumentNotFoundError(document_id)

    async def get_document_content(self, document_id: str) -> bytes:
        """Get document content with caching."""
        cached_content = self._get_cached_content(document_id)
        if cached_content:
            logger.debug("Using cached content")
            return cached_content

        path = await self.get_document_path(document_id)
        logger.debug(f"Reading content from: {path}")
        try:
            if path.suffix.lower() == '.pdf':
                # Extract text from PDF
                logger.debug("Extracting text from PDF")
                content = await self._extract_pdf_text(path)
                logger.debug(f"Extracted text length: {len(content)}")
                content_bytes = content.encode('utf-8')
                self._cache_content(document_id, content_bytes)
                return content_bytes
            elif path.suffix.lower() in ['.txt', '.md']:
                # Read text files directly
                logger.debug("Reading text file")
                async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    content_bytes = content.encode('utf-8')
                    self._cache_content(document_id, content_bytes)
                    return content_bytes
            else:
                # For other files, try to read as text first
                try:
                    logger.debug("Attempting to read as text")
                    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        content_bytes = content.encode('utf-8')
                        self._cache_content(document_id, content_bytes)
                        return content_bytes
                except UnicodeDecodeError:
                    # If text reading fails, return raw bytes
                    logger.debug("Falling back to raw bytes")
                    async with aiofiles.open(path, 'rb') as f:
                        content = await f.read()
                        self._cache_content(document_id, content)
                        return content
        except Exception as e:
            logger.error(f"Error reading document: {str(e)}")
            raise ValueError(f"Error reading document: {str(e)}")

    async def _extract_pdf_text(self, path: Path) -> str:
        """Extract text content from a PDF file."""
        try:
            # Read the PDF file in binary mode
            logger.debug("Opening PDF file")
            async with aiofiles.open(path, 'rb') as file:
                content = await file.read()
                
            # Create a PDF reader object
            logger.debug("Creating PDF reader")
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            logger.debug(f"Number of pages: {len(pdf_reader.pages)}")
            
            # Extract text from all pages
            text_content = []
            for i, page in enumerate(pdf_reader.pages):
                logger.debug(f"Extracting text from page {i+1}")
                text = page.extract_text()
                if text:
                    text_content.append(text.strip())
                    logger.debug(f"Page {i+1} text length: {len(text)}")
            
            full_text = "\n\n".join(text_content)
            logger.debug(f"Total extracted text length: {len(full_text)}")
            return full_text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise ValueError(f"Error extracting PDF text: {str(e)}")

    async def list_documents(self) -> List[Document]:
        """List all uploaded documents with parallel processing."""
        files = [
            f for f in self.upload_dir.glob('*')
            if any(f.name.endswith(ext) for ext in settings.ALLOWED_EXTENSIONS)
        ]

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
            (
                'application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.document'
            ): ['docx'],
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
        except (OSError, IOError):
            pass  # Ignore file removal errors during cleanup
