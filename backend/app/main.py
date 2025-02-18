"""Main application module."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(
    title="Document Q&A API",
    description="API for document upload and Q&A using LLM",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "Welcome to Document Q&A API",
        "version": "1.0.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "upload_document": "/api/upload",
            "ask_question": "/api/ask",
            "list_documents": "/api/documents"
        },
        "ui": "http://localhost:7860"  # Gradio interface URL
    }

# Include API routes
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 