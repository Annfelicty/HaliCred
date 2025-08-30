"""
Database models module.

This module defines the SQLAlchemy ORM models for the application.
It includes models for User, BusinessProfile, LoanApplication, Verification, GreenScore, and AuditLog.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Numeric, Enum, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, declarative_base
from geoalchemy2 import Geometry
from uuid import uuid4
import sqlalchemy as sa

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    phone = Column(String(32), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    roles = Column(ARRAY(String), server_default=text("ARRAY['borrower']::varchar[]"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())

    profile = relationship("BusinessProfile", back_populates="user", uselist=False)
    loans = relationship("LoanApplication", back_populates="user")
    verifications = relationship("Verification", back_populates="user")
    scores = relationship("GreenScore", back_populates="user")
    evidence = relationship("Evidence", back_populates="user")


class BusinessProfile(Base):
    __tablename__ = "business_profiles"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    business_type = Column(Enum("agriculture","beauty","welding","other", name="business_type_enum"))
    business_name = Column(String(160))
    location = Column(Geometry(geometry_type="POINT", srid=4326))
    consents = Column(JSONB)
    user = relationship("User", back_populates="profile")


class LoanApplication(Base):
    __tablename__ = "loan_applications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    amount = Column(Numeric(14,2))
    tenor_months = Column(Integer)
    quoted_rate = Column(Numeric(6,4))
    greenscore_snapshot = Column(JSONB)
    status = Column(Enum("draft","submitted","approved","declined","disbursed", name="loan_status"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())
    user = relationship("User", back_populates="loans")


class Verification(Base):
    __tablename__ = "verifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    kind = Column(Enum("receipt","photo","geo","transaction","telemetry", name="verification_kind"))
    status = Column(Enum("pending","processing","verified","rejected", name="verification_status"), index=True)
    s3_key = Column(String, nullable=False)
    receipt_hash = Column(String(64))
    parsed = Column(JSONB)
    result = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())
    user = relationship("User", back_populates="verifications")


class GreenScore(Base):
    __tablename__ = "greenscores"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    score = Column(Integer, nullable=False)
    subscores = Column(JSONB)
    explanation_json = Column(JSONB)
    computed_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())
    user = relationship("User", back_populates="scores")


class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    s3_key = Column(String, nullable=False)
    status = Column(Enum("pending", "processing", "verified", "rejected", name="evidence_status"), index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())
    user = relationship("User", back_populates="evidence")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(80))
    entity = Column(String(80))
    entity_id = Column(UUID(as_uuid=True))
    payload = Column(JSONB)
    audit_hmac = Column(String(64))
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())
