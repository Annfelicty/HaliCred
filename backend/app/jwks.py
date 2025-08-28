"""
JWKS endpoint module.

This module provides a JSON Web Key Set (JWKS) endpoint for public key retrieval.
It is used for JWT verification by clients.
"""

import json
from fastapi import APIRouter, Response
from pathlib import Path
from jose import jwk

router = APIRouter()

PUBLIC_KEY_PATH = Path("jwtRS256.key.pub")

@router.get("/.well-known/jwks.json")
def jwks():
    public_key = PUBLIC_KEY_PATH.read_text()
    jwk_data = jwk.construct(public_key, algorithm="RS256").to_dict()
    # JWKS format
    jwks = {"keys": [jwk_data]}
    return Response(content=json.dumps(jwks), media_type="application/json")
