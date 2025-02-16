"""Configuration settings for the Document Q&A application."""

import os
from typing import List, Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # File upload settings
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    MAX_UPLOAD_SIZE_STR: str = "10485760#bytes"
    ALLOWED_EXTENSIONS_STR: str = "txt,pdf,doc,docx"
    
    # API settings
    GROQ_API_KEY: str = ""  # Set via env var
    MODEL_NAME: str = "llama-3.2-1b-preview"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="allow",
        validate_default=False  # Allow empty GROQ_API_KEY default
    )

    @property
    def ALLOWED_EXTENSIONS(self) -> List[str]:
        """Get allowed extensions as a list."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS_STR.split(",")]
    
    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        """Get max upload size as an integer."""
        return int(self.MAX_UPLOAD_SIZE_STR.split("#", maxsplit=1)[0])

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings with validation."""
        super().__init__(**kwargs)
        if not self.GROQ_API_KEY and "GROQ_API_KEY" not in os.environ:
            msg = (
                "GROQ_API_KEY must be set in environment "
                "variables or .env file"
            )
            raise ValueError(msg)


settings = Settings() 