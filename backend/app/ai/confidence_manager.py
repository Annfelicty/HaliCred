"""
Confidence Management and Human-in-Loop Service
Manages confidence scoring, review triggers, and audit trails
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

from .models import AIOrchestrationResult, GreenScoreResult, CarbonCredit

logger = logging.getLogger(__name__)

class ReviewReason(Enum):
    LOW_CONFIDENCE = "low_confidence"
    HIGH_VALUE_CLAIM = "high_value_claim"
    INCONSISTENT_DATA = "inconsistent_data"
    FRAUD_RISK = "fraud_risk"
    NEW_USER = "new_user"
    SECTOR_OUTLIER = "sector_outlier"
    MANUAL_REQUEST = "manual_request"

class ReviewStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MORE_INFO = "needs_more_info"

class ConfidenceManager:
    """Manages confidence scoring and human review triggers"""
    
    def __init__(self):
        # Confidence thresholds for different actions
        self.thresholds = {
            "auto_approve": 0.85,
            "human_review": 0.60,
            "auto_reject": 0.30,
            "high_value_review": 0.70  # Higher threshold for high-value claims
        }
        
        # Value thresholds for human review (USD)
        self.value_thresholds = {
            "carbon_credit_value": 100.0,  # $100+ carbon credits need review
            "loan_amount": 5000.0,         # $5000+ loans need review
            "greenscore_impact": 20        # 20+ point GreenScore changes need review
        }
        
        # Fraud detection patterns
        self.fraud_patterns = {
            "duplicate_evidence": {"window_hours": 24, "max_similar": 3},
            "rapid_submissions": {"window_hours": 1, "max_submissions": 5},
            "inconsistent_location": {"max_distance_km": 50},
            "suspicious_amounts": {"min_amount": 10000, "max_amount": 100000}
        }

    async def evaluate_confidence(
        self,
        ai_result: AIOrchestrationResult,
        user_history: Dict[str, Any] = None,
        sector_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Comprehensive confidence evaluation"""
        try:
            # Base confidence from AI processing
            base_confidence = ai_result.confidence
            
            # Calculate component confidences
            components = await self._calculate_component_confidences(ai_result, user_history, sector_context)
            
            # Weighted final confidence
            weights = {
                "ai_processing": 0.4,
                "data_quality": 0.25,
                "user_credibility": 0.15,
                "sector_consistency": 0.10,
                "fraud_risk": 0.10
            }
            
            final_confidence = sum(
                components[component] * weight 
                for component, weight in weights.items()
                if component in components
            )
            
            # Determine review requirements
            review_decision = self._determine_review_requirements(
                final_confidence, ai_result, components
            )
            
            return {
                "final_confidence": round(final_confidence, 3),
                "component_confidences": components,
                "review_required": review_decision["required"],
                "review_reasons": review_decision["reasons"],
                "review_priority": review_decision["priority"],
                "auto_approve": final_confidence >= self.thresholds["auto_approve"],
                "auto_reject": final_confidence <= self.thresholds["auto_reject"],
                "confidence_factors": self._generate_confidence_explanation(components)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating confidence: {str(e)}")
            return {
                "final_confidence": 0.3,
                "review_required": True,
                "review_reasons": [ReviewReason.MANUAL_REQUEST.value],
                "error": str(e)
            }

    async def _calculate_component_confidences(
        self,
        ai_result: AIOrchestrationResult,
        user_history: Optional[Dict[str, Any]],
        sector_context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate confidence for each component"""
        components = {}
        
        # AI Processing Confidence
        components["ai_processing"] = ai_result.confidence
        
        # Data Quality Confidence
        components["data_quality"] = self._assess_data_quality(ai_result)
        
        # User Credibility Confidence
        components["user_credibility"] = self._assess_user_credibility(user_history or {})
        
        # Sector Consistency Confidence
        components["sector_consistency"] = self._assess_sector_consistency(
            ai_result, sector_context or {}
        )
        
        # Fraud Risk Assessment (inverted - lower risk = higher confidence)
        fraud_risk = await self._assess_fraud_risk(ai_result, user_history or {})
        components["fraud_risk"] = 1.0 - fraud_risk
        
        return components

    def _assess_data_quality(self, ai_result: AIOrchestrationResult) -> float:
        """Assess quality of input data and processing results"""
        quality_score = 0.5  # Base score
        
        try:
            if ai_result.greenscore_result:
                greenscore = ai_result.greenscore_result
                
                # Higher quality if multiple evidence types
                if len(greenscore.subscores) >= 3:
                    quality_score += 0.2
                
                # Higher quality if explainers are detailed
                if len(greenscore.explainers) >= 2:
                    quality_score += 0.1
                
                # Higher quality if provenance is complete
                if greenscore.provenance and len(greenscore.provenance) >= 5:
                    quality_score += 0.1
                
                # Lower quality for extreme scores (potential outliers)
                if greenscore.greenscore > 95 or greenscore.greenscore < 5:
                    quality_score -= 0.2
            
            # Processing time indicator (very fast might indicate cached/fake data)
            if ai_result.processing_time_ms < 100:
                quality_score -= 0.1
            elif ai_result.processing_time_ms > 30000:  # Very slow processing
                quality_score -= 0.05
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error assessing data quality: {str(e)}")
            return 0.3

    def _assess_user_credibility(self, user_history: Dict[str, Any]) -> float:
        """Assess user credibility based on history"""
        credibility_score = 0.5  # Base score for new users
        
        try:
            # Account age factor
            account_age_days = user_history.get("account_age_days", 0)
            if account_age_days > 365:
                credibility_score += 0.2
            elif account_age_days > 90:
                credibility_score += 0.1
            elif account_age_days < 7:
                credibility_score -= 0.2
            
            # Previous submission history
            previous_submissions = user_history.get("previous_submissions", 0)
            if previous_submissions > 10:
                credibility_score += 0.15
            elif previous_submissions > 3:
                credibility_score += 0.1
            
            # Previous approval rate
            approval_rate = user_history.get("approval_rate", 0.5)
            credibility_score += (approval_rate - 0.5) * 0.4
            
            # Fraud flags
            fraud_flags = user_history.get("fraud_flags", 0)
            credibility_score -= fraud_flags * 0.2
            
            # Verification status
            if user_history.get("phone_verified", False):
                credibility_score += 0.05
            if user_history.get("business_registered", False):
                credibility_score += 0.1
            
            return max(0.0, min(1.0, credibility_score))
            
        except Exception as e:
            logger.error(f"Error assessing user credibility: {str(e)}")
            return 0.5

    def _assess_sector_consistency(
        self, 
        ai_result: AIOrchestrationResult, 
        sector_context: Dict[str, Any]
    ) -> float:
        """Assess consistency with sector norms"""
        consistency_score = 0.7  # Base score
        
        try:
            if not ai_result.greenscore_result:
                return consistency_score
            
            greenscore = ai_result.greenscore_result.greenscore
            sector_avg = sector_context.get("average_greenscore", 50)
            sector_std = sector_context.get("std_greenscore", 20)
            
            # Check if score is within reasonable range
            z_score = abs(greenscore - sector_avg) / sector_std if sector_std > 0 else 0
            
            if z_score > 3:  # More than 3 standard deviations
                consistency_score -= 0.3
            elif z_score > 2:
                consistency_score -= 0.1
            
            # Check carbon credit values against sector norms
            if ai_result.carbon_credits:
                total_credit_value = sum(c.net_value_usd for c in ai_result.carbon_credits)
                sector_avg_credits = sector_context.get("average_credit_value", 50)
                
                if total_credit_value > sector_avg_credits * 5:  # 5x sector average
                    consistency_score -= 0.2
            
            return max(0.0, min(1.0, consistency_score))
            
        except Exception as e:
            logger.error(f"Error assessing sector consistency: {str(e)}")
            return 0.7

    async def _assess_fraud_risk(
        self, 
        ai_result: AIOrchestrationResult, 
        user_history: Dict[str, Any]
    ) -> float:
        """Assess fraud risk (0 = no risk, 1 = high risk)"""
        risk_score = 0.0
        
        try:
            # Rapid submission pattern
            recent_submissions = user_history.get("submissions_last_24h", 0)
            if recent_submissions > self.fraud_patterns["rapid_submissions"]["max_submissions"]:
                risk_score += 0.3
            
            # Duplicate evidence detection (simplified)
            similar_evidence_count = user_history.get("similar_evidence_count", 0)
            if similar_evidence_count > self.fraud_patterns["duplicate_evidence"]["max_similar"]:
                risk_score += 0.4
            
            # Suspicious amounts
            if ai_result.carbon_credits:
                max_credit_value = max(c.net_value_usd for c in ai_result.carbon_credits)
                if max_credit_value > self.fraud_patterns["suspicious_amounts"]["max_amount"]:
                    risk_score += 0.3
            
            # Inconsistent location data
            if user_history.get("location_inconsistency", False):
                risk_score += 0.2
            
            # Perfect scores (suspicious)
            if ai_result.greenscore_result and ai_result.greenscore_result.greenscore >= 98:
                risk_score += 0.1
            
            return min(1.0, risk_score)
            
        except Exception as e:
            logger.error(f"Error assessing fraud risk: {str(e)}")
            return 0.1

    def _determine_review_requirements(
        self, 
        confidence: float, 
        ai_result: AIOrchestrationResult, 
        components: Dict[str, float]
    ) -> Dict[str, Any]:
        """Determine if human review is required and why"""
        reasons = []
        priority = "low"
        
        # Confidence-based triggers
        if confidence < self.thresholds["human_review"]:
            reasons.append(ReviewReason.LOW_CONFIDENCE.value)
            priority = "medium"
        
        # High-value triggers
        if ai_result.carbon_credits:
            total_value = sum(c.net_value_usd for c in ai_result.carbon_credits)
            if total_value > self.value_thresholds["carbon_credit_value"]:
                reasons.append(ReviewReason.HIGH_VALUE_CLAIM.value)
                if confidence < self.thresholds["high_value_review"]:
                    priority = "high"
        
        # Fraud risk triggers
        if components.get("fraud_risk", 1.0) < 0.7:  # High fraud risk
            reasons.append(ReviewReason.FRAUD_RISK.value)
            priority = "high"
        
        # Data inconsistency triggers
        if components.get("sector_consistency", 1.0) < 0.5:
            reasons.append(ReviewReason.SECTOR_OUTLIER.value)
            priority = "medium"
        
        # New user trigger
        if components.get("user_credibility", 1.0) < 0.4:
            reasons.append(ReviewReason.NEW_USER.value)
        
        return {
            "required": len(reasons) > 0,
            "reasons": reasons,
            "priority": priority
        }

    def _generate_confidence_explanation(self, components: Dict[str, float]) -> List[str]:
        """Generate human-readable confidence explanations"""
        explanations = []
        
        try:
            for component, score in components.items():
                if score >= 0.8:
                    level = "High"
                elif score >= 0.6:
                    level = "Medium"
                else:
                    level = "Low"
                
                component_name = component.replace("_", " ").title()
                explanations.append(f"{component_name}: {level} ({score:.2f})")
            
            return explanations
            
        except Exception as e:
            logger.error(f"Error generating confidence explanation: {str(e)}")
            return ["Confidence assessment completed"]

    async def create_review_case(
        self,
        ai_result: AIOrchestrationResult,
        confidence_assessment: Dict[str, Any],
        reviewer_notes: str = ""
    ) -> Dict[str, Any]:
        """Create a human review case"""
        try:
            case_id = f"review_{ai_result.evidence_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            review_case = {
                "case_id": case_id,
                "evidence_id": ai_result.evidence_id,
                "user_id": ai_result.user_id,
                "status": ReviewStatus.PENDING.value,
                "priority": confidence_assessment.get("review_priority", "medium"),
                "reasons": confidence_assessment.get("review_reasons", []),
                "confidence_score": confidence_assessment.get("final_confidence", 0.5),
                "ai_result": ai_result.dict(),
                "created_at": datetime.now(),
                "reviewer_notes": reviewer_notes,
                "review_deadline": datetime.now() + timedelta(hours=24),  # 24h SLA
                "escalation_level": 1
            }
            
            # In a real system, this would be stored in a database
            logger.info(f"Created review case {case_id} for evidence {ai_result.evidence_id}")
            
            return review_case
            
        except Exception as e:
            logger.error(f"Error creating review case: {str(e)}")
            return {"error": str(e)}

    def evaluate_result(self, result: AIOrchestrationResult) -> Dict[str, Any]:
        """Evaluate AI result and determine if human review is needed"""
        try:
            confidence_score = result.confidence
            review_reasons = []
            
            # Check confidence threshold
            if confidence_score < self.confidence_threshold:
                review_reasons.append(ReviewReason.LOW_CONFIDENCE)
            
            # Check for high-value claims
            if result.co2_saved_tonnes > 10.0:  # High impact claim
                review_reasons.append(ReviewReason.HIGH_VALUE_CLAIM)
            
            # Check for outliers
            if result.greenscore > 900:  # Very high score
                review_reasons.append(ReviewReason.SECTOR_OUTLIER)
            
            needs_review = len(review_reasons) > 0
            
            return {
                "needs_review": needs_review,
                "confidence_score": confidence_score,
                "review_reasons": [r.value for r in review_reasons],
                "priority": "high" if confidence_score < 0.5 else "medium" if confidence_score < 0.7 else "low"
            }
            
        except Exception as e:
            logger.error(f"Error evaluating result: {str(e)}")
            return {
                "needs_review": True,
                "confidence_score": 0.0,
                "review_reasons": ["evaluation_error"],
                "priority": "high"
            }

    def get_review_queue_summary(self) -> Dict[str, Any]:
        """Get summary of pending reviews (mock implementation)"""
        # In a real system, this would query the review database
        return {
            "total_pending": 0,
            "high_priority": 0,
            "medium_priority": 0,
            "low_priority": 0,
            "overdue": 0,
            "avg_processing_time_hours": 4.2,
            "approval_rate": 0.78
        }
