"""
AI Service - Database integration layer for AI engine
Handles storing and retrieving AI processing results
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.ai_models import (
    AIEvidence, OCRResult, CVResult, EmissionResult,
    GreenScoreResult, CarbonCredit, SectorBaseline,
    ReviewCase, AIProcessingLog, UserGreenScoreHistory
)

logger = logging.getLogger(__name__)

class AIService:
    """Database service layer for AI engine operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def store_evidence(self, evidence_data: Dict[str, Any]) -> AIEvidence:
        """Store evidence in database"""
        try:
            evidence = AIEvidence(
                user_id=evidence_data["user_id"],
                evidence_type=evidence_data["type"],
                file_path=evidence_data.get("file_path"),
                file_url=evidence_data.get("file_url"),
                metadata=evidence_data.get("metadata", {}),
                geolocation=evidence_data.get("geolocation"),
                processing_status="pending"
            )
            self.db.add(evidence)
            self.db.commit()
            self.db.refresh(evidence)
            return evidence
        except Exception as e:
            logger.error(f"Error storing evidence: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_user_greenscore_current(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current GreenScore for user"""
        try:
            latest_score = (
                self.db.query(GreenScoreResult)
                .filter(GreenScoreResult.user_id == user_id)
                .order_by(desc(GreenScoreResult.created_at))
                .first()
            )
            
            if not latest_score:
                return None
                
            return {
                "user_id": latest_score.user_id,
                "greenscore": latest_score.greenscore,
                "subscores": latest_score.subscores,
                "co2_saved_tonnes": latest_score.co2_saved_tonnes,
                "confidence": latest_score.confidence,
                "last_updated": latest_score.created_at,
                "explainers": latest_score.explainers,
                "actions": latest_score.actions
            }
        except Exception as e:
            logger.error(f"Error getting current GreenScore: {str(e)}")
            return None
    
    async def get_user_greenscore_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get GreenScore history for user"""
        try:
            history = (
                self.db.query(UserGreenScoreHistory)
                .filter(UserGreenScoreHistory.user_id == user_id)
                .order_by(desc(UserGreenScoreHistory.created_at))
                .limit(limit)
                .all()
            )
            
            return [
                {
                    "date": record.created_at,
                    "greenscore": record.greenscore,
                    "change": record.score_change,
                    "evidence_count": record.evidence_count,
                    "co2_saved_tonnes": record.co2_saved_tonnes
                }
                for record in history
            ]
        except Exception as e:
            logger.error(f"Error getting GreenScore history: {str(e)}")
            return []
    
    async def get_carbon_credits_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Get carbon credits portfolio for user"""
        try:
            credits = (
                self.db.query(CarbonCredit)
                .filter(CarbonCredit.user_id == user_id)
                .all()
            )
            
            total_credits = sum(credit.credits_eligible for credit in credits)
            verified_credits = sum(
                credit.credits_eligible for credit in credits 
                if credit.status == "verified"
            )
            
            return {
                "total_credits": total_credits,
                "verified_credits": verified_credits,
                "pending_credits": total_credits - verified_credits,
                "credits_breakdown": [
                    {
                        "evidence_ids": credit.evidence_ids,
                        "credits": credit.credits_eligible,
                        "co2_tonnes": credit.verified_co2_tonnes,
                        "status": credit.status,
                        "created_at": credit.created_at
                    }
                    for credit in credits
                ]
            }
        except Exception as e:
            logger.error(f"Error getting carbon credits portfolio: {str(e)}")
            return {"total_credits": 0, "verified_credits": 0, "pending_credits": 0, "credits_breakdown": []}
