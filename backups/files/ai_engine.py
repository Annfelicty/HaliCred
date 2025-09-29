"""
AI Engine API Endpoints
FastAPI router for AI-powered GreenScore and carbon credit calculations
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import get_db
from app.models import User
from app.auth import get_current_user
from app.ai import (
    AIOrchestrator, ConfidenceManager, SectorBaselineService, 
    ScoreComputer, CarbonCreditAggregator
)
from app.ai.models import AIOrchestrationRequest, EvidenceData
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

# Initialize AI services
ai_config = {
    'gemini_api_key': os.getenv("GEMINI_API_KEY", ""),
    'google_vision_api_key': os.getenv("GOOGLE_VISION_API_KEY", ""),
    'climatiq_api_key': os.getenv("CLIMATIQ_API_KEY", "")
}
ai_orchestrator = AIOrchestrator(ai_config)
confidence_manager = ConfidenceManager()

router = APIRouter(prefix="/ai", tags=["AI Engine"])

# Helper function to get AI service
def get_ai_service(db: Session = Depends(get_db)) -> AIService:
    """Dependency to get AI service instance"""
    return AIService(db)

# Request/Response Models
class EvidenceUploadRequest(BaseModel):
    sector: str
    region: str = "Kenya"
    evidence_type: str
    description: Optional[str] = None

class AIProcessingResponse(BaseModel):
    request_id: str
    status: str
    message: str
    processing_time_ms: Optional[int] = None
    greenscore: Optional[int] = None
    confidence: Optional[float] = None
    carbon_credits: Optional[List[Dict[str, Any]]] = None
    review_required: Optional[bool] = None

class ScoreHistoryResponse(BaseModel):
    user_id: str
    scores: List[Dict[str, Any]]
    trend: str
    improvement_suggestions: List[str]

# Core AI Processing Endpoints

@router.post("/evidence/process", response_model=AIProcessingResponse)
async def process_evidence(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sector: str = Form(...),
    region: str = Form("Kenya"),
    evidence_type: str = Form(...),
    description: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Process uploaded evidence file and calculate GreenScore
    """
    try:
        # Validate file
        if file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=413, detail="File too large")
        
        # Save file temporarily
        file_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process evidence using AI service
        result = await ai_service.process_evidence_request(
            user_id=str(user.id),
            file_path=file_path,
            file_name=file.filename,
            file_size_mb=len(content) / (1024 * 1024),
            evidence_type=evidence_type,
            sector=sector,
            region=region,
            description=description
        )
        
        return AIProcessingResponse(
            request_id=result.get("evidence_id", "unknown"),
            status="completed" if result.get("success") else "failed",
            message="Processing completed successfully" if result.get("success") else "Processing failed",
            processing_time_ms=result.get("processing_time_ms"),
            greenscore=result.get("greenscore"),
            confidence=result.get("confidence"),
            carbon_credits=[],  # Will be populated by service
            review_required=result.get("review_required", False)
        )
        
    except Exception as e:
        logger.error(f"Error processing evidence: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/processing-status/{request_id}")
async def get_processing_status(
    request_id: str,
    user: User = Depends(get_current_user)
):
    """
    Get status of evidence processing request
    """
    try:
        # In a real system, this would query a processing status database
        # For now, return a mock response
        return {
            "request_id": request_id,
            "status": "completed",
            "progress": 100,
            "message": "Processing completed successfully",
            "estimated_completion": None
        }
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# GreenScore Management

