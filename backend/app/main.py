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

from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app import models, schemas, utilis
from app.db import get_db
from app.db.models import User, BusinessProfile
from app.jwks import router as jwks_router

# Setup
app = FastAPI(title="GreenCredit Backend")
app.include_router(jwks_router)
security = HTTPBearer()

# Ensure JWT RS256 authentication setup
private_key = Path(os.environ["JWT_PRIVATE_KEY_PATH"]).read_text()
public_key = Path(os.environ["JWT_PUBLIC_KEY_PATH"]).read_text()
ALGORITHM = "RS256"
HMAC_SECRET = os.environ.get("AUDIT_HMAC_SECRET", "devsecret").encode()


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        claims = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Query DB for user
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Create routers for different functionalities
auth_router = APIRouter()
profile_router = APIRouter()
evidence_router = APIRouter()
score_router = APIRouter()
loan_router = APIRouter()
admin_router = APIRouter()


# Authentication
@auth_router.post("/auth/otp")
def send_otp(payload: schemas.PhoneSchema):
    code = f"{random.randint(0, 999999):06d}"
    hashed = hashlib.sha256(code.encode()).hexdigest()
    expiry = int(time.time()) + 300
    utilis.OTP_STORE[payload.phone] = (hashed, expiry)  # later → Redis/DB
    print(f"OTP for {payload.phone}: {code}")
    return {"status": "sent"}


@auth_router.post("/auth/verify")
def verify_otp(payload: schemas.VerifySchema, db: Session = Depends(get_db)):
    phone, code = payload.phone, payload.code
    stored = utilis.OTP_STORE.get(phone)
    if not stored:
        raise HTTPException(400, "No OTP requested")
    hashed, expiry = stored
    if int(time.time()) > expiry:
        raise HTTPException(400, "OTP expired")
    if hashlib.sha256(code.encode()).hexdigest() != hashed:
        raise HTTPException(400, "Invalid code")

    # Upsert user in DB
    user = db.query(User).filter_by(phone=phone).first()
    if not user:
        user = User(phone=phone, full_name=payload.full_name or "")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Issue JWT
    now = int(time.time())
    claims = {
        "sub": str(user.id),
        "roles": user.roles or ["borrower"],
        "consents": getattr(user, "consents", []),
        "scope": ["user"],
        "iat": now,
        "exp": now + 3600,
    }
    token = jwt.encode(claims, private_key, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}



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



# Evidence Management

@evidence_router.post("/evidence")
def create_evidence(user: User = Depends(get_current_user)):
    evid_id = str(uuid4())
    key = f"evidence/{evid_id}.jpg"
    url = utilis.create_presigned_put(key, "image/jpeg")
    utilis.EVIDENCE[evid_id] = {"id": evid_id, "status": "pending", "s3_key": key}
    return {"id": evid_id, "url": url}


@evidence_router.post("/evidence/{id}/finalize")
def finalize_evidence(id: str, user: User = Depends(get_current_user)):
    ev = utilis.EVIDENCE.get(id)
    if not ev:
        raise HTTPException(404, "Not found")
    ev["status"] = "processing"
    utilis.EVIDENCE[id] = ev
    return {"id": id, "status": "processing"}


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
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(evidence_router)
app.include_router(score_router)
app.include_router(loan_router)
app.include_router(admin_router)
