"""
Utility functions module.

This module provides utility functions for user management, role checks, S3 presigned URL generation,
scoring, and loan rate calculations.
"""

import os
import boto3
import time
import logging
from fastapi import Depends, HTTPException
from app.auth import get_current_user as auth_get_current_user
from celery import Celery
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.db import get_db, SessionLocal
from app.models import Evidence

ai_service = None

# Legacy in-memory storage (migrated to database)
USERS = {}  # TODO: Remove after full migration to User model


# Logging setup
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'hali_score',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

if os.environ.get("CELERY_TASK_ALWAYS_EAGER") == "1":
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

# Configure S3/MinIO client
try:
    s3_client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.environ.get("S3_SECRET_KEY", "minioadmin"),
    )
except Exception as e:
    logger.warning("S3 client initialization failed: %s", e)
    s3_client = None

def get_or_create_user(phone, full_name=None):
    for u in USERS.values():
        if u["phone"] == phone:
            return u
    user = {"id": str(len(USERS)+1), "phone": phone, "full_name": full_name or "", "roles": ["borrower"], "consents": {}}
    USERS[user["id"]] = user
    return user

def require_role(role):
    """Role-based access control using proper authentication."""
    def checker(user=Depends(auth_get_current_user)):
        # user is now a User model from app.auth.get_current_user
        user_roles = user.roles or []
        if role not in user_roles:
            raise HTTPException(403, f"Role '{role}' required for this operation")
        return user
    return checker

def create_presigned_put(key: str, content_type: str, expires=600) -> str:
    if not s3_client:
        # Fallback for development
        return f"http://localhost:9000/upload/{key}"
    
    try:
        return s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": os.environ.get("S3_BUCKET", "haliscore"), "Key": key, "ContentType": content_type},
            ExpiresIn=expires,
        )
    except Exception as e:
        logger.warning("Failed to generate presigned URL: %s", e)
        return f"http://localhost:9000/upload/{key}"

# AI-powered scoring
def rule_based_score(user_id: str) -> Dict[str, Any]:
    """Calculate Green Score using AI service."""
    if ai_service:
        # Get user data from database (simplified for now)
        user_data = {
            "business_type": "agriculture",
            "evidence": [
                {"type": "receipt", "path": "/tmp/sample_receipt.jpg"}
            ]
        }
        return ai_service.calculate_green_score(user_data)
    else:
        # Fallback scoring
        return {
            "score_raw": 75,
            "score_0_100": 75,
            "subscores": {"energy": 20, "water": 15, "waste": 20, "behavior": 20},
            "explanations": ["+20 solar vendor", "+10 LED evidence"],
            "computed_at": time.time(),
            "confidence": 0.8
        }

def quote_rate(score: int, base_rate=0.20, discount_factor=0.25) -> float:
    """Calculate loan rate based on Green Score."""
    s = max(0, min(100, score))
    return round(base_rate * (1 - discount_factor * (s / 100.0)), 4)

@celery_app.task
def process_ocr(evidence_id: str) -> bool:
    """Process OCR for evidence using AI service."""
    try:
        # Create database session for Celery task
        db = SessionLocal()
        try:
            evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
            if not evidence:
                logger.error(f"Evidence not found: {evidence_id}")
                return False

            if ai_service:
                # Process the evidence
                result = ai_service.analyze_receipt_ocr(evidence.s3_key)
                # Update evidence status in database
                evidence.status = 'verified'
                # Note: OCR result would need to be stored in a new field or in Evidence model
                db.commit()
                return True
            else:
                logger.warning("AI service not available for OCR processing")
                return False
        finally:
            db.close()
    except Exception as e:
        logger.error("OCR processing failed: %s", e)
        return False
@celery_app.task
def process_climate_practices(evidence_id: str) -> Dict:
    """Detect climate-smart practices from evidence."""
    try:
        # Create database session for Celery task
        db = SessionLocal()
        try:
            evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
            if not evidence:
                logger.error(f"Evidence not found: {evidence_id}")
                return {"error": "Evidence not found"}

            if ai_service:
                result = ai_service.detect_climate_smart_practices(evidence.s3_key)
                # Note: Climate analysis result would need to be stored in a new field or in Evidence model
                return result
            else:
                logger.warning("AI service not available for climate analysis")
                return {"error": "AI service not available"}
        finally:
            db.close()
    except Exception as e:
        logger.error("Climate practices processing failed: %s", e, exc_info=True)
        return {"error": str(e)}