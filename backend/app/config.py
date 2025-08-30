"""
Configuration module for HaliScore.

This module manages environment variables and application settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/haliscore"
    
    # JWT Authentication
    JWT_PRIVATE_KEY_PATH: str = "jwtRS256.key"
    JWT_PUBLIC_KEY_PATH: str = "jwtRS256.key.pub"
    JWT_ALGORITHM: str = "RS256"
    JWT_EXPIRY_HOURS: int = 24
    
    # S3/MinIO Storage
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "haliscore"
    
    # Redis and Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Security
    AUDIT_HMAC_SECRET: str = "devsecret"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "HaliScore"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # AI/ML Settings
    AI_MODEL_PATH: Optional[str] = None
    OCR_LANGUAGE: str = "eng"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
