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
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app import models, schemas, utilis
from app.db import get_db, SessionLocal
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jwks_router)
security = HTTPBearer()

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
    token = credentials.credentials
    try:
        if ALGORITHM == "RS256" and private_key != "dev-secret-key":
            claims = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        else:
            # Fallback for development
            claims = {"sub": "dev-user-id", "roles": ["borrower"]}
        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Query DB for user
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception:
        # Fallback for development
        return {"id": user_id, "phone": "dev-phone", "full_name": "Dev User", "roles": ["borrower"]}

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
        "full_name": user.full_name,
        "roles": user.roles,
        "created_at": user.created_at,
    }

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
@score_router.post("/score/compute")
def compute_score(user: User = Depends(get_current_user)):
    score = utilis.rule_based_score(str(user.id))
    utilis.SCORES[str(user.id)] = score
    return score

@score_router.get("/score/me")
def get_score(user: User = Depends(get_current_user)):
    return utilis.SCORES.get(str(user.id), {})

# Loan Management
@loan_router.post("/loan/quote")
def loan_quote(payload: schemas.LoanQuoteSchema, user: User = Depends(get_current_user)):
    score = utilis.SCORES.get(str(user.id), {}).get("score_raw", 50)
    rate = utilis.quote_rate(score)
    return {"options": [{"tenor": payload.tenor, "rate": rate, "discount_reason": "greenscore"}]}

@loan_router.post("/loan/apply")
def loan_apply(payload: schemas.LoanApplySchema, user: User = Depends(get_current_user)):
    app_id = str(uuid4())
    utilis.LOANS[app_id] = {
        "id": app_id,
        "user_id": str(user.id),
        "amount": payload.amount,
        "tenor": payload.tenor,
        "greenscore_snapshot": utilis.SCORES.get(str(user.id)),
        "status": "submitted",
    }
    return utilis.LOANS[app_id]

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
