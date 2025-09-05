"""
Utility functions module.

This module provides utility functions for user management, role checks, S3 presigned URL generation,
scoring, and loan rate calculations.
"""

import os, boto3, time
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pathlib import Path
from celery import Celery
from typing import Dict, Any

ai_service = None

OTP_STORE = {}
USERS = {}
EVIDENCE = {}
SCORES = {}
LOANS = {}

security = HTTPBearer()

# Initialize Celery
celery_app = Celery(
    'hali_score',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configure S3/MinIO client
try:
    s3_client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.environ.get("S3_SECRET_KEY", "minioadmin"),
    )
except Exception as e:
    print(f"S3 client initialization failed: {e}")
    s3_client = None

def get_or_create_user(phone, full_name=None):
    for u in USERS.values():
        if u["phone"] == phone:
            return u
    user = {"id": str(len(USERS)+1), "phone": phone, "full_name": full_name or "", "roles": ["borrower"], "consents": {}}
    USERS[user["id"]] = user
    return user

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # For development, use a simple token
        if token == "dev-token":
            return {"id": "dev-user-id", "roles": ["borrower"]}
        
        # In production, decode JWT
        public_key = Path(os.environ.get("JWT_PUBLIC_KEY_PATH", "jwtRS256.key.pub")).read_text()
        claims = jwt.decode(token, public_key, algorithms=["RS256"])
        return USERS.get(claims["sub"], {"id": claims["sub"], "roles": claims.get("roles", [])})
    except Exception:
        raise HTTPException(401, "Invalid token")

def require_role(role):
    def checker(user=Depends(get_current_user)):
        if role not in user.get("roles", []):
            raise HTTPException(403, "Forbidden")
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
        print(f"Failed to generate presigned URL: {e}")
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
        if ai_service and evidence_id in EVIDENCE:
            evidence = EVIDENCE[evidence_id]
            # Process the evidence
            result = ai_service.analyze_receipt_ocr(evidence.get('s3_key', ''))
            EVIDENCE[evidence_id]['status'] = 'verified'
            EVIDENCE[evidence_id]['ocr_result'] = result
            return True
        return False
    except Exception as e:
        print(f"OCR processing failed: {e}")
        return False

@celery_app.task
def process_climate_practices(evidence_id: str) -> Dict:
    """Detect climate-smart practices from evidence."""
    try:
        if ai_service and evidence_id in EVIDENCE:
            evidence = EVIDENCE[evidence_id]
            result = ai_service.detect_climate_smart_practices(evidence.get('s3_key', ''))
            EVIDENCE[evidence_id]['climate_analysis'] = result
            return result
        return {"error": "Evidence not found"}
    except Exception as e:
        return {"error": str(e)}