@router.get("/greenscore/current")
async def get_current_greenscore(
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get user's current GreenScore and breakdown
    """
    try:
        current_score = ai_service.get_user_greenscore_current(str(user.id))
        
        if not current_score:
            return {
                "user_id": str(user.id),
                "greenscore": None,
                "message": "No GreenScore available. Upload evidence to get started."
            }
        
        return current_score
        
    except Exception as e:
        logger.error(f"Error getting current GreenScore: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function to get AI service
def get_ai_service(db: Session = Depends(get_db)) -> AIService:
    """Dependency to get AI service instance"""
    return AIService(db)

@router.get("/greenscore/history", response_model=ScoreHistoryResponse)
async def get_greenscore_history(
    months: int = 12,
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get user's GreenScore history and trends
    """
    try:
        history = ai_service.get_user_greenscore_history(str(user.id), months)
        
        # Calculate trend
        trend = "stable"
        if len(history) >= 2:
            recent_avg = sum(h["greenscore"] for h in history[:3]) / min(3, len(history))
            older_avg = sum(h["greenscore"] for h in history[-3:]) / min(3, len(history))
            if recent_avg > older_avg + 5:
                trend = "improving"
            elif recent_avg < older_avg - 5:
                trend = "declining"
        
        return ScoreHistoryResponse(
            user_id=str(user.id),
            scores=history,
            trend=trend,
            improvement_suggestions=[
                "Upload more recent evidence",
                "Consider renewable energy upgrades",
                "Implement energy efficiency measures"
            ]
        )
    except Exception as e:
        logger.error(f"Error getting GreenScore history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Carbon Credits Management

@router.get("/carbon-credits/portfolio")
async def get_carbon_credits_portfolio(
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get user's carbon credits portfolio
    """
    try:
        portfolio = ai_service.get_user_carbon_credits_portfolio(str(user.id))
        return portfolio
    except Exception as e:
        logger.error(f"Error getting carbon credits portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/carbon-credits/recommendations")
async def get_carbon_credit_recommendations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized carbon credit recommendations
    """
    try:
        return {
            "user_id": str(user.id),
            "recommendations": [
                {
                    "action": "Install LED lighting",
                    "estimated_co2_tonnes": 0.6,
                    "estimated_value_usd": 10.80,
                    "payback_period_months": 8,
                    "priority": "high"
                },
                {
                    "action": "Implement drip irrigation",
                    "estimated_co2_tonnes": 1.2,
                    "estimated_value_usd": 21.60,
                    "payback_period_months": 12,
                    "priority": "medium"
                }
            ],
            "pooling_opportunities": {
                "available": True,
                "pool_name": "Kenya_SME_Pool_VCS",
                "min_participation": 0.1,
                "estimated_timeline_months": 3
            }
        }
    except Exception as e:
        logger.error(f"Error getting carbon credit recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Sector Analytics

@router.get("/analytics/sector/{sector}")
async def get_sector_analytics(
    sector: str,
    region: str = "Kenya",
    user: User = Depends(get_current_user)
):
    """
    Get sector-specific analytics and benchmarks
    """
    try:
        baseline_service = ai_orchestrator.sector_baseline
        baseline = await baseline_service.get_baseline(sector, region)
        
        return {
            "sector": sector,
            "region": region,
            "baseline_stats": baseline.baseline,
            "user_percentile": 65,  # Mock user percentile
            "improvement_areas": [
                "Energy efficiency",
                "Renewable energy adoption",
                "Waste management"
            ],
            "top_performers": {
                "average_greenscore": 78,
                "common_practices": [
                    "Solar panel installation",
                    "LED lighting upgrade",
                    "Water recycling systems"
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error getting sector analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin and Review Endpoints

@router.get("/admin/review-queue")
async def get_review_queue(
    priority: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    Get human review queue (admin only)
    """
    try:
        # Check admin permissions (simplified)
        if "admin" not in getattr(user, 'roles', []):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        queue_summary = confidence_manager.get_review_queue_summary()
        
        return {
            "queue_summary": queue_summary,
            "pending_reviews": [
                {
                    "case_id": "review_001",
                    "user_id": "user_123",
                    "evidence_type": "solar_panel_receipt",
                    "confidence": 0.45,
                    "reasons": ["low_confidence", "high_value_claim"],
                    "priority": "high",
                    "created_at": "2024-08-30T10:00:00Z"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error getting review queue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/review/{case_id}/decision")
async def submit_review_decision(
    case_id: str,
    decision: str,
    notes: str,
    user: User = Depends(get_current_user)
):
    """
    Submit human review decision
    """
    try:
        # Check admin permissions
        if "admin" not in getattr(user, 'roles', []):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # In a real system, update the review case in database
        return {
            "case_id": case_id,
            "decision": decision,
            "reviewer_id": str(user.id),
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Error submitting review decision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper Functions

async def process_evidence_async(ai_request: AIOrchestrationRequest):
    """Background task for processing large evidence files"""
    try:
        result = await ai_orchestrator.process_request(ai_request)
        # In a real system, store result in database and notify user
        logger.info(f"Async processing completed for evidence {ai_request.evidence.evidence_id}")
    except Exception as e:
        logger.error(f"Async processing failed for evidence {ai_request.evidence.evidence_id}: {str(e)}")

async def get_user_history(user_id: str, db: Session) -> Dict[str, Any]:
    """Get user history for confidence assessment"""
    # Mock user history - in real system, query database
    return {
        "account_age_days": 45,
        "previous_submissions": 3,
        "approval_rate": 0.85,
        "fraud_flags": 0,
        "phone_verified": True,
        "business_registered": True,
        "submissions_last_24h": 1,
        "similar_evidence_count": 0,
        "location_inconsistency": False
    }

async def get_sector_context(sector: str) -> Dict[str, Any]:
    """Get sector context for confidence assessment"""
    # Mock sector context - in real system, query analytics database
    return {
        "average_greenscore": 58,
        "std_greenscore": 18,
        "average_credit_value": 35.0,
        "participant_count": 1250
    }
