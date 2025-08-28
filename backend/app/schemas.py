"""
Pydantic schemas module.

This module defines the Pydantic models used for data validation and serialization.
It includes schemas for Phone, Verify, Consent, Profile, LoanQuote, LoanApply, and Decision.
"""

from pydantic import BaseModel
from typing import Optional

class PhoneSchema(BaseModel):
    phone: str

class VerifySchema(BaseModel):
    phone: str
    code: str
    full_name: Optional[str] = None

class ConsentSchema(BaseModel):
    mpesa: bool
    geo: bool
    documents: bool

class ProfileSchema(BaseModel):
    business_type: Optional[str]
    business_name: Optional[str]
    location: Optional[str]

class LoanQuoteSchema(BaseModel):
    amount: float
    tenor: int

class LoanApplySchema(BaseModel):
    amount: float
    tenor: int

class DecisionSchema(BaseModel):
    decision: str
    reason: Optional[str] = None
