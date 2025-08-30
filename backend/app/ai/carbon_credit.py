"""
Carbon Credit Aggregation Service
Calculates eligible carbon credits and manages pooling for SMEs
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import uuid

from .models import CarbonCredit, EmissionResult, GreenScoreResult

logger = logging.getLogger(__name__)

class CarbonCreditAggregator:
    """Manages carbon credit calculation, verification, and pooling"""
    
    def __init__(self):
        # Carbon credit standards and pricing
        self.standards = {
            "VCS": {
                "min_tonnes_individual": 1.0,
                "min_tonnes_pooled": 0.1,
                "buffer_percentage": 0.15,  # 15% buffer for permanence
                "price_usd_per_tonne": 12.0,
                "verification_cost_usd": 50.0,
                "pooling_fee_percentage": 0.08  # 8% pooling fee
            },
            "Gold_Standard": {
                "min_tonnes_individual": 2.0,
                "min_tonnes_pooled": 0.2,
                "buffer_percentage": 0.20,  # 20% buffer
                "price_usd_per_tonne": 18.0,
                "verification_cost_usd": 75.0,
                "pooling_fee_percentage": 0.10
            },
            "CDM": {
                "min_tonnes_individual": 5.0,
                "min_tonnes_pooled": 0.5,
                "buffer_percentage": 0.10,  # 10% buffer
                "price_usd_per_tonne": 8.0,
                "verification_cost_usd": 100.0,
                "pooling_fee_percentage": 0.12
            }
        }
        
        # Additionality criteria by sector
        self.additionality_criteria = {
            "salon": {
                "solar_panels": {"baseline_adoption": 0.12, "additionality_threshold": 0.15},
                "led_lighting": {"baseline_adoption": 0.35, "additionality_threshold": 0.40},
                "energy_efficient_equipment": {"baseline_adoption": 0.20, "additionality_threshold": 0.25}
            },
            "farmer": {
                "solar_irrigation": {"baseline_adoption": 0.15, "additionality_threshold": 0.20},
                "drip_irrigation": {"baseline_adoption": 0.08, "additionality_threshold": 0.12},
                "organic_farming": {"baseline_adoption": 0.05, "additionality_threshold": 0.10}
            },
            "welding": {
                "solar_power": {"baseline_adoption": 0.18, "additionality_threshold": 0.25},
                "efficient_welders": {"baseline_adoption": 0.25, "additionality_threshold": 0.30},
                "waste_recycling": {"baseline_adoption": 0.15, "additionality_threshold": 0.20}
            }
        }

    async def calculate_carbon_credits(
        self,
        user_id: str,
        evidence_id: str,
        emission_result: EmissionResult,
        greenscore_result: GreenScoreResult,
        sector: str,
        project_lifetime_years: int = 5
    ) -> List[CarbonCredit]:
        """Calculate eligible carbon credits for different standards"""
        credits = []
        
        try:
            # Calculate annual CO2 reduction in tonnes
            annual_co2_tonnes = emission_result.co2_kg_total / 1000.0
            
            # Check additionality
            is_additional = await self._check_additionality(
                emission_result, sector, greenscore_result.confidence
            )
            
            if not is_additional:
                logger.info(f"Project {evidence_id} does not meet additionality criteria")
                return credits
            
            # Calculate credits for each standard
            for standard_name, standard_config in self.standards.items():
                credit = await self._calculate_credit_for_standard(
                    user_id=user_id,
                    evidence_id=evidence_id,
                    standard_name=standard_name,
                    standard_config=standard_config,
                    annual_co2_tonnes=annual_co2_tonnes,
                    project_lifetime_years=project_lifetime_years,
                    confidence=greenscore_result.confidence,
                    sector=sector
                )
                
                if credit:
                    credits.append(credit)
            
            return credits
            
        except Exception as e:
            logger.error(f"Error calculating carbon credits: {str(e)}")
            return []

    async def _calculate_credit_for_standard(
        self,
        user_id: str,
        evidence_id: str,
        standard_name: str,
        standard_config: Dict[str, Any],
        annual_co2_tonnes: float,
        project_lifetime_years: int,
        confidence: float,
        sector: str
    ) -> Optional[CarbonCredit]:
        """Calculate carbon credit for a specific standard"""
        try:
            # Total lifetime emissions reduction
            total_co2_tonnes = annual_co2_tonnes * project_lifetime_years
            
            # Apply buffer for permanence and leakage
            buffer_percentage = standard_config["buffer_percentage"]
            net_co2_tonnes = total_co2_tonnes * (1 - buffer_percentage)
            
            # Check minimum thresholds
            min_individual = standard_config["min_tonnes_individual"]
            min_pooled = standard_config["min_tonnes_pooled"]
            
            # Determine eligibility and approach
            if net_co2_tonnes >= min_individual:
                approach = "individual"
                eligible_tonnes = net_co2_tonnes
            elif net_co2_tonnes >= min_pooled:
                approach = "pooled"
                eligible_tonnes = net_co2_tonnes
            else:
                return None  # Below minimum threshold
            
            # Calculate financial metrics
            price_per_tonne = standard_config["price_usd_per_tonne"]
            verification_cost = standard_config["verification_cost_usd"]
            
            gross_value = eligible_tonnes * price_per_tonne
            
            if approach == "pooled":
                pooling_fee = gross_value * standard_config["pooling_fee_percentage"]
                net_value = gross_value - pooling_fee - (verification_cost / 10)  # Shared verification cost
            else:
                pooling_fee = 0.0
                net_value = gross_value - verification_cost
            
            # Determine status based on confidence and tonnes
            if confidence >= 0.8 and net_co2_tonnes >= min_individual:
                status = "eligible"
            elif confidence >= 0.6 and net_co2_tonnes >= min_pooled:
                status = "pooling_eligible"
            else:
                status = "pending_verification"
            
            # Calculate issuance timeline
            if approach == "individual":
                estimated_issuance = datetime.now() + timedelta(days=180)  # 6 months
            else:
                estimated_issuance = datetime.now() + timedelta(days=90)   # 3 months for pooled
            
            return CarbonCredit(
                id=str(uuid.uuid4()),
                user_id=user_id,
                evidence_id=evidence_id,
                standard=standard_name,
                tonnes_co2=round(eligible_tonnes, 3),
                annual_tonnes=round(annual_co2_tonnes, 3),
                project_lifetime_years=project_lifetime_years,
                buffer_percentage=buffer_percentage,
                gross_value_usd=round(gross_value, 2),
                net_value_usd=round(net_value, 2),
                verification_cost_usd=verification_cost if approach == "individual" else round(verification_cost / 10, 2),
                pooling_fee_usd=round(pooling_fee, 2) if approach == "pooled" else 0.0,
                status=status,
                approach=approach,
                estimated_issuance=estimated_issuance,
                sector=sector,
                additionality_verified=True,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating credit for {standard_name}: {str(e)}")
            return None

    async def _check_additionality(
        self,
        emission_result: EmissionResult,
        sector: str,
        confidence: float
    ) -> bool:
        """Check if the project meets additionality criteria"""
        try:
            # Minimum confidence threshold for additionality
            if confidence < 0.5:
                return False
            
            # Check sector-specific additionality
            sector_criteria = self.additionality_criteria.get(sector.lower(), {})
            
            # For now, use a simplified additionality check
            # In practice, this would involve:
            # 1. Barrier analysis (financial, technological, institutional)
            # 2. Common practice analysis
            # 3. Investment analysis
            
            # Simplified check: if emission reduction is significant relative to baseline
            if emission_result.co2_kg_total > 100:  # At least 100kg CO2 annually
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking additionality: {str(e)}")
            return False

    async def aggregate_pool_credits(
        self,
        credits: List[CarbonCredit],
        pool_name: str = "Kenya_SME_Pool"
    ) -> Dict[str, Any]:
        """Aggregate multiple small credits into a pooled project"""
        try:
            # Filter pooling-eligible credits
            pooled_credits = [c for c in credits if c.approach == "pooled" and c.status in ["pooling_eligible", "eligible"]]
            
            if not pooled_credits:
                return {"status": "no_eligible_credits", "total_tonnes": 0}
            
            # Group by standard
            pools_by_standard = {}
            for credit in pooled_credits:
                if credit.standard not in pools_by_standard:
                    pools_by_standard[credit.standard] = []
                pools_by_standard[credit.standard].append(credit)
            
            pool_summary = {}
            
            for standard, standard_credits in pools_by_standard.items():
                total_tonnes = sum(c.tonnes_co2 for c in standard_credits)
                total_gross_value = sum(c.gross_value_usd for c in standard_credits)
                total_net_value = sum(c.net_value_usd for c in standard_credits)
                
                pool_summary[standard] = {
                    "pool_name": f"{pool_name}_{standard}",
                    "participant_count": len(standard_credits),
                    "total_tonnes_co2": round(total_tonnes, 3),
                    "total_gross_value_usd": round(total_gross_value, 2),
                    "total_net_value_usd": round(total_net_value, 2),
                    "average_tonnes_per_participant": round(total_tonnes / len(standard_credits), 3),
                    "participants": [
                        {
                            "user_id": c.user_id,
                            "tonnes": c.tonnes_co2,
                            "value_usd": c.net_value_usd,
                            "sector": c.sector
                        }
                        for c in standard_credits
                    ]
                }
            
            return {
                "status": "pooled",
                "pools": pool_summary,
                "total_participants": len(pooled_credits),
                "total_tonnes": sum(c.tonnes_co2 for c in pooled_credits),
                "total_value": sum(c.net_value_usd for c in pooled_credits)
            }
            
        except Exception as e:
            logger.error(f"Error aggregating pool credits: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_credit_recommendations(
        self,
        credits: List[CarbonCredit],
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Provide recommendations for carbon credit strategy"""
        try:
            if not credits:
                return {
                    "recommendation": "increase_impact",
                    "message": "Increase environmental impact to qualify for carbon credits",
                    "min_annual_co2_needed": 100  # kg
                }
            
            # Find best credit option
            eligible_credits = [c for c in credits if c.status in ["eligible", "pooling_eligible"]]
            
            if not eligible_credits:
                return {
                    "recommendation": "improve_verification",
                    "message": "Improve evidence quality for carbon credit eligibility",
                    "pending_credits": len(credits)
                }
            
            # Sort by net value per tonne
            best_credit = max(eligible_credits, key=lambda c: c.net_value_usd / c.tonnes_co2 if c.tonnes_co2 > 0 else 0)
            
            recommendations = {
                "recommended_standard": best_credit.standard,
                "approach": best_credit.approach,
                "estimated_annual_value": round(best_credit.net_value_usd / best_credit.project_lifetime_years, 2),
                "total_project_value": best_credit.net_value_usd,
                "timeline_months": (best_credit.estimated_issuance - datetime.now()).days // 30,
                "next_steps": []
            }
            
            if best_credit.approach == "pooled":
                recommendations["next_steps"].extend([
                    "Join SME carbon credit pool for faster issuance",
                    "Maintain evidence quality for verification",
                    "Continue sustainable practices for ongoing credits"
                ])
            else:
                recommendations["next_steps"].extend([
                    "Prepare for individual project verification",
                    "Gather additional supporting documentation",
                    "Consider expanding project scope for higher value"
                ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating credit recommendations: {str(e)}")
            return {"recommendation": "error", "message": "Unable to generate recommendations"}

    async def track_credit_performance(
        self,
        user_id: str,
        time_period_months: int = 12
    ) -> Dict[str, Any]:
        """Track carbon credit performance over time"""
        try:
            # This would typically query a database
            # For now, return a template structure
            
            return {
                "user_id": user_id,
                "period_months": time_period_months,
                "total_credits_issued": 0,
                "total_value_earned": 0.0,
                "credits_pending": 0,
                "average_monthly_co2": 0.0,
                "performance_trend": "stable",
                "recommendations": [
                    "Continue current sustainable practices",
                    "Consider expanding to additional activities"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error tracking credit performance: {str(e)}")
            return {"error": str(e)}
