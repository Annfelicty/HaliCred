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
from app.models import User, GreenScore, BusinessProfile, Evidence
from app.db.ai_models import AIEvidence
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
            logger.info(f"✅ Evidence {evidence.id} status updated to 'verified'")

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
            logger.warning(f"⚠️ Evidence {evidence.id} status updated to 'rejected'")

        db.commit()
        logger.info(f"💾 Evidence status committed to database: {evidence.status}")

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

        # Get user's evidence history with details
        evidence_list = db.query(AIEvidence).filter(
            AIEvidence.user_id == user.id
        ).order_by(AIEvidence.uploaded_at.desc()).limit(10).all()

        evidence_count = len(evidence_list)

        # Extract evidence summary (what they've already done)
        evidence_summary = []
        for ev in evidence_list:
            if ev.description:
                evidence_summary.append(ev.description[:100])
            elif ev.file_name:
                # Extract hints from filename
                fname_lower = ev.file_name.lower()
                if 'solar' in fname_lower:
                    evidence_summary.append("Solar installation")
                elif 'led' in fname_lower or 'light' in fname_lower:
                    evidence_summary.append("LED lighting")
                elif 'water' in fname_lower or 'irrigation' in fname_lower:
                    evidence_summary.append("Water system")
                elif 'waste' in fname_lower or 'recycle' in fname_lower:
                    evidence_summary.append("Waste management")

        # Generate personalized recommendations using Gemini AI
        recommendations = await generate_personalized_recommendations(
            user, latest_score, business_profile, evidence_count, evidence_summary
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

# Recommendations cache (1 hour TTL)
RECOMMENDATIONS_CACHE: Dict[str, tuple[List[Dict[str, Any]], float]] = {}
CACHE_TTL = 3600  # 1 hour in seconds

try:
    import redis
    from app.config import settings
    recommendations_redis = redis.Redis.from_url(
        settings.CELERY_BROKER_URL,
        decode_responses=False,  # We'll handle JSON manually
        socket_connect_timeout=5,
        socket_timeout=5
    )
    recommendations_redis.ping()
    logger.info("Recommendations cache using Redis")
except Exception as e:
    logger.warning(f"Redis unavailable for recommendations cache, using memory: {e}")
    recommendations_redis = None

async def generate_personalized_recommendations(
    user: User,
    latest_score: Optional[GreenScore],
    business_profile: Optional[BusinessProfile],
    evidence_count: int,
    evidence_summary: List[str] = []
) -> List[Dict[str, Any]]:
    """Generate personalized recommendations using Gemini AI with 1-hour caching"""
    import json
    import time

    # Build cache key using hourly time bucket (cache persists for 1 hour regardless of evidence changes)
    hour_bucket = int(time.time() // 3600)  # 1-hour time buckets
    cache_key = f"recommendations:{user.id}:{hour_bucket}"

    # Try to get from cache (Redis first, then memory)
    try:
        if recommendations_redis:
            cached_data = recommendations_redis.get(cache_key)
            if cached_data:
                logger.info(f"✅ Returning cached recommendations for user {user.id}")
                return json.loads(cached_data)
        else:
            # Memory cache fallback
            if cache_key in RECOMMENDATIONS_CACHE:
                cached_recs, timestamp = RECOMMENDATIONS_CACHE[cache_key]
                if time.time() - timestamp < CACHE_TTL:
                    logger.info(f"✅ Returning cached recommendations (memory) for user {user.id}")
                    return cached_recs
                else:
                    # Expired, remove from cache
                    del RECOMMENDATIONS_CACHE[cache_key]
    except Exception as e:
        logger.warning(f"Cache retrieval failed: {e}")

    # Cache miss - generate new recommendations
    try:
        import google.generativeai as genai
        from app.config import settings

        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Extract user context
        current_score = latest_score.score if latest_score else 0
        subscores = latest_score.subscores if latest_score else {}
        business_type = business_profile.business_type if business_profile else "unknown"
        business_name = business_profile.business_name if business_profile else "Business"
        location = business_profile.location if business_profile else "Kenya"

        # Identify weak areas for targeted recommendations
        weak_areas = []
        for pillar, score in subscores.items():
            if score < 30:
                weak_areas.append(pillar)

        engagement_level = "new" if evidence_count == 0 else ("low" if evidence_count < 3 else "active")

        # Build evidence history context
        evidence_context = "None yet - this is their first time" if not evidence_summary else "\n".join([f"  • {ev}" for ev in evidence_summary[:5]])

        # Create enhanced, HYPERAWARE user-centric prompt
        prompt = f"""
        You are HaliCred's AI sustainability advisor specializing in Kenyan SMEs. Your role is to recommend high-impact carbon credit opportunities that are practical and profitable.

        BUSINESS CONTEXT:
        - Name: {business_name}
        - Sector: {business_type}
        - Region: {location}, Kenya
        - Current GreenScore: {current_score}/100 (0-30: Beginner, 31-60: Intermediate, 61-100: Advanced)
        - Engagement Level: {engagement_level} ({evidence_count} evidence submissions)

        ACTIONS ALREADY TAKEN (do NOT repeat these):
{evidence_context}

        PERFORMANCE BREAKDOWN:
        - Energy Efficiency: {subscores.get('energy_efficiency', 0)}/100
        - Water Conservation: {subscores.get('water_conservation', 0)}/100
        - Waste Management: {subscores.get('waste_management', 0)}/100
        - Sustainable Sourcing: {subscores.get('sustainable_sourcing', 0)}/100
        - Carbon Reduction: {subscores.get('carbon_reduction', 0)}/100

        WEAK AREAS (priority): {', '.join(weak_areas) if weak_areas else 'None - all areas need development'}

        YOUR TASK:
        Generate 4 SPECIFIC, ACTIONABLE carbon credit opportunities ranked by:
        1. **Impact on weak areas** (highest priority)
        2. **ROI for {business_type} businesses in Kenya**
        3. **Feasibility at GreenScore level {current_score}**
        4. **Carbon credit monetization potential**

        CRITICAL REQUIREMENTS:
        - **DO NOT repeat actions they've already taken** (listed above)
        - Recommend NEXT STEPS that build on their current progress
        - If they have solar, suggest battery storage or expanding capacity
        - If they have LED, suggest solar to power them or smart controls
        - Match recommendations to their current capability (don't suggest solar farms if they're at 10/100)
        - Use Kenya-specific costs (KES converted to USD at 150:1)
        - Include exact equipment/actions, not generic advice
        - Prioritize quick wins for beginners (score < 30)
        - For advanced users (score > 60), suggest certification/aggregation opportunities

        CONTEXT AWARENESS:
        - {business_type} sector typically has high potential in: {"solar energy, drip irrigation" if business_type == "agriculture" else "LED lighting, efficient motors" if business_type == "manufacturing" else "waste reduction, energy efficiency"}
        - Common barriers: upfront cost, technical know-how
        - Local suppliers: Available for solar, biogas, LED, water systems

        CARBON CREDIT VALUE:
        - Current price: ~$15-25 per tonne CO2e
        - Include GreenScore impact: +5 to +20 points per action

        Return ONLY a JSON array (no markdown, no explanations):
        [
          {{
            "action": "[Exact action with equipment/vendor if relevant] e.g., 'Install 5kW solar system from Chloride Exide Kenya'",
            "estimated_co2_tonnes": [Annual tonnes saved],
            "estimated_value_usd": [Carbon credits value at $20/tonne],
            "payback_period_months": [ROI from energy savings + carbon credits],
            "priority": "high|medium|low",
            "greenscore_impact": "+[5-20] points",
            "pillar": "[energy_efficiency|water_conservation|waste_management|sustainable_sourcing|carbon_reduction]"
          }}
        ]
        """

        # Generate recommendations
        response = model.generate_content(prompt)

        # Parse JSON response
        import json
        import re
        try:
            response_text = response.text.strip()

            # Strip markdown code fences if present (Gemini wraps JSON in ```json ... ```)
            if response_text.startswith("```"):
                # Remove ```json at start
                response_text = re.sub(r'^```(?:json|JSON)?\s*\n?', '', response_text)
                # Remove ``` at end
                response_text = re.sub(r'\n?\s*```\s*$', '', response_text)
                response_text = response_text.strip()

            recommendations = json.loads(response_text)
            # Ensure we have valid recommendations
            if isinstance(recommendations, list) and len(recommendations) > 0:
                limited_recs = recommendations[:4]  # Limit to 4 recommendations

                # Store in cache for 1 hour
                try:
                    if recommendations_redis:
                        recommendations_redis.setex(
                            cache_key,
                            CACHE_TTL,
                            json.dumps(limited_recs)
                        )
                    else:
                        RECOMMENDATIONS_CACHE[cache_key] = (limited_recs, time.time())
                    logger.info(f"🔄 Cached new recommendations for user {user.id}")
                except Exception as cache_err:
                    logger.warning(f"Failed to cache recommendations: {cache_err}")

                return limited_recs
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini JSON response: {e}")
            logger.debug(f"Response text (first 200 chars): {response.text[:200]}")

    except Exception as e:
        logger.error(f"Error generating Gemini recommendations: {str(e)}")

    # Fallback to sector-specific recommendations
    sector = business_profile.business_type if business_profile else "general"
    fallback_recs = get_fallback_recommendations(sector, current_score)

    # Cache fallback too (shorter TTL - 5 minutes)
    try:
        if recommendations_redis:
            recommendations_redis.setex(cache_key, 300, json.dumps(fallback_recs))
        else:
            RECOMMENDATIONS_CACHE[cache_key] = (fallback_recs, time.time())
    except Exception:
        pass

    return fallback_recs

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
