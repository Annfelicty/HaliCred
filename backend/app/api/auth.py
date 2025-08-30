"""
Authentication API module.

This module handles user authentication including OTP generation, verification,
and JWT token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import time
import hashlib
import random
from jose import jwt

from app.db import get_db
from app.models import User
from app.schemas import PhoneSchema, VerifySchema
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

# In-memory OTP store (replace with Redis in production)
OTP_STORE = {}

@router.post("/otp", response_model=Dict[str, str])
async def send_otp(payload: PhoneSchema):
    """
    Send OTP to the provided phone number.
    
    Args:
        payload: PhoneSchema containing the phone number
        
    Returns:
        Dict with status message
    """
    try:
        # Generate 6-digit OTP
        code = f"{random.randint(0, 999999):06d}"
        hashed = hashlib.sha256(code.encode()).hexdigest()
        expiry = int(time.time()) + 300  # 5 minutes expiry
        
        # Store OTP (in production, use Redis)
        OTP_STORE[payload.phone] = (hashed, expiry)
        
        # In production, integrate with SMS service here
        print(f"OTP for {payload.phone}: {code}")
        
        return {
            "status": "sent",
            "message": "OTP sent successfully",
            "expires_in": 300
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )

@router.post("/verify", response_model=Dict[str, Any])
async def verify_otp(payload: VerifySchema, db: Session = Depends(get_db)):
    """
    Verify OTP and authenticate user.
    
    Args:
        payload: VerifySchema containing phone, code, and optional full_name
        db: Database session
        
    Returns:
        Dict with access token and user info
    """
    try:
        phone, code = payload.phone, payload.code
        
        # Check if OTP exists
        stored = OTP_STORE.get(phone)
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No OTP requested for this phone number"
            )
        
        hashed, expiry = stored
        
        # Check if OTP expired
        if int(time.time()) > expiry:
            del OTP_STORE[phone]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired"
            )
        
        # Verify OTP
        if hashlib.sha256(code.encode()).hexdigest() != hashed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code"
            )
        
        # Clear OTP after successful verification
        del OTP_STORE[phone]
        
        # Find or create user
        user = db.query(User).filter_by(phone=phone).first()
        if not user:
            user = User(
                phone=phone,
                full_name=payload.full_name or "",
                roles=["borrower"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif payload.full_name and user.full_name != payload.full_name:
            # Update name if provided and different
            user.full_name = payload.full_name
            db.commit()
            db.refresh(user)
        
        # Generate JWT token
        now = int(time.time())
        claims = {
            "sub": str(user.id),
            "roles": user.roles or ["borrower"],
            "phone": user.phone,
            "scope": ["user"],
            "iat": now,
            "exp": now + (settings.JWT_EXPIRY_HOURS * 3600),
        }
        
        # Use development fallback if JWT keys not available
        if settings.ENVIRONMENT == "development" and not hasattr(settings, 'JWT_PRIVATE_KEY'):
            token = "dev-token"
        else:
            token = jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRY_HOURS * 3600,
            "user": {
                "id": str(user.id),
                "phone": user.phone,
                "full_name": user.full_name,
                "roles": user.roles
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

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
