"""
Pydantic schemas module.

This module defines the Pydantic models used for data validation and serialization.
It includes schemas for Phone, Verify, Consent, Profile, LoanQuote, LoanApply, and Decision.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, EmailStr, model_validator

class OTPRequestSchema(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

    @model_validator(mode="after")
    def validate_contact(cls, values: "OTPRequestSchema") -> "OTPRequestSchema":
        phone, email = values.phone, values.email
        if not phone and not email:
            raise ValueError("Either phone or email must be provided")
        if phone and email:
            raise ValueError("Provide only one contact method")
        return values

class VerifySchema(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    code: str
    full_name: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_contact(cls, values: "VerifySchema") -> "VerifySchema":
        phone, email = values.phone, values.email
        if not phone and not email:
            raise ValueError("Either phone or email must be provided")
        if phone and email:
            raise ValueError("Provide only one contact method")
        return values

class PasswordLoginSchema(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

    @model_validator(mode="after")
    def validate_identifier(cls, values: "PasswordLoginSchema") -> "PasswordLoginSchema":
        phone, email = values.phone, values.email
        if not phone and not email:
            raise ValueError("Either phone or email must be provided")
        if phone and email:
            raise ValueError("Provide only one identifier")
        return values

class ConsentSchema(BaseModel):
    mpesa: bool
    geo: bool
    documents: bool

class ProfileSchema(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    business_type: Optional[str] = None
    business_name: Optional[str] = None
    location: Optional[str] = None

class LoanQuoteSchema(BaseModel):
    amount: float
    tenor: int

class LoanApplySchema(BaseModel):
    amount: float
    tenor: int
    purpose: Optional[str] = None


class LoanRecordSchema(BaseModel):
    id: str
    amount: float
    tenor: int
    status: str
    quoted_rate: Optional[float] = None
    purpose: Optional[str] = None
    created_at: Optional[int] = None
    greenscore_snapshot: Optional[Dict[str, Any]] = None

class DecisionSchema(BaseModel):
    decision: str
    reason: Optional[str] = None


class OTPSendResponse(BaseModel):
    status: Literal["sent"]
    message: str
    expires_in: int
