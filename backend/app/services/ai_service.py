"""Database integration layer for AI engine operations."""
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.ai_models import (
    AIEvidence,
    OCRResult,
    CVResult,
    EmissionResult,
    GreenScoreResult,
    CarbonCredit as CarbonCreditDB,
    SectorBaseline,
    ReviewCase,
    AIProcessingLog,
    UserGreenScoreHistory,
)

logger = logging.getLogger(__name__)

class AIService:
    """Database service layer for AI engine operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def store_evidence(self, evidence_data: Dict[str, Any]) -> AIEvidence:
        """Persist uploaded evidence using ORM-aligned fields."""
        try:
            file_path = evidence_data.get("file_path")
            file_name = evidence_data.get("file_name") or (os.path.basename(file_path) if file_path else None)
            evidence = AIEvidence(
                user_id=evidence_data["user_id"],
                type=evidence_data["type"],
                file_path=file_path,
                file_name=file_name or "evidence",
                file_size_mb=evidence_data.get("file_size_mb", 0.0),
                mime_type=evidence_data.get("mime_type"),
                description=evidence_data.get("description"),
                sector=evidence_data.get("sector", "other"),
                region=evidence_data.get("region", "Kenya"),
                latitude=evidence_data.get("latitude"),
                longitude=evidence_data.get("longitude"),
                location_accuracy=evidence_data.get("location_accuracy"),
                processing_status="pending"
            )
            self.db.add(evidence)
            self.db.commit()
            self.db.refresh(evidence)
            return evidence
        except Exception as e:
            logger.error("Error storing evidence: %s", e)
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
        """Build a summarized view of the user's carbon credits."""
        try:
            credits = (
                self.db.query(CarbonCredit)
                .filter(CarbonCredit.user_id == user_id)
                .order_by(desc(CarbonCredit.created_at))
                .all()
            )

            def summarize(items: List[CarbonCredit]) -> Dict[str, Any]:
                return {
                    "count": len(items),
                    "tonnes_co2": round(sum(c.tonnes_co2 for c in items), 3),
                    "value_usd": round(sum(c.net_value_usd for c in items), 2),
                }

            issued = [c for c in credits if c.status == "issued"]
            pending = [c for c in credits if c.status in {"pending_verification", "pooling_eligible"}]
            eligible = [c for c in credits if c.status in {"eligible"}]

            total_value = summarize(credits)

            recent_issuances = [
                {
                    "credit_id": str(c.id),
                    "evidence_id": str(c.evidence_id),
                    "standard": c.standard,
                    "tonnes_co2": c.tonnes_co2,
                    "net_value_usd": c.net_value_usd,
                    "issued_at": c.actual_issuance,
                }
                for c in issued[:5]
            ]

            breakdown = [
                {
                    "id": str(c.id),
                    "evidence_id": str(c.evidence_id),
                    "greenscore_result_id": str(c.greenscore_result_id),
                    "standard": c.standard,
                    "status": c.status,
                    "approach": c.approach,
                    "tonnes_co2": c.tonnes_co2,
                    "annual_tonnes": c.annual_tonnes,
                    "gross_value_usd": c.gross_value_usd,
                    "net_value_usd": c.net_value_usd,
                    "estimated_issuance": c.estimated_issuance,
                    "actual_issuance": c.actual_issuance,
                    "registry_id": c.registry_id,
                    "created_at": c.created_at,
                }
                for c in credits
            ]

            return {
                "user_id": user_id,
                "summary": {
                    "issued": summarize(issued),
                    "pending": summarize(pending),
                    "eligible": summarize(eligible),
                    "overall": total_value,
                },
                "recent_issuances": recent_issuances,
                "credits": breakdown,
            }
        except Exception as e:
            logger.error("Error getting carbon credits portfolio: %s", e)
            return {
                "user_id": user_id,
                "summary": {
                    "issued": {"count": 0, "tonnes_co2": 0.0, "value_usd": 0.0},
                    "pending": {"count": 0, "tonnes_co2": 0.0, "value_usd": 0.0},
                    "eligible": {"count": 0, "tonnes_co2": 0.0, "value_usd": 0.0},
                    "overall": {"count": 0, "tonnes_co2": 0.0, "value_usd": 0.0},
                },
                "recent_issuances": [],
                "credits": [],
            }

    async def process_evidence_request(
        self,
        user_id: str,
        file_path: str,
        file_name: str,
        file_size_mb: float,
        evidence_type: str,
        sector: str,
        region: str = "Kenya",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process evidence end-to-end using live AI services."""

        from datetime import datetime
        import os
        import time
        import tempfile
        import shutil
        from pathlib import Path

        from app.ai import AIOrchestrator
        from app.ai.models import EvidenceData, AIOrchestrationRequest

        temp_dir: Optional[Path] = None
        temp_path: Optional[Path] = None
        evidence: Optional[AIEvidence] = None

        try:
            allowed_evidence_types = {"receipt", "photo", "invoice", "meter_reading"}
            normalized_type = evidence_type if evidence_type in allowed_evidence_types else "photo"

            # Persist evidence metadata in DB first
            evidence = AIEvidence(
                user_id=user_id,
                type=normalized_type,
                file_path=file_path,
                file_name=file_name,
                file_size_mb=file_size_mb,
                description=description,
                sector=sector,
                region=region,
                processing_status="processing",
                processing_started_at=datetime.utcnow(),
            )
            self.db.add(evidence)
            self.db.commit()
            self.db.refresh(evidence)

            # Ensure evidence file is locally accessible
            source_path = Path(file_path)
            if source_path.exists():
                temp_dir = Path(tempfile.mkdtemp(prefix="evidence_"))
                temp_path = temp_dir / Path(file_name).name
                shutil.copy2(source_path, temp_path)
            else:
                temp_path = None  # evidence processor will fetch via original path

            start_time = time.time()

            orchestrator = AIOrchestrator(
                {
                    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
                    "google_vision_api_key": os.getenv("GOOGLE_VISION_API_KEY", ""),
                    "climatiq_api_key": os.getenv("CLIMATIQ_API_KEY", ""),
                }
            )

            evidence_payload = EvidenceData(
                evidence_id=str(evidence.id),
                user_id=user_id,
                type=normalized_type,
                file_url=str(temp_path) if temp_path else file_path,
                timestamp=datetime.utcnow(),
                metadata={
                    "file_name": file_name,
                    "file_size_mb": file_size_mb,
                    "description": description,
                },
            )

            orchestration_result = await orchestrator.process_request(
                AIOrchestrationRequest(
                    evidence=evidence_payload,
                    sector=sector,
                    region=region,
                    user_profile={"user_id": user_id},
                )
            )

            evidence.processing_status = "completed"
            evidence.processing_completed_at = datetime.utcnow()

            greenscore_record = GreenScoreResult(
                user_id=user_id,
                evidence_id=evidence.id,
                greenscore=orchestration_result.greenscore,
                subscores=orchestration_result.subscores,
                co2_saved_tonnes=orchestration_result.co2_saved_tonnes,
                confidence=orchestration_result.confidence,
                explainers=orchestration_result.explainers,
                actions=orchestration_result.actions,
                sector=sector,
                region=region,
                calculation_method="ai_live",
            )
            self.db.add(greenscore_record)
            self.db.commit()

            processing_time = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "evidence_id": str(evidence.id),
                "processing_time_ms": processing_time,
                "greenscore": orchestration_result.greenscore,
                "confidence": orchestration_result.confidence,
                "review_required": orchestration_result.confidence < 0.7,
                "carbon_credits": orchestration_result.carbon_credits,
            }

        except Exception as exc:  # noqa: BLE001
            logger.error("Error processing evidence request: %s", exc, exc_info=True)
            self.db.rollback()
            if evidence is not None and evidence.id is not None:
                try:
                    self.db.query(AIEvidence).filter(AIEvidence.id == evidence.id).update(
                        {
                            "processing_status": "failed",
                            "processing_completed_at": datetime.utcnow(),
                        }
                    )
                    self.db.commit()
                except Exception as update_exc:  # noqa: BLE001
                    logger.warning("Failed to mark evidence %s as failed: %s", evidence.id, update_exc)
                    self.db.rollback()
            raise

        finally:
            if temp_dir is not None:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as cleanup_exc:  # noqa: BLE001
                    logger.warning("Failed to clean temp evidence directory: %s", cleanup_exc)
    
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
