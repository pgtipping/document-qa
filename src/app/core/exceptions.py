from fastapi import HTTPException
from typing import Any, Optional


class DocumentQAException(HTTPException):
    """Base exception for Document Q&A application."""
    def __init__(
        self,
        status_code: int = 500,
        detail: Any = None,
        headers: Optional[dict] = None
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers
        )


class DocumentNotFoundError(DocumentQAException):
    """Raised when a document is not found."""
    def __init__(self, document_id: str):
        super().__init__(
            status_code=404,
            detail=f"Document not found: {document_id}"
        )


class InvalidFileTypeError(DocumentQAException):
    """Raised when an invalid file type is uploaded."""
    def __init__(self, allowed_types: set):
        super().__init__(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {allowed_types}"
        )


class FileSizeLimitError(DocumentQAException):
    """Raised when file size exceeds limit."""
    def __init__(self, max_size: int):
        super().__init__(
            status_code=400,
            detail=f"File too large. Max size: {max_size} bytes"
        )


class LLMConfigError(DocumentQAException):
    """Raised when LLM configuration is invalid."""
    def __init__(self, message: str = "LLM configuration error"):
        super().__init__(
            status_code=500,
            detail=message
        ) 