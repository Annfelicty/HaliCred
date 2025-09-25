"""
Main application module.

This module initializes the FastAPI application and includes all API routers.
It handles authentication, user profiles, evidence management, scoring, and loan management.

Classes:
    - None

Functions:
    - get_db: Dependency function to provide a database session.
    - get_current_user: Dependency function to get the current authenticated user.

Routers:
    - auth_router: Handles authentication-related endpoints.
    - profile_router: Manages user profile-related endpoints.
    - evidence_router: Manages evidence-related endpoints.
    - score_router: Handles scoring-related endpoints.
    - loan_router: Manages loan-related endpoints.
    - admin_router: Handles admin-related endpoints.

Each router includes endpoints for specific functionalities:
    - Authentication: /auth/otp, /auth/verify
    - User Profile: /me, /me/consents, /me/profile
    - Evidence: /evidence, /evidence/{id}/finalize
    - Scoring: /score/compute, /score/me
    - Loan Management: /loan/quote, /loan/apply
    - Admin: /admin/applications, /admin/applications/{id}/decision
"""

# app/main.py
import os, time, random, hashlib, hmac
from pathlib import Path
from uuid import uuid4, UUID

from fastapi import FastAPI, Depends, HTTPException, APIRouter, status
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from typing import List

from app import models, schemas, utilis
from app.db import get_db
from app.models import User, BusinessProfile
from app.jwks import router as jwks_router
from app.config import settings

# Import API modules
from app.api import auth, evidence, ai_engine

# Setup
app = FastAPI(
    title="HaliScore Backend",
    description="AI-powered eco-finance platform that transforms sustainable actions into financial credibility",
    version="1.0.0"
)

# CORS Configuration
origins = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(jwks_router)
security = HTTPBearer(auto_error=False)

# Ensure JWT RS256 authentication setup
try:
    private_key = Path(settings.JWT_PRIVATE_KEY_PATH).read_text()
    public_key = Path(settings.JWT_PUBLIC_KEY_PATH).read_text()
except FileNotFoundError:
    # Fallback for development - generate simple keys
    private_key = "dev-secret-key"
    public_key = "dev-secret-key"
    
ALGORITHM = settings.JWT_ALGORITHM
HMAC_SECRET = settings.AUDIT_HMAC_SECRET.encode()

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "haliscore-backend"}

# Dependencies
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication credentials were not provided")

    token = credentials.credentials
    algorithm = settings.JWT_ALGORITHM.upper()
    try:
        if algorithm.startswith("HS"):
            claims = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_aud": False},
            )
        else:
            key_path = Path(settings.JWT_PUBLIC_KEY_PATH)
            if key_path.exists():
                public_key = key_path.read_text()
            else:
                # Workaround for missing key in development/test environments
                public_key = settings.SECRET_KEY
            claims = jwt.decode(
                token,
                public_key,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_aud": False},
            )
        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        user_uuid = UUID(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token subject")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Create routers for different functionalities
profile_router = APIRouter()
score_router = APIRouter()
loan_router = APIRouter()
admin_router = APIRouter()

# User Info & Profile (DB-backed)
@profile_router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "phone": user.phone,
        "email": user.email,
        "full_name": user.full_name,
        "roles": user.roles,
        "created_at": user.created_at,
    }

@profile_router.get("/me/consents")
def get_consents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user.id).first()
    consents = getattr(profile, "consents", None) if profile else None
    if not consents:
        raise HTTPException(status_code=404, detail="Consents not found")
    return consents


@profile_router.post("/me/consents")
def save_consents(
    payload: schemas.ConsentSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user.id).first()
    if not profile:
        profile = BusinessProfile(user_id=user.id)
        db.add(profile)

    profile.consents = payload.dict()
    profile.consents["timestamp"] = int(time.time())
    db.commit()
    db.refresh(profile)
    return profile.consents

@profile_router.get("/me/profile")
def fetch_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user.id).first()
    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "roles": user.roles,
        "business_type": getattr(profile, "business_type", None) if profile else None,
        "business_name": getattr(profile, "business_name", None) if profile else None,
    }


