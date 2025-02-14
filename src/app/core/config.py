from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Document Q&A"
    
    # LLM Configuration
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    MODEL_NAME: str = "llama2-70b-4096"
    
    # Document Storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {"txt", "pdf", "doc", "docx"}
    
    # Security
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    class Config:
        case_sensitive = True

settings = Settings() 