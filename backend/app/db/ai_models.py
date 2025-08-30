"""
Database models for AI Engine data
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
# Base imported from app.db
from datetime import datetime
import uuid

from app.db import Base

class AIEvidence(Base):
    """AI Evidence uploaded by users for GreenScore calculation"""
    __tablename__ = "ai_evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # solar_panel_receipt, led_lighting, etc.
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_mb = Column(Float, nullable=False)
    mime_type = Column(String(100))
    description = Column(Text)
    sector = Column(String(50), nullable=False)  # salon, farmer, welding, etc.
    region = Column(String(50), default="Kenya")
    
    # Geolocation data
    latitude = Column(Float)
    longitude = Column(Float)
    location_accuracy = Column(Float)
    
    # Processing status
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ai_evidence")
    ocr_results = relationship("OCRResult", back_populates="ai_evidence", cascade="all, delete-orphan")
    cv_results = relationship("CVResult", back_populates="ai_evidence", cascade="all, delete-orphan")
    emission_results = relationship("EmissionResult", back_populates="ai_evidence", cascade="all, delete-orphan")
    greenscore_results = relationship("GreenScoreResult", back_populates="ai_evidence", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_evidence_user_id', 'user_id'),
        Index('idx_evidence_type', 'type'),
        Index('idx_evidence_sector', 'sector'),
        Index('idx_evidence_status', 'processing_status'),
        Index('idx_evidence_uploaded_at', 'uploaded_at'),
    )

class OCRResult(Base):
    """OCR processing results"""
    __tablename__ = "ocr_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("ai_evidence.id"), nullable=False)
    
    # OCR extracted data
    raw_text = Column(Text)
    vendor = Column(String(255))
    amount = Column(Float)
    currency = Column(String(10), default="KES")
    date = Column(DateTime)
    items = Column(ARRAY(String))
    
    # OCR quality metrics
    confidence = Column(Float)
    text_regions_count = Column(Integer)
    processing_method = Column(String(50))  # pytesseract, google_vision
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ai_evidence = relationship("AIEvidence", back_populates="ocr_results")

class CVResult(Base):
    """Computer Vision processing results"""
    __tablename__ = "cv_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("ai_evidence.id"), nullable=False)
    
    # CV detected objects/labels
    labels = Column(ARRAY(String))
    confidence_scores = Column(ARRAY(Float))
    bounding_boxes = Column(JSON)  # Array of bounding box coordinates
    
    # Equipment detection
    solar_panels_detected = Column(Boolean, default=False)
    led_lights_detected = Column(Boolean, default=False)
    meters_detected = Column(Boolean, default=False)
    equipment_count = Column(JSON)  # {"solar_panels": 2, "led_lights": 5}
    
    # Processing metadata
    processing_method = Column(String(50))  # opencv, google_vision
    confidence = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ai_evidence = relationship("AIEvidence", back_populates="cv_results")

class EmissionResult(Base):
    """CO2 emission calculation results"""
    __tablename__ = "emission_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("ai_evidence.id"), nullable=False)
    
    # Emission calculations
    co2_kg_total = Column(Float, nullable=False)
    co2_kg_components = Column(JSON)  # {"electricity": 45.2, "diesel": 12.8}
    emission_factors_used = Column(JSON)  # Factors and sources used
    
    # Calculation metadata
    method = Column(String(50))  # climatiq_api, local_factors
    confidence = Column(Float)
    data_completeness = Column(Float)
    
    # Features extracted
    features = Column(JSON)  # Structured features for ML
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ai_evidence = relationship("AIEvidence", back_populates="emission_results")

class GreenScoreResult(Base):
    """GreenScore calculation results"""
    __tablename__ = "greenscore_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("ai_evidence.id"), nullable=False)
    
    # Score components
    greenscore = Column(Integer, nullable=False)  # 0-100
    subscores = Column(JSON, nullable=False)  # {"energy": 25, "water": 15, ...}
    co2_saved_tonnes = Column(Float)
    
    # Confidence and quality
    confidence = Column(Float, nullable=False)
    explainers = Column(ARRAY(String))
    actions = Column(ARRAY(String))
    
    # Calculation metadata
    sector = Column(String(50), nullable=False)
    region = Column(String(50), default="Kenya")
    calculation_method = Column(String(50))
    provenance = Column(JSON)  # Full calculation audit trail
    
    # Status
    status = Column(String(20), default="provisional")  # provisional, final, under_review
    review_required = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    ai_evidence = relationship("AIEvidence", back_populates="greenscore_results")
    carbon_credits = relationship("CarbonCredit", back_populates="greenscore_result", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_greenscore_user_id', 'user_id'),
        Index('idx_greenscore_score', 'greenscore'),
        Index('idx_greenscore_sector', 'sector'),
        Index('idx_greenscore_created_at', 'created_at'),
    )

class CarbonCredit(Base):
    """Carbon credit calculations and tracking"""
    __tablename__ = "carbon_credits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("ai_evidence.id"), nullable=False)
    greenscore_result_id = Column(UUID(as_uuid=True), ForeignKey("greenscore_results.id"), nullable=False)
    
    # Credit details
    standard = Column(String(50), nullable=False)  # VCS, Gold_Standard, CDM
    tonnes_co2 = Column(Float, nullable=False)
    annual_tonnes = Column(Float, nullable=False)
    project_lifetime_years = Column(Integer, default=5)
    buffer_percentage = Column(Float, nullable=False)
    
    # Financial details
    gross_value_usd = Column(Float, nullable=False)
    net_value_usd = Column(Float, nullable=False)
    verification_cost_usd = Column(Float, default=0.0)
    pooling_fee_usd = Column(Float, default=0.0)
    
    # Status and approach
    status = Column(String(30), nullable=False)  # eligible, pooling_eligible, pending_verification, issued, retired
    approach = Column(String(20), nullable=False)  # individual, pooled
    pool_id = Column(String(100))  # If part of a pool
    
    # Verification and issuance
    additionality_verified = Column(Boolean, default=False)
    estimated_issuance = Column(DateTime)
    actual_issuance = Column(DateTime)
    registry_id = Column(String(100))  # ID in carbon registry
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    ai_evidence = relationship("AIEvidence")
    greenscore_result = relationship("GreenScoreResult", back_populates="carbon_credits")
    
    # Indexes
    __table_args__ = (
        Index('idx_carbon_credit_user_id', 'user_id'),
        Index('idx_carbon_credit_standard', 'standard'),
        Index('idx_carbon_credit_status', 'status'),
        Index('idx_carbon_credit_created_at', 'created_at'),
    )

class SectorBaseline(Base):
    """Sector baseline statistics for relative scoring"""
    __tablename__ = "sector_baselines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sector = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False)
    
    # Baseline statistics
    baseline_data = Column(JSON, nullable=False)  # All baseline metrics
    data_source = Column(String(200), nullable=False)
    sample_size = Column(Integer)
    
    # Validity period
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_sector_baseline_sector_region', 'sector', 'region'),
        Index('idx_sector_baseline_valid', 'valid_from', 'valid_until'),
    )

class ReviewCase(Base):
    """Human review cases for low confidence or high value claims"""
    __tablename__ = "review_cases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(100), unique=True, nullable=False)
    
    # Case details
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("ai_evidence.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    greenscore_result_id = Column(UUID(as_uuid=True), ForeignKey("greenscore_results.id"))
    
    # Review metadata
    status = Column(String(20), default="pending")  # pending, in_review, approved, rejected, needs_more_info
    priority = Column(String(10), default="medium")  # low, medium, high
    reasons = Column(ARRAY(String))  # Reasons for review
    confidence_score = Column(Float)
    
    # Review process
    assigned_reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewer_notes = Column(Text)
    review_decision = Column(String(20))  # approved, rejected, needs_revision
    review_completed_at = Column(DateTime)
    
    # SLA tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    review_deadline = Column(DateTime)
    escalation_level = Column(Integer, default=1)
    
    # AI result data (for review)
    ai_result_data = Column(JSON)
    
    # Relationships
    ai_evidence = relationship("AIEvidence")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
    greenscore_result = relationship("GreenScoreResult")
    
    # Indexes
    __table_args__ = (
        Index('idx_review_case_status', 'status'),
        Index('idx_review_case_priority', 'priority'),
        Index('idx_review_case_deadline', 'review_deadline'),
        Index('idx_review_case_created_at', 'created_at'),
    )

class AIProcessingLog(Base):
    """Audit log for AI processing requests"""
    __tablename__ = "ai_processing_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(100), unique=True, nullable=False)
    
    # Request details
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("ai_evidence.id"), nullable=False)
    
    # Processing details
    processing_method = Column(String(50))  # llm_orchestrated, deterministic
    processing_time_ms = Column(Integer)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    
    # AI model details
    ai_model_used = Column(String(50))  # gemini-2.0-flash-exp, deterministic
    function_calls_made = Column(ARRAY(String))
    confidence_final = Column(Float)
    
    # Results summary
    greenscore_achieved = Column(Integer)
    carbon_credits_calculated = Column(Integer)
    review_triggered = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    ai_evidence = relationship("AIEvidence")
    
    # Indexes
    __table_args__ = (
        Index('idx_ai_log_user_id', 'user_id'),
        Index('idx_ai_log_success', 'success'),
        Index('idx_ai_log_created_at', 'created_at'),
    )

class UserGreenScoreHistory(Base):
    """Historical GreenScore tracking for users"""
    __tablename__ = "user_greenscore_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Score snapshot
    greenscore = Column(Integer, nullable=False)
    subscores = Column(JSON, nullable=False)
    evidence_count = Column(Integer, default=0)
    total_co2_saved_tonnes = Column(Float, default=0.0)
    total_carbon_credits_value_usd = Column(Float, default=0.0)
    
    # Ranking and percentiles
    sector_percentile = Column(Float)
    regional_percentile = Column(Float)
    global_percentile = Column(Float)
    
    # Period details
    calculation_date = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_history_user_id', 'user_id'),
        Index('idx_user_history_date', 'calculation_date'),
        Index('idx_user_history_score', 'greenscore'),
    )
