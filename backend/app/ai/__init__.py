"""
HaliCred 
AI Engine Package
Provides AI-powered GreenScore calculation and carbon credit assessment
"""

# Import main orchestrator
from .orchestrator import AIOrchestrator

# Import microservices
from .evidence_processor import EvidenceProcessor
from .emission_calculator import EmissionCalculator
from .score_computer import ScoreComputer
from .sector_baseline import SectorBaselineService
from .carbon_credit import CarbonCreditAggregator
from .confidence_manager import ConfidenceManager

# Import data models
from .models import (
    Evidence, OCRResult, CVResult, EmissionResult, 
    GreenScoreResult, CarbonCredit, AIRequest, AIResult
)

__all__ = [
    "AIOrchestrator",
    "EvidenceProcessor", 
    "EmissionCalculator",
    "ScoreComputer",
    "SectorBaselineService",
    "CarbonCreditAggregator",
    "ConfidenceManager",
    "Evidence", "OCRResult", "CVResult", "EmissionResult", 
    "GreenScoreResult", "CarbonCredit", "AIRequest", "AIResult"
]
