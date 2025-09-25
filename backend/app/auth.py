"""
Authentication utilities
Shared authentication functions to avoid circular imports
"""
import os
from pathlib import Path
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db import get_db
from app.models import User
from app.config import settings

security = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    algorithm = settings.JWT_ALGORITHM.upper()
    if algorithm.startswith("HS"):
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )

    key_path = Path(settings.JWT_PUBLIC_KEY_PATH)
    if key_path.exists():
        public_key = key_path.read_text()
    else:
        # Development/testing fallback when key pair isn't provisioned
        public_key = settings.SECRET_KEY
    return jwt.decode(
        token,
        public_key,
        algorithms=[settings.JWT_ALGORITHM],
        options={"verify_aud": False},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Resolve the authenticated user from a bearer token."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
        )

    token = credentials.credentials
    try:
        payload = _decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing user ID")
        user_uuid = UUID(user_id)
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
