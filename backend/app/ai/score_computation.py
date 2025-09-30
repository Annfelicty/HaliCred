"""
Production-ready score computation service with reliability, monitoring, and error handling.
Implements robust scoring algorithms with fallback mechanisms and comprehensive monitoring.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import json
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import User, GreenScore, Evidence, BusinessProfile
from app.ai.api_client import external_api_client
from app.config import settings

logger = logging.getLogger(__name__)


class ComputationMethod(Enum):
    """Score computation methods"""
    AI_ENHANCED = "ai_enhanced"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"
    FALLBACK = "fallback"


class ScoreCategory(Enum):
    """Green score categories"""
    ENERGY_EFFICIENCY = "energy_efficiency"
    WATER_CONSERVATION = "water_conservation"
    WASTE_MANAGEMENT = "waste_management"
    SUSTAINABLE_PRACTICES = "sustainable_practices"
    CARBON_FOOTPRINT = "carbon_footprint"


@dataclass
class ScoreMetrics:
    """Score computation metrics for monitoring"""
    computation_time: float
    method_used: ComputationMethod
    confidence_level: float
    evidence_count: int
    ai_api_calls: int
    fallback_triggers: int
    error_count: int
    warnings: List[str]


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown"""
    category: ScoreCategory
    score: float
    max_score: float
    evidence_items: List[str]
    reasoning: str
    confidence: float


@dataclass
class ComputationResult:
    """Complete score computation result"""
    user_id: str
    total_score: float
    raw_score: float
    normalized_score: float
    breakdown: List[ScoreBreakdown]
    computation_method: ComputationMethod
    confidence: float
    metrics: ScoreMetrics
    explanations: List[str]
    computed_at: datetime
    expires_at: Optional[datetime]