@profile_router.patch("/me/profile")
def update_profile(
    payload: schemas.ProfileSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    update_data = payload.dict(exclude_unset=True)

    if "full_name" in update_data:
        user.full_name = update_data["full_name"]
    if "phone" in update_data:
        user.phone = update_data["phone"]
    if "email" in update_data:
        user.email = update_data["email"]

    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user.id).first()
    if not profile:
        profile = BusinessProfile(user_id=user.id)
        db.add(profile)

    if "business_type" in update_data:
        profile.business_type = update_data["business_type"]
    if "business_name" in update_data:
        profile.business_name = update_data["business_name"]

    db.commit()
    db.refresh(user)
    db.refresh(profile)

    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "phone": user.phone,
        "roles": user.roles,
        "business_type": profile.business_type if profile else None,
        "business_name": profile.business_name if profile else None,
    }

# Scoring
@score_router.get("/score/compute")
def compute_score_not_allowed():
    raise HTTPException(status_code=404, detail="Use POST to compute score")


@score_router.post("/score/compute")
def compute_score(user: User = Depends(get_current_user)):
    score = utilis.rule_based_score(str(user.id))
    utilis.SCORES[str(user.id)] = score
    return score

@score_router.get("/score/me")
def get_score(user: User = Depends(get_current_user)):
    return utilis.SCORES.get(str(user.id), {})

# Loan Management
@loan_router.get("/loan/quote")
def loan_quote_not_allowed():
    raise HTTPException(status_code=404, detail="Submit loan quote requests with POST")


@loan_router.post("/loan/quote")
def loan_quote(payload: schemas.LoanQuoteSchema, user: User = Depends(get_current_user)):
    score = utilis.SCORES.get(str(user.id), {}).get("score_raw", 50)
    rate = utilis.quote_rate(score)
    return {"options": [{"tenor": payload.tenor, "rate": rate, "discount_reason": "greenscore"}]}

@loan_router.get("/loan/apply")
def loan_apply_not_allowed():
    raise HTTPException(status_code=404, detail="Submit loan applications with POST")


@loan_router.post("/loan/apply", response_model=schemas.LoanRecordSchema)
def loan_apply(payload: schemas.LoanApplySchema, user: User = Depends(get_current_user)):
    app_id = str(uuid4())
    created_at = int(time.time())
    score_snapshot = utilis.SCORES.get(str(user.id))
    quoted_rate = None
    if score_snapshot and isinstance(score_snapshot, dict):
        quoted_rate = utilis.quote_rate(score_snapshot.get("score_raw", 50))
    utilis.LOANS[app_id] = {
        "id": app_id,
        "user_id": str(user.id),
        "amount": payload.amount,
        "tenor": payload.tenor,
        "greenscore_snapshot": score_snapshot,
        "status": "submitted",
        "purpose": payload.purpose,
        "quoted_rate": quoted_rate,
        "created_at": created_at,
    }
    return utilis.LOANS[app_id]


@loan_router.get("/loan/my", response_model=List[schemas.LoanRecordSchema])
def list_my_loans(user: User = Depends(get_current_user)):
    user_id = str(user.id)
    records = [
        loan
        for loan in utilis.LOANS.values()
        if loan.get("user_id") == user_id
    ]
    # Sort newest first for convenience
    records.sort(key=lambda item: item.get("created_at", 0), reverse=True)
    return records

# Admin routes
@admin_router.get("/admin/applications")
def list_applications(status: str = "submitted", user=Depends(utilis.require_role("underwriter"))):
    return [loan for loan in utilis.LOANS.values() if loan["status"] == status]

@admin_router.post("/admin/applications/{id}/decision")
def decide_application(id: str, payload: schemas.DecisionSchema, user=Depends(utilis.require_role("underwriter"))):
    loan = utilis.LOANS.get(id)
    if not loan:
        raise HTTPException(404, "Not found")
    loan["status"] = payload.decision
    log = {"entity": "loan", "entity_id": id, "action": payload.decision}
    loan["audit_hmac"] = hmac.new(HMAC_SECRET, str(log).encode(), hashlib.sha256).hexdigest()
    return loan

# Include all routers
app.include_router(auth.router)
app.include_router(evidence.router)
app.include_router(ai_engine.router)
app.include_router(profile_router)
app.include_router(score_router)
app.include_router(loan_router)
app.include_router(admin_router)
