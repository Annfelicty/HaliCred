"""
Configuration module for HaliScore.

This module manages environment variables and application settings.
"""

import os
from typing import Optional

class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://halicred_user:HaliCred2024!Secure@localhost:5432/halicred_db")
        
        # JWT Authentication
        self.JWT_PRIVATE_KEY_PATH = os.getenv("JWT_PRIVATE_KEY_PATH", "./keys/private_key.pem")
        self.JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "./keys/public_key.pem")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "Vsj5Sz3fIzHXyLd1uTebrvtPnWRGC_4V_kV_DhRVsr3nH8mU0A5o96xGU4Iqa7XbfmkIRpVr2EGSOAN4G9dW2g")
        
        # S3/MinIO Storage
        self.S3_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.S3_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.S3_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.S3_BUCKET = os.getenv("MINIO_BUCKET", "halicred-evidence")
        
        # Redis and Celery
        self.CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
        self.CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
        
        # Security
        self.AUDIT_HMAC_SECRET = os.getenv("AUDIT_HMAC_SECRET", "gWSicjkO5182OewT_24xjGIkariixz2z_qdeYaLACpDIzrBMKNhBtqozR0eR3sRhfXmqtOgyx8xI4G9Je58jcA")
        self.SECRET_KEY = os.getenv("JWT_SECRET_KEY", "Vsj5Sz3fIzHXyLd1uTebrvtPnWRGC_4V_kV_DhRVsr3nH8mU0A5o96xGU4Iqa7XbfmkIRpVr2EGSOAN4G9dW2g")
        
        # AI Services
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY", "")
        self.CLIMATIQ_API_KEY = os.getenv("CLIMATIQ_API_KEY", "")
        
        # API Settings
        self.API_V1_STR = "/api/v1"
        self.PROJECT_NAME = "HaliScore"
        
        # CORS
        self.BACKEND_CORS_ORIGINS = ["*"]
        
        # AI/ML Settings
        self.AI_MODEL_PATH: Optional[str] = None
        self.OCR_LANGUAGE = "eng"
        
        # Environment
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Global settings instance
settings = Settings()