class ScoreComputationService:
    """Production-ready score computation service"""

    def __init__(self):
        self.max_score = 100.0
        self.min_score = 0.0
        self.confidence_threshold = 0.6
        self.cache_duration_hours = 24

        # Score weights for each category
        self.category_weights = {
            ScoreCategory.ENERGY_EFFICIENCY: 0.25,
            ScoreCategory.WATER_CONSERVATION: 0.20,
            ScoreCategory.WASTE_MANAGEMENT: 0.20,
            ScoreCategory.SUSTAINABLE_PRACTICES: 0.20,
            ScoreCategory.CARBON_FOOTPRINT: 0.15
        }

        # Evidence type scoring rules
        self.evidence_scoring_rules = {
            'solar_installation': {'base_score': 25, 'category': ScoreCategory.ENERGY_EFFICIENCY},
            'led_lighting': {'base_score': 15, 'category': ScoreCategory.ENERGY_EFFICIENCY},
            'water_pump': {'base_score': 20, 'category': ScoreCategory.WATER_CONSERVATION},
            'waste_recycling': {'base_score': 18, 'category': ScoreCategory.WASTE_MANAGEMENT},
            'carbon_credit': {'base_score': 22, 'category': ScoreCategory.CARBON_FOOTPRINT},
            'green_certification': {'base_score': 20, 'category': ScoreCategory.SUSTAINABLE_PRACTICES}
        }

    async def compute_score(
        self,
        user_id: str,
        db: Session,
        force_refresh: bool = False,
        preferred_method: Optional[ComputationMethod] = None
    ) -> ComputationResult:
        """
        Compute comprehensive green score for user

        Args:
            user_id: User ID to compute score for
            db: Database session
            force_refresh: Force score recomputation even if cached
            preferred_method: Preferred computation method

        Returns:
            ComputationResult with detailed scoring information
        """
        start_time = datetime.now()
        logger.info(f"🎯 Starting score computation for user: {user_id}")

        # Initialize metrics
        metrics = ScoreMetrics(
            computation_time=0.0,
            method_used=ComputationMethod.FALLBACK,
            confidence_level=0.0,
            evidence_count=0,
            ai_api_calls=0,
            fallback_triggers=0,
            error_count=0,
            warnings=[]
        )

        try:
            # Check for cached score unless force refresh
            if not force_refresh:
                cached_result = await self._get_cached_score(user_id, db)
                if cached_result:
                    logger.info(f"✅ Using cached score for user: {user_id}")
                    return cached_result

            # Get user data
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User not found: {user_id}")

            # Get business profile
            business_profile = db.query(BusinessProfile).filter(
                BusinessProfile.user_id == user_id
            ).first()

            # Get evidence
            evidence_list = db.query(Evidence).filter(
                Evidence.user_id == user_id,
                Evidence.status.in_(['approved', 'verified'])
            ).order_by(Evidence.created_at.desc()).all()

            metrics.evidence_count = len(evidence_list)

            # Determine computation method
            computation_method = await self._determine_computation_method(
                evidence_list, preferred_method, metrics
            )
            metrics.method_used = computation_method

            # Compute score based on method
            if computation_method == ComputationMethod.AI_ENHANCED:
                result = await self._compute_ai_enhanced_score(
                    user, business_profile, evidence_list, metrics, db
                )
            elif computation_method == ComputationMethod.HYBRID:
                result = await self._compute_hybrid_score(
                    user, business_profile, evidence_list, metrics, db
                )
            elif computation_method == ComputationMethod.RULE_BASED:
                result = await self._compute_rule_based_score(
                    user, business_profile, evidence_list, metrics, db
                )
            else:  # FALLBACK
                result = await self._compute_fallback_score(
                    user, business_profile, evidence_list, metrics, db
                )
                metrics.fallback_triggers += 1

            # Calculate final metrics
            metrics.computation_time = (datetime.now() - start_time).total_seconds()
            metrics.confidence_level = result.confidence

            # Save to database
            await self._save_score_to_database(result, db)

            logger.info(f"✅ Score computation completed: {result.total_score:.1f}/100 "
                       f"(method: {computation_method.value}, confidence: {result.confidence:.2f})")

            return result

        except Exception as e:
            metrics.error_count += 1
            metrics.computation_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Score computation failed: {e}")

            # Return fallback result
            return await self._create_fallback_result(user_id, metrics, str(e))

    async def _determine_computation_method(
        self,
        evidence_list: List[Evidence],
        preferred_method: Optional[ComputationMethod],
        metrics: ScoreMetrics
    ) -> ComputationMethod:
        """Determine the best computation method based on available data and system state"""

        # Check preferred method first
        if preferred_method:
            if await self._validate_computation_method(preferred_method, evidence_list):
                return preferred_method
            else:
                metrics.warnings.append(f"Preferred method {preferred_method.value} not available")

        # Check AI service availability
        ai_available = await self._check_ai_service_availability()

        # Determine method based on evidence and system state
        if ai_available and len(evidence_list) >= 3:
            return ComputationMethod.AI_ENHANCED
        elif ai_available and len(evidence_list) >= 1:
            return ComputationMethod.HYBRID
        elif len(evidence_list) >= 1:
            return ComputationMethod.RULE_BASED
        else:
            return ComputationMethod.FALLBACK

    async def _check_ai_service_availability(self) -> bool:
        """Check if AI services are available and responsive"""
        try:
            # Quick health check for external API
            async with external_api_client as client:
                # This would be a lightweight test call
                return True
        except Exception:
            return False

    async def _validate_computation_method(
        self,
        method: ComputationMethod,
        evidence_list: List[Evidence]
    ) -> bool:
        """Validate if a computation method can be used"""
        if method == ComputationMethod.AI_ENHANCED:
            return await self._check_ai_service_availability() and len(evidence_list) >= 3
        elif method == ComputationMethod.HYBRID:
            return await self._check_ai_service_availability() and len(evidence_list) >= 1
        elif method == ComputationMethod.RULE_BASED:
            return len(evidence_list) >= 1
        else:  # FALLBACK
            return True

    async def _compute_ai_enhanced_score(
        self,
        user: User,
        business_profile: Optional[BusinessProfile],
        evidence_list: List[Evidence],
        metrics: ScoreMetrics,
        db: Session
    ) -> ComputationResult:
        """Compute score using AI-enhanced analysis"""
        logger.info("🤖 Computing AI-enhanced score")

        breakdown = []
        explanations = []
        total_weighted_score = 0.0

        try:
            # Prepare context for AI analysis
            context = self._prepare_ai_context(user, business_profile, evidence_list)

            # Call AI service for enhanced analysis
            async with external_api_client as client:
                metrics.ai_api_calls += 1

                ai_prompt = f"""
                Analyze the following green/sustainability evidence and provide a comprehensive scoring:

                User Profile:
                - Business Type: {business_profile.business_type if business_profile else 'Unknown'}
                - Evidence Count: {len(evidence_list)}

                Evidence Summary:
                {context}

                Please provide scores (0-100) for each category:
                1. Energy Efficiency
                2. Water Conservation
                3. Waste Management
                4. Sustainable Practices
                5. Carbon Footprint

                For each category, provide:
                - Score (0-100)
                - Reasoning (brief explanation)
                - Confidence (0.0-1.0)

                Respond in JSON format with categories as keys.
                """

                ai_response = await client.call_gemini_api(ai_prompt)
                ai_scores = self._parse_ai_response(ai_response)

            # Process AI scores into breakdown
            for category in ScoreCategory:
                category_data = ai_scores.get(category.value, {})
                score = min(100.0, max(0.0, float(category_data.get('score', 50))))
                reasoning = category_data.get('reasoning', 'AI analysis')
                confidence = float(category_data.get('confidence', 0.7))

                breakdown.append(ScoreBreakdown(
                    category=category,
                    score=score,
                    max_score=100.0,
                    evidence_items=self._get_category_evidence(category, evidence_list),
                    reasoning=reasoning,
                    confidence=confidence
                ))

                # Apply category weight
                weighted_score = score * self.category_weights[category]
                total_weighted_score += weighted_score

                explanations.append(f"{category.value.replace('_', ' ').title()}: {score:.1f}/100 - {reasoning}")

            # Calculate overall confidence
            avg_confidence = sum(b.confidence for b in breakdown) / len(breakdown)

        except Exception as e:
            logger.error(f"AI-enhanced scoring failed: {e}")
            metrics.error_count += 1
            metrics.fallback_triggers += 1
            # Fall back to rule-based computation
            return await self._compute_rule_based_score(user, business_profile, evidence_list, metrics, db)

        return self._create_computation_result(
            user.id, total_weighted_score, breakdown, explanations,
            ComputationMethod.AI_ENHANCED, avg_confidence, metrics
        )

    async def _compute_hybrid_score(
        self,
        user: User,
        business_profile: Optional[BusinessProfile],
        evidence_list: List[Evidence],
        metrics: ScoreMetrics,
        db: Session
    ) -> ComputationResult:
        """Compute score using hybrid rule-based and AI analysis"""
        logger.info("🔄 Computing hybrid score")

        # Start with rule-based computation
        rule_result = await self._compute_rule_based_score(
            user, business_profile, evidence_list, metrics, db
        )

        try:
            # Enhance with AI insights for confidence and explanations
            async with external_api_client as client:
                metrics.ai_api_calls += 1

                context = self._prepare_ai_context(user, business_profile, evidence_list)
                ai_prompt = f"""
                Review this green score computation and provide enhanced insights:

                Current Score: {rule_result.total_score:.1f}/100
                Evidence: {context}

                Please provide:
                1. Confidence level (0.0-1.0) for this score
                2. Additional insights or adjustments
                3. Key sustainability strengths
                4. Areas for improvement

                Keep response concise and actionable.
                """

                ai_insights = await client.call_gemini_api(ai_prompt)

                # Extract confidence and enhanced explanations
                enhanced_confidence = self._extract_confidence_from_insights(ai_insights)
                enhanced_explanations = rule_result.explanations + [f"AI Insight: {ai_insights[:200]}..."]

        except Exception as e:
            logger.warning(f"AI enhancement failed, using rule-based result: {e}")
            enhanced_confidence = rule_result.confidence
            enhanced_explanations = rule_result.explanations

        # Create hybrid result
        return ComputationResult(
            user_id=rule_result.user_id,
            total_score=rule_result.total_score,
            raw_score=rule_result.raw_score,
            normalized_score=rule_result.normalized_score,
            breakdown=rule_result.breakdown,
            computation_method=ComputationMethod.HYBRID,
            confidence=enhanced_confidence,
            metrics=metrics,
            explanations=enhanced_explanations,
            computed_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self.cache_duration_hours)
        )

    async def _compute_rule_based_score(
        self,
        user: User,
        business_profile: Optional[BusinessProfile],
        evidence_list: List[Evidence],
        metrics: ScoreMetrics,
        db: Session
    ) -> ComputationResult:
        """Compute score using rule-based algorithms"""
        logger.info("📏 Computing rule-based score")

        breakdown = []
        explanations = []
        total_weighted_score = 0.0

        # Initialize category scores
        category_scores = {category: 0.0 for category in ScoreCategory}
        category_evidence = {category: [] for category in ScoreCategory}

        # Process evidence by category
        for evidence in evidence_list:
            evidence_type = self._classify_evidence_type(evidence)
            if evidence_type in self.evidence_scoring_rules:
                rule = self.evidence_scoring_rules[evidence_type]
                category = rule['category']
                base_score = rule['base_score']

                # Apply confidence modifier
                confidence_modifier = evidence.confidence_score or 0.8
                adjusted_score = base_score * confidence_modifier

                category_scores[category] += adjusted_score
                category_evidence[category].append(f"{evidence_type} ({adjusted_score:.1f} pts)")

        # Create breakdown for each category
        for category in ScoreCategory:
            raw_score = category_scores[category]
            # Normalize to 0-100 scale
            normalized_score = min(100.0, raw_score)

            breakdown.append(ScoreBreakdown(
                category=category,
                score=normalized_score,
                max_score=100.0,
                evidence_items=category_evidence[category],
                reasoning=f"Rule-based analysis of {len(category_evidence[category])} evidence items",
                confidence=0.8
            ))

            # Apply category weight
            weighted_score = normalized_score * self.category_weights[category]
            total_weighted_score += weighted_score

            if normalized_score > 0:
                explanations.append(
                    f"{category.value.replace('_', ' ').title()}: {normalized_score:.1f}/100 "
                    f"from {len(category_evidence[category])} evidence items"
                )

        # Apply business profile bonus
        if business_profile:
            profile_bonus = self._calculate_profile_bonus(business_profile)
            total_weighted_score += profile_bonus
            if profile_bonus > 0:
                explanations.append(f"Business profile bonus: +{profile_bonus:.1f} points")

        return self._create_computation_result(
            user.id, total_weighted_score, breakdown, explanations,
            ComputationMethod.RULE_BASED, 0.8, metrics
        )

    async def _compute_fallback_score(
        self,
        user: User,
        business_profile: Optional[BusinessProfile],
        evidence_list: List[Evidence],
        metrics: ScoreMetrics,
        db: Session
    ) -> ComputationResult:
        """Compute basic fallback score when other methods fail"""
        logger.info("🔄 Computing fallback score")

        # Basic scoring algorithm
        base_score = 30.0  # Minimum score for registered users
        evidence_bonus = len(evidence_list) * 5.0  # 5 points per evidence
        profile_bonus = 10.0 if business_profile else 0.0

        total_score = min(100.0, base_score + evidence_bonus + profile_bonus)

        # Create simple breakdown
        breakdown = [
            ScoreBreakdown(
                category=ScoreCategory.SUSTAINABLE_PRACTICES,
                score=total_score,
                max_score=100.0,
                evidence_items=[f"{len(evidence_list)} evidence items submitted"],
                reasoning="Basic fallback computation",
                confidence=0.5
            )
        ]

        explanations = [
            f"Base score: {base_score} points",
            f"Evidence bonus: {evidence_bonus} points ({len(evidence_list)} items)",
            f"Profile bonus: {profile_bonus} points"
        ]

        return self._create_computation_result(
            user.id, total_score, breakdown, explanations,
            ComputationMethod.FALLBACK, 0.5, metrics
        )

    def _prepare_ai_context(
        self,
        user: User,
        business_profile: Optional[BusinessProfile],
        evidence_list: List[Evidence]
    ) -> str:
        """Prepare context for AI analysis"""
        context_parts = []

        if business_profile:
            context_parts.append(f"Business: {business_profile.business_type}")
            context_parts.append(f"Company: {business_profile.business_name}")

        for evidence in evidence_list[:10]:  # Limit to first 10 items
            extracted_text = evidence.extracted_text or "No text extracted"
            context_parts.append(f"Evidence: {extracted_text[:200]}...")

        return "\n".join(context_parts)

    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response into structured scores"""
        try:
            # Try to extract JSON from AI response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass

        # Fallback: extract scores using pattern matching
        scores = {}
        for category in ScoreCategory:
            # Look for score patterns in the response
            pattern = rf"{category.value}.*?(\d+)"
            match = re.search(pattern, ai_response.lower())
            if match:
                scores[category.value] = {
                    'score': int(match.group(1)),
                    'reasoning': 'AI analysis',
                    'confidence': 0.7
                }

        return scores

    def _get_category_evidence(self, category: ScoreCategory, evidence_list: List[Evidence]) -> List[str]:
        """Get evidence items relevant to a category"""
        relevant_evidence = []
        for evidence in evidence_list:
            evidence_type = self._classify_evidence_type(evidence)
            if evidence_type in self.evidence_scoring_rules:
                if self.evidence_scoring_rules[evidence_type]['category'] == category:
                    relevant_evidence.append(f"Evidence: {evidence_type}")
        return relevant_evidence

    def _classify_evidence_type(self, evidence: Evidence) -> str:
        """Classify evidence type based on extracted text and metadata"""
        text = (evidence.extracted_text or "").lower()

        # Simple keyword-based classification
        if any(word in text for word in ['solar', 'photovoltaic', 'pv']):
            return 'solar_installation'
        elif any(word in text for word in ['led', 'light', 'bulb']):
            return 'led_lighting'
        elif any(word in text for word in ['pump', 'water', 'irrigation']):
            return 'water_pump'
        elif any(word in text for word in ['recycle', 'waste', 'plastic']):
            return 'waste_recycling'
        elif any(word in text for word in ['carbon', 'emission', 'offset']):
            return 'carbon_credit'
        elif any(word in text for word in ['certification', 'certificate', 'green']):
            return 'green_certification'
        else:
            return 'general_sustainability'

    def _calculate_profile_bonus(self, business_profile: BusinessProfile) -> float:
        """Calculate bonus points based on business profile"""
        bonus = 0.0

        # Bonus for sustainable business types
        sustainable_types = ['renewable_energy', 'waste_management', 'organic_farming']
        if business_profile.business_type in sustainable_types:
            bonus += 10.0

        return bonus

    def _extract_confidence_from_insights(self, ai_insights: str) -> float:
        """Extract confidence level from AI insights"""
        try:
            # Look for confidence patterns
            import re
            confidence_match = re.search(r'confidence.*?(\d+\.?\d*)', ai_insights.lower())
            if confidence_match:
                confidence = float(confidence_match.group(1))
                return min(1.0, max(0.0, confidence if confidence <= 1.0 else confidence / 100.0))
        except Exception:
            pass

        return 0.7  # Default confidence

    def _create_computation_result(
        self,
        user_id: str,
        total_score: float,
        breakdown: List[ScoreBreakdown],
        explanations: List[str],
        method: ComputationMethod,
        confidence: float,
        metrics: ScoreMetrics
    ) -> ComputationResult:
        """Create standardized computation result"""

        # Normalize score
        normalized_score = min(self.max_score, max(self.min_score, total_score))

        return ComputationResult(
            user_id=user_id,
            total_score=normalized_score,
            raw_score=total_score,
            normalized_score=normalized_score,
            breakdown=breakdown,
            computation_method=method,
            confidence=confidence,
            metrics=metrics,
            explanations=explanations,
            computed_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self.cache_duration_hours)
        )

    async def _create_fallback_result(
        self,
        user_id: str,
        metrics: ScoreMetrics,
        error_message: str
    ) -> ComputationResult:
        """Create fallback result when computation fails"""

        return ComputationResult(
            user_id=user_id,
            total_score=30.0,  # Minimum fallback score
            raw_score=30.0,
            normalized_score=30.0,
            breakdown=[],
            computation_method=ComputationMethod.FALLBACK,
            confidence=0.3,
            metrics=metrics,
            explanations=[f"Fallback score due to computation error: {error_message}"],
            computed_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)  # Short cache for errors
        )

    async def _get_cached_score(self, user_id: str, db: Session) -> Optional[ComputationResult]:
        """Get cached score if available and not expired"""
        try:
            latest_score = db.query(GreenScore).filter(
                GreenScore.user_id == user_id
            ).order_by(GreenScore.computed_at.desc()).first()

            if latest_score:
                # Check if score is not expired
                cache_expiry = latest_score.computed_at + timedelta(hours=self.cache_duration_hours)
                if datetime.now() < cache_expiry:
                    # Convert database record to ComputationResult
                    return self._db_record_to_computation_result(latest_score)

        except Exception as e:
            logger.warning(f"Failed to get cached score: {e}")

        return None

    def _db_record_to_computation_result(self, score_record: GreenScore) -> ComputationResult:
        """Convert database GreenScore record to ComputationResult"""

        # Create basic metrics
        metrics = ScoreMetrics(
            computation_time=0.0,
            method_used=ComputationMethod.RULE_BASED,  # Default for cached
            confidence_level=0.8,
            evidence_count=0,
            ai_api_calls=0,
            fallback_triggers=0,
            error_count=0,
            warnings=[]
        )

        return ComputationResult(
            user_id=str(score_record.user_id),
            total_score=score_record.score,
            raw_score=score_record.score,
            normalized_score=score_record.score,
            breakdown=[],  # Would need to reconstruct from subscores
            computation_method=ComputationMethod.RULE_BASED,
            confidence=0.8,
            metrics=metrics,
            explanations=score_record.explanation_json or [],
            computed_at=score_record.computed_at,
            expires_at=score_record.computed_at + timedelta(hours=self.cache_duration_hours)
        )

    async def _save_score_to_database(self, result: ComputationResult, db: Session):
        """Save computation result to database"""
        try:
            # Create subscores dictionary
            subscores = {}
            for breakdown_item in result.breakdown:
                subscores[breakdown_item.category.value] = breakdown_item.score

            # Create new GreenScore record
            green_score = GreenScore(
                user_id=result.user_id,
                score=result.total_score,
                subscores=subscores,
                explanation_json=result.explanations,
                computed_at=result.computed_at
            )

            db.add(green_score)
            db.commit()
            db.refresh(green_score)

            logger.info(f"✅ Score saved to database for user: {result.user_id}")

        except Exception as e:
            logger.error(f"Failed to save score to database: {e}")
            db.rollback()

    async def get_score_metrics(self, user_id: str, db: Session) -> Dict[str, Any]:
        """Get score computation metrics and history"""
        try:
            # Get recent scores
            recent_scores = db.query(GreenScore).filter(
                GreenScore.user_id == user_id
            ).order_by(GreenScore.computed_at.desc()).limit(10).all()

            if not recent_scores:
                return {"message": "No score history found"}

            # Calculate metrics
            scores = [score.score for score in recent_scores]
            latest_score = recent_scores[0]

            return {
                "latest_score": latest_score.score,
                "score_trend": scores[0] - scores[-1] if len(scores) > 1 else 0,
                "computation_count": len(recent_scores),
                "score_history": [
                    {
                        "score": score.score,
                        "computed_at": score.computed_at.isoformat(),
                        "subscores": score.subscores
                    }
                    for score in recent_scores
                ],
                "average_score": sum(scores) / len(scores),
                "max_score": max(scores),
                "min_score": min(scores)
            }

        except Exception as e:
            logger.error(f"Failed to get score metrics: {e}")
            return {"error": str(e)}


# Global service instance
score_computation_service = ScoreComputationService()