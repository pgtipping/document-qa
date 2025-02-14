from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QuestionRequest(BaseModel):
    document_id: str = Field(..., description="ID of the document to query")
    question: str = Field(..., description="Question about the document")


class QuestionResponse(BaseModel):
    answer: str = Field(..., description="Answer from the LLM")


class Document(BaseModel):
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    upload_date: datetime = Field(default_factory=datetime.now)
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type of the document") 