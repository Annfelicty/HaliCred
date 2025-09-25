"""
Authentication API module.

This module handles user authentication including OTP generation, verification,
and JWT token management.
"""

import base64
import hashlib
import random
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User
from app.schemas import OTPSendResponse, OTPRequestSchema, VerifySchema, PasswordLoginSchema

router = APIRouter(prefix="/auth", tags=["authentication"])

# In-memory OTP store (replace with Redis in production)
OTP_STORE: Dict[str, Dict[str, Any]] = {}

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 150_000
SME_GRACE_PERIOD = timedelta(hours=6)
BANK_GRACE_PERIOD = timedelta(hours=12)


def _now() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def _contact_key(phone: str | None, email: str | None) -> Tuple[str, str]:
    if phone and email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide only one identifier")
    if not phone and not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either phone or email is required")
    if phone:
        return phone, "phone"
    return email, "email"  # type: ignore


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{PASSWORD_ALGORITHM}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt_b64, digest_b64 = stored.split("$")
        if algorithm != PASSWORD_ALGORITHM:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return secrets.compare_digest(expected, candidate)
    except Exception:
        return False


def _issue_token(user: User, now: datetime) -> Dict[str, Any]:
    claims = {
        "sub": str(user.id),
        "roles": user.roles or ["borrower"],
        "phone": user.phone,
        "email": user.email,
        "scope": ["user"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.JWT_EXPIRY_HOURS)).timestamp()),
    }

    algorithm = settings.JWT_ALGORITHM.upper()
    if algorithm.startswith("HS"):
        signing_key = settings.SECRET_KEY
    else:
        private_key = getattr(settings, "JWT_PRIVATE_KEY", None)
        if not private_key:
            key_path = Path(settings.JWT_PRIVATE_KEY_PATH)
            if key_path.exists():
                private_key = key_path.read_text()
                setattr(settings, "JWT_PRIVATE_KEY", private_key)
            else:
                raise RuntimeError("JWT private key not configured for RS algorithm")
        signing_key = private_key

    token = jwt.encode(claims, signing_key, algorithm=settings.JWT_ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRY_HOURS * 3600,
        "user": {
            "id": str(user.id),
            "phone": user.phone,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
        },
        "last_otp_verified_at": user.last_otp_verified_at.isoformat() if user.last_otp_verified_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }

@router.get("/otp", status_code=status.HTTP_404_NOT_FOUND)
async def otp_not_found() -> None:
    """Placeholder GET handler to satisfy health checks/tests."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submit OTP requests with POST")


@router.post("/otp", response_model=OTPSendResponse)
async def send_otp(payload: OTPRequestSchema) -> OTPSendResponse:
    """
    Send OTP to the provided phone number.
    
    Args:
        payload: OTPRequestSchema containing phone or email
        
    Returns:
        Dict with status message
    """
    try:
        identifier, contact_type = _contact_key(payload.phone, payload.email)

        # Generate 6-digit OTP (deterministic in development for testing)
        if settings.ENVIRONMENT.lower() in {"development", "testing", "dev"}:
            code = "123456"
        else:
            code = f"{random.randint(0, 999999):06d}"
        hashed = hashlib.sha256(code.encode()).hexdigest()
        expires_at = _now() + timedelta(minutes=5)

        # Store OTP (in production, use Redis)
        OTP_STORE[identifier] = {"hash": hashed, "expires_at": expires_at}

        # In production, integrate with SMS/email service here
        print(f"OTP for {contact_type} {identifier}: {code}")
        
        return OTPSendResponse(
            status="sent",
            message="OTP sent successfully",
            expires_in=300,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )

@router.get("/verify", status_code=status.HTTP_404_NOT_FOUND)
async def verify_not_found() -> None:
    """Placeholder GET handler to satisfy health checks/tests."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submit OTP verification with POST")


@router.post("/verify", response_model=Dict[str, Any])
async def verify_otp(payload: VerifySchema, db: Session = Depends(get_db)):
    """
    Verify OTP and authenticate user.
    
    Args:
        payload: VerifySchema containing identifier, code, and optional metadata
        db: Database session
        
    Returns:
        Dict with access token and user info
    """
    try:
        identifier, contact_type = _contact_key(payload.phone, payload.email)
        code = payload.code

        stored = OTP_STORE.get(identifier)
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No OTP requested for this identifier"
            )

        hashed = stored["hash"]
        expires_at = stored["expires_at"]

        if _now() > expires_at:
            del OTP_STORE[identifier]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired"
            )

        submitted_hash = hashlib.sha256(code.encode()).hexdigest()
        if submitted_hash != hashed:
            # Allow deterministic development OTP when hashed value differs
            dev_override = settings.ENVIRONMENT.lower() in {"development", "testing", "dev"} and code == "123456"
            if not dev_override:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OTP code"
                )

        del OTP_STORE[identifier]

        query_filter = User.email == identifier if contact_type == "email" else User.phone == identifier
        user = db.query(User).filter(query_filter).first()

        new_user = False
        if not user:
            user = User(
                phone=identifier if contact_type == "phone" else payload.phone,
                email=identifier if contact_type == "email" else payload.email,
                full_name=payload.full_name or "",
                roles=payload.roles or (["borrower"] if contact_type == "phone" else ["underwriter"]),
            )
            db.add(user)
            new_user = True
        else:
            if contact_type == "phone" and not user.phone:
                user.phone = identifier
            if contact_type == "email" and not user.email:
                user.email = identifier

        if payload.full_name and payload.full_name != user.full_name:
            user.full_name = payload.full_name

        if payload.roles:
            user.roles = payload.roles

        if payload.password:
            user.password_hash = _hash_password(payload.password)

        current_time = _now()
        user.last_otp_verified_at = current_time
        user.last_login_at = current_time

        db.commit()
        if new_user:
            db.refresh(user)

        return _issue_token(user, current_time)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/login", response_model=Dict[str, Any])
async def password_login(payload: PasswordLoginSchema, db: Session = Depends(get_db)):
    """Authenticate using password within OTP grace window."""

    identifier, contact_type = _contact_key(payload.phone, payload.email)
    query_filter = User.email == identifier if contact_type == "email" else User.phone == identifier
    user = db.query(User).filter(query_filter).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password login unavailable. Please request an OTP."
        )

    if not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    grace_period = BANK_GRACE_PERIOD if contact_type == "email" else SME_GRACE_PERIOD
    if not user.last_otp_verified_at or _now() - user.last_otp_verified_at > grace_period:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OTP verification required before logging in"
        )

    current_time = _now()
    user.last_login_at = current_time
    db.commit()

    return _issue_token(user, current_time)

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token():
    """
    Refresh JWT token (placeholder for future implementation).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not implemented yet"
    )

@router.post("/logout")
async def logout():
    """
    Logout user (placeholder for future implementation).
    """
    return {"message": "Logged out successfully"}
