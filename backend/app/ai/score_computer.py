"""
GreenScore Computation Service
Deterministic scoring engine that converts emissions and metrics to GreenScore
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import math

from .models import GreenScoreResult, EmissionResult
from .sector_baseline import SectorBaselineService

logger = logging.getLogger(__name__)

class ScoreComputer:
    """Deterministic GreenScore computation engine"""
    
    def __init__(self):
        self.sector_baseline = SectorBaselineService()
        
        # Pillar maximum points
        self.pillar_maxes = {
            "energy": 30,
            "water": 15, 
            "waste": 20,
            "carbon": 25,
            "community": 10
        }
        
        # Impact caps for scoring (annual basis)
        self.impact_caps = {
            "co2_tonnes_ann": 5.0,      # 5 tonnes CO2 = max carbon points
            "kwh_saved_ann": 3000.0,    # 3000 kWh = max energy points
            "water_m3_ann": 2000.0,     # 2000 m3 = max water points
            "waste_kg_ann": 500.0       # 500 kg = max waste points
        }

    async def compute_score(
        self,
        user_id: str,
        evidence_id: str,
        sector: str,
        emission_result: EmissionResult,
        user_metrics: Dict[str, float],
        region: str = "Kenya"
    ) -> GreenScoreResult:
        """Main scoring computation pipeline"""
        try:
            # Get sector baseline for relative scoring
            baseline = await self.sector_baseline.get_baseline(sector, region)
            sector_weights = self.sector_baseline.get_sector_weights(sector)
            
            # Calculate pillar scores
            subscores = await self._calculate_subscores(
                emission_result, user_metrics, baseline.baseline, sector
            )
            
            # Apply sector weights
            weighted_subscores = self._apply_sector_weights(subscores, sector_weights)
            
            # Calculate final GreenScore
            greenscore = sum(weighted_subscores.values())
            greenscore = max(0, min(100, round(greenscore)))
            
            # Generate explanations
            explainers = self._generate_explainers(weighted_subscores, emission_result, sector)
            
            # Generate action recommendations
            actions = await self._generate_actions(greenscore, weighted_subscores, sector)
            
            # Calculate overall confidence
            confidence = self._calculate_score_confidence(
                emission_result, user_metrics, weighted_subscores
            )
            
            return GreenScoreResult(
                user_id=user_id,
                evidence_id=evidence_id,
                greenscore=greenscore,
                subscores=weighted_subscores,
                co2_saved_tonnes=emission_result.co2_kg_total / 1000.0,
                confidence=confidence,
                explainers=explainers,
                actions=actions,
                provenance={
                    "sector": sector,
                    "region": region,
                    "baseline_source": baseline.data_source,
                    "calculation_method": "weighted_pillars_v1",
                    "emission_method": emission_result.method,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error computing score for {evidence_id}: {str(e)}")
            return GreenScoreResult(
                user_id=user_id,
                evidence_id=evidence_id,
                greenscore=0,
                confidence=0.1,
                explainers=["Error in score calculation"],
                actions=["Please re-upload evidence"]
            )

    async def _calculate_subscores(
        self,
        emission_result: EmissionResult,
        user_metrics: Dict[str, float],
        baseline: Dict[str, float],
        sector: str
    ) -> Dict[str, float]:
        """Calculate raw pillar subscores before weighting"""
        subscores = {}
        
        # Carbon pillar (based on CO2 saved)
        co2_tonnes = emission_result.co2_kg_total / 1000.0
        carbon_score = min(
            self.pillar_maxes["carbon"],
            (co2_tonnes / self.impact_caps["co2_tonnes_ann"]) * self.pillar_maxes["carbon"]
        )
        subscores["carbon"] = carbon_score
        
        # Energy pillar (based on renewable % and efficiency)
        energy_score = 0.0
        if "renewable_pct" in user_metrics:
            energy_score += user_metrics["renewable_pct"] * self.pillar_maxes["energy"] * 0.7
        
        if "kwh_saved_ann" in user_metrics:
            efficiency_score = min(
                self.pillar_maxes["energy"] * 0.3,
                (user_metrics["kwh_saved_ann"] / self.impact_caps["kwh_saved_ann"]) * self.pillar_maxes["energy"] * 0.3
            )
            energy_score += efficiency_score
        
        subscores["energy"] = min(self.pillar_maxes["energy"], energy_score)
        
        # Water pillar (based on water saved)
        water_score = 0.0
        if "water_m3_saved_ann" in user_metrics:
            water_score = min(
                self.pillar_maxes["water"],
                (user_metrics["water_m3_saved_ann"] / self.impact_caps["water_m3_ann"]) * self.pillar_maxes["water"]
            )
        subscores["water"] = water_score
        
        # Waste pillar (based on recycling and waste reduction)
        waste_score = 0.0
        if "waste_recycled_pct" in user_metrics:
            waste_score += user_metrics["waste_recycled_pct"] * self.pillar_maxes["waste"] * 0.6
        
        if "waste_kg_recycled_ann" in user_metrics:
            recycling_score = min(
                self.pillar_maxes["waste"] * 0.4,
                (user_metrics["waste_kg_recycled_ann"] / self.impact_caps["waste_kg_ann"]) * self.pillar_maxes["waste"] * 0.4
            )
            waste_score += recycling_score
        
        subscores["waste"] = min(self.pillar_maxes["waste"], waste_score)
        
        # Community pillar (based on certifications and community impact)
        community_score = 0.0
        if "nema_certified" in user_metrics and user_metrics["nema_certified"]:
            community_score += 3.0
        if "community_training" in user_metrics and user_metrics["community_training"]:
            community_score += 2.0
        if "local_sourcing_pct" in user_metrics:
            community_score += user_metrics["local_sourcing_pct"] * 5.0
        
        subscores["community"] = min(self.pillar_maxes["community"], community_score)
        
        return subscores

    def _apply_sector_weights(
        self, 
        subscores: Dict[str, float], 
        sector_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Apply sector-specific weights to subscores"""
        weighted_subscores = {}
        
        for pillar, score in subscores.items():
            weight = sector_weights.get(pillar, 0.2)  # Default 20% if not specified
            weighted_subscores[pillar] = score * weight / 0.2  # Normalize to base weight of 0.2
        
        return weighted_subscores

    def _generate_explainers(
        self,
        subscores: Dict[str, float],
        emission_result: EmissionResult,
        sector: str
    ) -> List[str]:
        """Generate human-readable explanations for the score"""
        explainers = []
        
        try:
            # Sort subscores by value to highlight top contributors
            sorted_subscores = sorted(subscores.items(), key=lambda x: x[1], reverse=True)
            
            for pillar, score in sorted_subscores[:3]:  # Top 3 contributors
                max_points = self.pillar_maxes[pillar]
                percentage = (score / max_points) * 100 if max_points > 0 else 0
                
                if pillar == "carbon":
                    co2_tonnes = emission_result.co2_kg_total / 1000.0
                    explainers.append(f"Carbon: {co2_tonnes:.2f} tonnes CO₂ saved → +{score:.0f}/{max_points} points ({percentage:.0f}%)")
                
                elif pillar == "energy":
                    explainers.append(f"Energy: Renewable adoption and efficiency → +{score:.0f}/{max_points} points ({percentage:.0f}%)")
                
                elif pillar == "water":
                    explainers.append(f"Water: Conservation and efficiency measures → +{score:.0f}/{max_points} points ({percentage:.0f}%)")
                
                elif pillar == "waste":
                    explainers.append(f"Waste: Recycling and waste reduction → +{score:.0f}/{max_points} points ({percentage:.0f}%)")
                
                elif pillar == "community":
                    explainers.append(f"Community: Certifications and local impact → +{score:.0f}/{max_points} points ({percentage:.0f}%)")
            
            # Add emission breakdown if significant
            if emission_result.co2_kg_components:
                top_emission = max(emission_result.co2_kg_components.items(), key=lambda x: x[1])
                explainers.append(f"Largest impact: {top_emission[1]:.0f} kg CO₂ from {top_emission[0].replace('_', ' ')}")
            
        except Exception as e:
            logger.error(f"Error generating explainers: {str(e)}")
            explainers = ["Score calculated based on verified environmental actions"]
        
        return explainers

    async def _generate_actions(
        self,
        greenscore: int,
        subscores: Dict[str, float],
        sector: str
    ) -> List[str]:
        """Generate recommended actions based on score and sector"""
        actions = []
        
        try:
            # Score-based actions
            if greenscore >= 80:
                actions.append("Excellent! Approved for premium green loan rates")
                actions.append("Consider carbon credit monetization opportunities")
            elif greenscore >= 60:
                actions.append("Good progress! Approved for standard green loan discount")
                actions.append("Continue implementing sustainable practices")
            elif greenscore >= 40:
                actions.append("Approved with basic green discount")
                actions.append("Focus on high-impact improvements for better rates")
            else:
                actions.append("Additional evidence needed for green loan qualification")
                actions.append("Implement foundational sustainability measures")
            
            # Pillar-specific recommendations
            lowest_pillar = min(subscores.items(), key=lambda x: x[1])
            pillar_name, pillar_score = lowest_pillar
            max_points = self.pillar_maxes[pillar_name]
            
            if pillar_score < max_points * 0.3:  # Less than 30% of max
                if pillar_name == "energy":
                    actions.append("Priority: Invest in renewable energy or energy efficiency")
                elif pillar_name == "water":
                    actions.append("Priority: Implement water conservation measures")
                elif pillar_name == "waste":
                    actions.append("Priority: Set up recycling and waste reduction systems")
                elif pillar_name == "carbon":
                    actions.append("Priority: Focus on high-impact carbon reduction activities")
                elif pillar_name == "community":
                    actions.append("Priority: Obtain environmental certifications")
            
            # Sector-specific suggestions
            sector_suggestions = self.sector_baseline.get_improvement_suggestions(sector, {})
            if sector_suggestions:
                actions.extend(sector_suggestions[:2])  # Add top 2 sector suggestions
            
        except Exception as e:
            logger.error(f"Error generating actions: {str(e)}")
            actions = ["Continue implementing sustainable practices", "Upload additional evidence for better scoring"]
        
        return actions

    def _calculate_score_confidence(
        self,
        emission_result: EmissionResult,
        user_metrics: Dict[str, float],
        subscores: Dict[str, float]
    ) -> float:
        """Calculate confidence in the computed score"""
        try:
            confidence = 0.5  # Base confidence
            
            # Higher confidence with more emission calculation confidence
            confidence += emission_result.confidence * 0.3
            
            # Higher confidence with more user metrics
            metrics_count = len([v for v in user_metrics.values() if v is not None and v > 0])
            confidence += min(metrics_count * 0.05, 0.2)
            
            # Higher confidence if subscores are balanced (not all from one pillar)
            non_zero_pillars = len([s for s in subscores.values() if s > 0])
            if non_zero_pillars >= 3:
                confidence += 0.1
            elif non_zero_pillars >= 2:
                confidence += 0.05
            
            # Lower confidence for extreme scores (potential outliers)
            total_score = sum(subscores.values())
            if total_score > 90 or total_score < 10:
                confidence -= 0.1
            
            return max(0.1, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating score confidence: {str(e)}")
            return 0.5

    def estimate_user_metrics_from_evidence(
        self,
        emission_result: EmissionResult,
        sector: str,
        ocr_data: Dict[str, Any],
        cv_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Estimate user metrics from evidence data"""
        metrics = {}
        
        try:
            # Estimate renewable percentage based on evidence
            if "solar" in str(cv_data.get("labels", [])).lower():
                if sector == "salon":
                    metrics["renewable_pct"] = 0.6  # 60% renewable for salon with solar
                elif sector == "farmer":
                    metrics["renewable_pct"] = 0.8  # 80% for farmer with solar pump
                elif sector == "welding":
                    metrics["renewable_pct"] = 0.4  # 40% for welding shop with solar
            
            # Estimate annual savings from monthly/seasonal data
            co2_kg_total = emission_result.co2_kg_total
            if co2_kg_total > 0:
                # Estimate annual kWh saved from CO2 (assuming grid factor 0.45)
                estimated_kwh_ann = (co2_kg_total / 0.45) * 12  # Monthly to annual
                metrics["kwh_saved_ann"] = estimated_kwh_ann
            
            # Estimate waste recycling based on sector and evidence
            if "led" in str(cv_data.get("labels", [])).lower():
                metrics["waste_recycled_pct"] = 0.3  # 30% recycling with LED upgrade
            
            # Estimate water savings for farmers
            if sector == "farmer" and ("drip" in str(ocr_data.get("items", [])).lower() or 
                                     "irrigation" in str(ocr_data.get("items", [])).lower()):
                metrics["water_m3_saved_ann"] = 800.0  # Typical drip irrigation savings
            
            # Community metrics based on vendor credibility
            vendor = ocr_data.get("vendor", "")
            if vendor and any(cert in vendor.lower() for cert in ["certified", "approved", "licensed"]):
                metrics["nema_certified"] = 1.0
            
        except Exception as e:
            logger.error(f"Error estimating user metrics: {str(e)}")
        
        return metrics
