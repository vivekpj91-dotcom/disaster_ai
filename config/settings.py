import os
import secrets
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Secret keys & Security
    GOOGLE_API_KEY: Optional[str] = None
    JWT_SECRET: str = os.environ.get("JWT_SECRET") or secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./database/database.db"
    
    # Cloud Storage (GCS) Configuration
    GCS_BUCKET_NAME: Optional[str] = None
    
    # API Gateway Config
    API_V1_PREFIX: str = "/api"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings()
