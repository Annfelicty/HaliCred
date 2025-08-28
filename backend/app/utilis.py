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

OTP_STORE = {}
USERS = {}
EVIDENCE = {}
SCORES = {}
LOANS = {}

security = HTTPBearer()
public_key = Path(os.environ["JWT_PUBLIC_KEY_PATH"]).read_text()

# Initialize Celery
celery_app = Celery(
    'hali_score',
    broker=os.environ.get('CELERY_BROKER_URL'),
    backend=os.environ.get('CELERY_RESULT_BACKEND')
)

# Configure S3/MinIO client
s3_client = boto3.client(
    "s3",
    endpoint_url=os.environ.get("S3_ENDPOINT"),
    aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("S3_SECRET_KEY"),
)

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
        claims = jwt.decode(token, public_key, algorithms=["RS256"])
    except Exception:
        raise HTTPException(401, "Invalid token")
    return USERS.get(claims["sub"], {"id": claims["sub"], "roles": claims.get("roles", [])})

def require_role(role):
    def checker(user=Depends(get_current_user)):
        if role not in user.get("roles", []):
            raise HTTPException(403, "Forbidden")
        return user
    return checker

def create_presigned_put(key: str, content_type: str, expires=600) -> str:
    return s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": os.environ["S3_BUCKET"], "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )

# Rule-based scoring (toy example)
def rule_based_score(user_id: str):
    return {
        "score_raw": 75,
        "score_0_100": 75,
        "subscores": {"energy": 20, "water": 15, "waste": 20, "behavior": 20},
        "explanation": ["+20 solar vendor", "+10 LED evidence"],
    }

def quote_rate(score: int, base_rate=0.20, discount_factor=0.25) -> float:
    s = max(0, min(100, score))
    return round(base_rate * (1 - discount_factor * (s / 100.0)), 4)

@celery_app.task
def process_ocr(evidence_id):
    # Placeholder for OCR processing logic
    print(f"Processing OCR for evidence ID: {evidence_id}")
    # Update evidence status to 'verified' after processing
    EVIDENCE[evidence_id]['status'] = 'verified'
    return True