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

    async def process_evidence_request(
        self, user_id: str, file_path: str, file_name: str, file_size_mb: float,
        evidence_type: str, sector: str, region: str = "Kenya", description: str = None
    ) -> Dict[str, Any]:
        """Process evidence request and return results"""
        try:
            import os
            import time
            from datetime import datetime
            
            # Create evidence record
            evidence = AIEvidence(
                user_id=user_id,
                type=evidence_type,
                file_path=file_path,
                file_name=file_name,
                file_size_mb=file_size_mb,
                description=description,
                sector=sector,
                region=region,
                processing_status="processing",
                processing_started_at=datetime.utcnow()
            )
            
            self.db.add(evidence)
            self.db.commit()
            self.db.refresh(evidence)
            
            start_time = time.time()
            
            # Simulate AI processing with realistic results
            processing_result = self._simulate_ai_processing(evidence_type, sector)
            
            # Update evidence status
            evidence.processing_status = "completed"
            evidence.processing_completed_at = datetime.utcnow()
            self.db.commit()
            
            # Create GreenScore result
            greenscore_result = GreenScoreResult(
                user_id=user_id,
                evidence_id=evidence.id,
                greenscore=processing_result["greenscore"],
                subscores=processing_result["subscores"],
                co2_saved_tonnes=processing_result["co2_saved_tonnes"],
                confidence=processing_result["confidence"],
                explainers=processing_result["explainers"],
                actions=processing_result["actions"],
                sector=sector,
                region=region,
                calculation_method="ai_simulation"
            )
            
            self.db.add(greenscore_result)
            self.db.commit()
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "evidence_id": str(evidence.id),
                "processing_time_ms": processing_time,
                "greenscore": processing_result["greenscore"],
                "confidence": processing_result["confidence"],
                "review_required": processing_result["confidence"] < 0.7
            }
            
        except Exception as e:
            logger.error(f"Error processing evidence request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": 0,
                "greenscore": None,
                "confidence": 0.0,
                "review_required": True
            }
    
    def _simulate_ai_processing(self, evidence_type: str, sector: str) -> Dict[str, Any]:
        """Simulate AI processing results based on evidence type and sector"""
        import random
        
        # Base scores by sector
        sector_base_scores = {
            "agriculture": {"base": 65, "variance": 15},
            "beauty": {"base": 55, "variance": 12},
            "welding": {"base": 50, "variance": 10},
            "transport": {"base": 60, "variance": 18},
            "other": {"base": 55, "variance": 15}
        }
        
        # Evidence type multipliers
        evidence_multipliers = {
            "solar_panel_receipt": 1.3,
            "led_lighting": 1.2,
            "energy_meter": 1.15,
            "biogas_setup": 1.4,
            "drip_irrigation": 1.25,
            "receipt": 1.0,
            "photo": 0.9,
            "invoice": 1.1
        }
        
        base_info = sector_base_scores.get(sector, sector_base_scores["other"])
        multiplier = evidence_multipliers.get(evidence_type, 1.0)
        
        # Calculate score with some randomness
        base_score = base_info["base"]
        variance = base_info["variance"]
        random_factor = random.uniform(-variance, variance)
        
        greenscore = max(20, min(100, int((base_score + random_factor) * multiplier)))
        
        # Generate subscores
        subscores = {
            "energy_efficiency": random.uniform(15, 30),
            "renewable_energy": random.uniform(10, 25),
            "water_conservation": random.uniform(8, 20),
            "waste_management": random.uniform(5, 15),
            "sustainable_practices": random.uniform(10, 20)
        }
        
        # Normalize subscores to match total
        total_subscore = sum(subscores.values())
        for key in subscores:
            subscores[key] = round((subscores[key] / total_subscore) * greenscore, 2)
        
        # Calculate CO2 savings
        co2_saved_tonnes = round(greenscore * 0.025 + random.uniform(0, 2), 3)
        
        # Generate explainers
        explainers = [
            f"Evidence shows {evidence_type.replace('_', ' ')} implementation",
            f"Sector: {sector} - Above average performance",
            f"Estimated CO2 reduction: {co2_saved_tonnes} tonnes/year"
        ]
        
        # Generate action recommendations
        actions = [
            "Consider upgrading to more efficient equipment",
            "Document regular maintenance for better scoring",
            "Track energy consumption for verification",
            "Join local sustainability networks"
        ]
        
        # Confidence based on evidence type and score consistency
        base_confidence = evidence_multipliers.get(evidence_type, 1.0) * 0.6
        confidence = min(0.95, max(0.4, base_confidence + random.uniform(-0.1, 0.2)))
        
        return {
            "greenscore": greenscore,
            "subscores": subscores,
            "co2_saved_tonnes": co2_saved_tonnes,
            "confidence": round(confidence, 2),
            "explainers": explainers,
            "actions": actions
        }
