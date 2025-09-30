"""
AI Engine API Endpoints
FastAPI router for AI-powered GreenScore and carbon credit calculations
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import get_db
from app.models import User, GreenScore, Evidence, BusinessProfile
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
    db: Session = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Process uploaded evidence file, create database record, and calculate GreenScore
    """
    try:
        # Validate file
        if file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=413, detail="File too large")

        # Create evidence record in database first
        evidence_uuid = uuid.uuid4()
        s3_key = f"evidence/{user.id}/{evidence_uuid}_{file.filename}"

        evidence = Evidence(
            id=evidence_uuid,
            user_id=user.id,
            s3_key=s3_key,
            status="processing"
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        # Save file temporarily using cross-platform temp directory
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
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

        # Update evidence status based on processing result
        if result.get("success"):
            evidence.status = "verified"

            # Create or update GreenScore if processing was successful
            if result.get("greenscore"):
                green_score = GreenScore(
                    user_id=user.id,
                    score=result.get("greenscore", 0),
                    subscores=result.get("subscores", {}),
                    explanation_json=result.get("explanations", [])
                )
                db.add(green_score)
        else:
            evidence.status = "rejected"

        db.commit()

        # Clean up temporary file
        try:
            os.unlink(file_path)
        except:
            pass

        return AIProcessingResponse(
            request_id=str(evidence.id),
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
    db: Session = Depends(get_db)
):
    """
    Get user's current GreenScore and breakdown from database
    """
    try:
        # Get the latest GreenScore from database
        latest_score = db.query(GreenScore).filter(
            GreenScore.user_id == user.id
        ).order_by(GreenScore.computed_at.desc()).first()

        if not latest_score:
            return {
                "user_id": str(user.id),
                "greenscore": None,
                "message": "No GreenScore available. Upload evidence to get started."
            }

        # Transform database format to frontend expected format
        subscores = latest_score.subscores or {}
        return {
            "user_id": str(user.id),
            "greenscore": latest_score.score,
            "subscores": {
                "energy_efficiency": subscores.get("energy", 0),
                "renewable_energy": subscores.get("energy", 0),  # Use energy as fallback
                "waste_management": subscores.get("waste", 0),
                "water_conservation": subscores.get("water", 0)
            },
            "confidence": 0.8,  # Default confidence
            "last_updated": latest_score.computed_at.isoformat() if latest_score.computed_at else None,
            "sector_percentile": 75,  # TODO: Calculate based on sector data
            "explainers": latest_score.explanation_json or [],
            "actions": []  # TODO: Connect to recommendations
        }

    except Exception as e:
        logger.error(f"Error getting current GreenScore: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function to get AI service
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
        history = await ai_service.get_user_greenscore_history(str(user.id), months)
        
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
        portfolio = await ai_service.get_carbon_credits_portfolio(str(user.id))
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
    Get personalized carbon credit recommendations using Gemini AI
    """
    try:
        # Get user's current GreenScore and business profile
        latest_score = db.query(GreenScore).filter(
            GreenScore.user_id == user.id
        ).order_by(GreenScore.computed_at.desc()).first()

        # Get user's business profile
        business_profile = db.query(BusinessProfile).filter(
            BusinessProfile.user_id == user.id
        ).first()

        # Get user's evidence history
        evidence_count = db.query(Evidence).filter(
            Evidence.user_id == user.id
        ).count()

        # Generate personalized recommendations using Gemini
        recommendations = await generate_personalized_recommendations(
            user, latest_score, business_profile, evidence_count
        )

        return {
            "user_id": str(user.id),
            "recommendations": recommendations,
            "pooling_opportunities": {
                "available": True,
                "pool_name": "Kenya_SME_Pool_VCS",
                "min_participation": 0.1,
                "estimated_timeline_months": 3
            }
        }

    except Exception as e:
        logger.error(f"Error getting carbon credit recommendations: {str(e)}")
        # Fallback to static recommendations if Gemini fails
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


@router.get("/sector/analytics")
async def get_sector_analytics_alias(
    sector: str,
    region: str = "Kenya",
    user: User = Depends(get_current_user)
):
    """Alias route to match frontend expectations (legacy contract)."""
    return await get_sector_analytics(sector=sector, region=region, user=user)

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

async def generate_personalized_recommendations(
    user: User,
    latest_score: Optional[GreenScore],
    business_profile: Optional[BusinessProfile],
    evidence_count: int
) -> List[Dict[str, Any]]:
    """Generate personalized recommendations using Gemini AI"""
    try:
        import google.generativeai as genai
        from app.config import settings

        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Build user context
        current_score = latest_score.score if latest_score else 50
        subscores = latest_score.subscores if latest_score else {}
        business_type = business_profile.business_type if business_profile else "unknown"
        business_name = business_profile.business_name if business_profile else "Business"
        location = business_profile.location if business_profile else "Kenya"

        # Create personalized prompt
        prompt = f"""
        You are an AI sustainability advisor for SMEs in Kenya. Generate 3-4 personalized carbon reduction recommendations for this business:

        Business Profile:
        - Name: {business_name}
        - Type: {business_type}
        - Location: {location}
        - Current GreenScore: {current_score}/100
        - Energy Score: {subscores.get('energy', 'N/A')}
        - Water Score: {subscores.get('water', 'N/A')}
        - Waste Score: {subscores.get('waste', 'N/A')}
        - Evidence uploaded: {evidence_count} files

        Generate specific, actionable recommendations that are:
        1. Relevant to their business type
        2. Appropriate for Kenya's context
        3. Focus on areas where their scores are lowest
        4. Include realistic cost estimates and payback periods

        Return ONLY a JSON array with this exact format:
        [
          {{
            "action": "Specific action to take",
            "estimated_co2_tonnes": 0.8,
            "estimated_value_usd": 15.20,
            "payback_period_months": 6,
            "priority": "high"
          }}
        ]
        """

        # Generate recommendations
        response = model.generate_content(prompt)

        # Parse JSON response
        import json
        try:
            recommendations = json.loads(response.text.strip())
            # Ensure we have valid recommendations
            if isinstance(recommendations, list) and len(recommendations) > 0:
                return recommendations[:4]  # Limit to 4 recommendations
        except json.JSONDecodeError:
            logger.warning("Failed to parse Gemini JSON response")

    except Exception as e:
        logger.error(f"Error generating Gemini recommendations: {str(e)}")

    # Fallback to sector-specific recommendations
    sector = business_profile.business_type if business_profile else "general"
    return get_fallback_recommendations(sector, current_score)

def get_fallback_recommendations(sector: str, current_score: int) -> List[Dict[str, Any]]:
    """Get fallback recommendations based on sector and score"""
    if sector == "agriculture":
        return [
            {
                "action": "Install drip irrigation system",
                "estimated_co2_tonnes": 1.2,
                "estimated_value_usd": 21.60,
                "payback_period_months": 8,
                "priority": "high"
            },
            {
                "action": "Use solar-powered water pumps",
                "estimated_co2_tonnes": 0.8,
                "estimated_value_usd": 14.40,
                "payback_period_months": 12,
                "priority": "medium"
            }
        ]
    elif sector == "beauty":
        return [
            {
                "action": "Switch to LED lighting",
                "estimated_co2_tonnes": 0.6,
                "estimated_value_usd": 10.80,
                "payback_period_months": 6,
                "priority": "high"
            },
            {
                "action": "Use eco-friendly packaging",
                "estimated_co2_tonnes": 0.4,
                "estimated_value_usd": 7.20,
                "payback_period_months": 10,
                "priority": "medium"
            }
        ]
    else:
        return [
            {
                "action": "Install LED lighting",
                "estimated_co2_tonnes": 0.6,
                "estimated_value_usd": 10.80,
                "payback_period_months": 8,
                "priority": "high"
            },
            {
                "action": "Implement waste sorting",
                "estimated_co2_tonnes": 0.3,
                "estimated_value_usd": 5.40,
                "payback_period_months": 6,
                "priority": "medium"
            }
        ]
