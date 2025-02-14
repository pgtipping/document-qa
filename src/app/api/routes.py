from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.document import DocumentService
from app.services.llm import LLMService
from app.models.schemas import QuestionRequest, QuestionResponse
from typing import List
import os

router = APIRouter()
document_service = DocumentService()
llm_service = LLMService()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for Q&A."""
    try:
        document_id = await document_service.save_document(file)
        return {"document_id": document_id, "message": "Document uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(question: QuestionRequest):
    """Ask a question about the uploaded document."""
    try:
        answer = await llm_service.get_answer(
            question.document_id,
            question.question
        )
        return QuestionResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    try:
        documents = await document_service.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 