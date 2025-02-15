"""Configuration settings for the Document Q&A application."""

import os
from typing import Set

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # File upload settings
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: Set[str] = {"txt", "pdf", "doc", "docx"}
    
    # API settings
    GROQ_API_KEY: str
    MODEL_NAME: str = "mixtral-8x7b-32768"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()  # type: ignore[call-arg] 