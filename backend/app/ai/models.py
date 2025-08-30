"""
AI Engine Data Models
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class EvidenceData(BaseModel):
    """Raw evidence data from user upload"""
    evidence_id: str
    user_id: str
    type: Literal["receipt", "photo", "invoice", "meter_reading"]
    file_url: str
    timestamp: datetime
    geo: Optional[Dict[str, float]] = None  # {"lat": -1.2921, "lon": 36.8219}
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OCRResult(BaseModel):
    """OCR extraction results"""
    vendor: Optional[str] = None
    amount_ksh: Optional[float] = None
    date: Optional[str] = None
    items: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    raw_text: str = ""

class CVResult(BaseModel):
    """Computer Vision analysis results"""
    labels: List[str] = Field(default_factory=list)
    caption: str = ""
    confidence: float = 0.0
    detected_objects: List[Dict[str, Any]] = Field(default_factory=list)

class ProcessedEvidence(BaseModel):
    """Processed evidence with OCR and CV results"""
    evidence_id: str
    user_id: str
    type: str
    ocr: OCRResult
    cv: CVResult
    geo: Optional[Dict[str, float]] = None
    timestamp: datetime
    processing_confidence: float = 0.0

class EmissionFeatures(BaseModel):
    """Features for emission calculation"""
    kwh_saved: Optional[float] = None
    diesel_liters_avoided: Optional[float] = None
    plastic_kg_recycled: Optional[float] = None
    water_m3_saved: Optional[float] = None
    solar_kwh_generated: Optional[float] = None
    appliance_efficiency_gain: Optional[float] = None

class EmissionResult(BaseModel):
    """CO2 emission calculation result"""
    evidence_id: str
    co2_kg_components: Dict[str, float] = Field(default_factory=dict)
    co2_kg_total: float = 0.0
    method: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0

class SectorBaseline(BaseModel):
    """Sector baseline statistics"""
    sector: str
    region: str = "Kenya"
    baseline: Dict[str, float] = Field(default_factory=dict)
    data_source: str = ""
    last_updated: datetime = Field(default_factory=datetime.now)

class GreenScoreResult(BaseModel):
    """Final GreenScore computation result"""
    user_id: str
    evidence_id: str
    greenscore: int
    subscores: Dict[str, float] = Field(default_factory=dict)
    co2_saved_tonnes: float = 0.0
    confidence: float = 0.0
    explainers: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class CarbonCredit(BaseModel):
    """Carbon credit calculation"""
    user_id: str
    evidence_ids: List[str]
    verified_co2_tonnes: float
    credits_eligible: float
    buffer_applied: float = 0.1  # 10% buffer
    status: Literal["pending", "verified", "issued"] = "pending"
    created_at: datetime = Field(default_factory=datetime.now)

class AIOrchestrationRequest(BaseModel):
    """Request for AI orchestration"""
    evidence: ProcessedEvidence
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    sector: str
    region: str = "Kenya"

class AIOrchestrationResult(BaseModel):
    """AI orchestration final result"""
    evidence_id: str
    user_id: str
    greenscore: int
    subscores: Dict[str, float]
    co2_saved_tonnes: float
    confidence: float
    explainers: List[str]
    actions: List[str]
    carbon_credits: Optional[CarbonCredit] = None
    requires_human_review: bool = False
    provenance: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
