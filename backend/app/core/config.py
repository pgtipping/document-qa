"""Configuration settings for the Document Q&A application."""

import os
from pathlib import Path
from typing import List, Any
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the absolute path to the backend directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Load environment variables from .env file
env_file = os.path.join(BACKEND_DIR, ".env")
load_dotenv(env_file)

class Settings(BaseSettings):
    """Application settings."""
    
    # File upload settings
    UPLOAD_DIR: str = os.path.join(BACKEND_DIR, "uploads")
    MAX_UPLOAD_SIZE_STR: str = "10485760#bytes"
    ALLOWED_EXTENSIONS_STR: str = "txt,pdf,doc,docx"
    
    # API settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.2-1b-preview")
    
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        env_prefix="",
        extra="allow"
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings with validation."""
        print(f"Looking for .env file at: {env_file}")
        print(f"File exists: {os.path.exists(env_file)}")
        
        super().__init__(**kwargs)
        # Create upload directory if it doesn't exist
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        
        print(f"GROQ_API_KEY is set: {bool(self.GROQ_API_KEY)}")
        print(f"GROQ_API_KEY in env: {bool('GROQ_API_KEY' in os.environ)}")
        
        if not self.GROQ_API_KEY:
            msg = (
                "GROQ_API_KEY must be set in environment "
                "variables or .env file"
            )
            raise ValueError(msg)

    @property
    def ALLOWED_EXTENSIONS(self) -> List[str]:
        """Get allowed extensions as a list."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS_STR.split(",")]
    
    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        """Get max upload size as an integer."""
        return int(self.MAX_UPLOAD_SIZE_STR.split("#", maxsplit=1)[0])


settings = Settings()