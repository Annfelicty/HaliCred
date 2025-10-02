"""
AI Orchestrator with LLM Function Calling
Coordinates evidence processing, scoring, and carbon credit calculation
Enhanced for production with external API integration and reliability patterns
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import time

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .models import (
    EvidenceData, OCRResult, CVResult, EmissionResult,
    GreenScoreResult, CarbonCredit, AIOrchestrationRequest, AIOrchestrationResult,
    EmissionFeatures,
)
from .evidence_processor import EvidenceProcessor
from .emission_calculator import EmissionCalculator
from .score_computer import ScoreComputer
from .sector_baseline import SectorBaselineService
from .carbon_credit import CarbonCreditAggregator
from .api_client import external_api_client

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """LLM-powered orchestrator that coordinates AI microservices"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AI Orchestrator with production configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Use external API client for all AI services
        self.api_client = external_api_client

        # Initialize microservices
        self.evidence_processor = EvidenceProcessor()
        self.emission_calculator = EmissionCalculator()
        self.score_computer = ScoreComputer()
        self.sector_baseline = SectorBaselineService()
        self.carbon_credit_aggregator = CarbonCreditAggregator()

        # Processing metrics
        self.processing_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0
        }

        # Confidence thresholds for human review
        self.confidence_thresholds = {
            "low_confidence": 0.6,
            "medium_confidence": 0.8,
            "high_confidence": 0.9
        }

        # Function definitions for Gemini function calling
        self.available_functions = {
            "process_evidence": self._process_evidence,
            "calculate_emissions": self._calculate_emissions,
            "compute_greenscore": self._compute_greenscore,
            "calculate_carbon_credits": self._calculate_carbon_credits,
            "get_sector_baseline": self._get_sector_baseline,
            "estimate_user_metrics": self._estimate_user_metrics,
            "validate_evidence_quality": self._validate_evidence_quality
        }
        
        # Simplified function declarations for compatibility
        self.function_declarations = None
        self.function_tool = None

    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time metric"""
        total = self.processing_metrics["total_requests"]
        current_avg = self.processing_metrics["average_processing_time"]

        # Calculate new average
        new_avg = ((current_avg * (total - 1)) + processing_time) / total
        self.processing_metrics["average_processing_time"] = new_avg

    def _requires_human_review(self, result: AIOrchestrationResult) -> bool:
        """Determine if result requires human review based on confidence and other factors"""

        # Low confidence always requires review
        if result.confidence < self.confidence_thresholds["low_confidence"]:
            logger.info(f"🔍 Human review required: Low confidence ({result.confidence:.2f})")
            return True

        # High-value claims require review
        if result.co2_saved_tonnes > 5.0:  # Threshold for high-impact claims
            logger.info(f"🔍 Human review required: High-value claim ({result.co2_saved_tonnes} tonnes CO2)")
            return True

        # Unusual score changes require review
        if result.greenscore > 90:  # Very high scores
            logger.info(f"🔍 Human review required: Very high score ({result.greenscore})")
            return True

        # No review needed
        return False

    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get current processing metrics"""
        total = self.processing_metrics["total_requests"]
        if total == 0:
            return {**self.processing_metrics, "success_rate": 0.0}

        success_rate = (self.processing_metrics["successful_requests"] / total) * 100

        return {
            **self.processing_metrics,
            "success_rate": success_rate,
            "failure_rate": 100 - success_rate
        }

    async def process_request(self, request: AIOrchestrationRequest) -> AIOrchestrationResult:
        """Main orchestration method - processes AI request end-to-end with monitoring"""
        start_time = time.time()
        processing_id = f"{request.evidence.user_id}_{request.evidence.evidence_id}_{int(start_time)}"

        # Update metrics
        self.processing_metrics["total_requests"] += 1

        try:
            logger.info(f"🔄 Processing AI request {processing_id}")
            logger.info(f"📊 User: {request.evidence.user_id}, Evidence: {request.evidence.evidence_id}")

            # Check if external API client is available
            async with self.api_client as client:
                # Attempt Gemini-powered processing first
                try:
                    result = await self._llm_orchestrated_processing(request, client)
                    logger.info(f"✅ LLM processing successful for {processing_id}")
                except Exception as llm_error:
                    logger.warning(f"⚠️ LLM processing failed for {processing_id}: {llm_error}")
                    logger.info(f"🔄 Falling back to deterministic processing")
                    result = await self._deterministic_processing(request)

            # Calculate processing time
            processing_time = time.time() - start_time
            result.processing_time_ms = processing_time * 1000

            # Update metrics
            self.processing_metrics["successful_requests"] += 1
            self._update_average_processing_time(processing_time)

            # Evaluate confidence and determine if human review is needed
            result.requires_human_review = self._requires_human_review(result)

            logger.info(f"✅ Processing complete for {processing_id} in {processing_time:.2f}s")
            logger.info(f"📈 Score: {result.greenscore}, Confidence: {result.confidence:.2f}")

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.processing_metrics["failed_requests"] += 1

            logger.error(f"💥 Processing failed for {processing_id}: {str(e)}")

            return AIOrchestrationResult(
                evidence_id=request.evidence.evidence_id,
                user_id=request.evidence.user_id,
                greenscore=0,
                subscores={},
                co2_saved_tonnes=0.0,
                confidence=0.0,
                explainers=[f"Processing error: {str(e)}"],  # List, not JSON string
                actions=[],  # List, not JSON string
                processing_time_ms=processing_time * 1000,
                requires_human_review=True,  # Correct field name
                provenance={"error_details": str(e)}  # Store error in provenance
            )

    async def _llm_orchestrated_processing(self, request: AIOrchestrationRequest, api_client) -> AIOrchestrationResult:
        """LLM-guided processing with function calling"""
        start_time = datetime.now()
        
        try:
            # Create context for LLM
            context = self._build_context(request)

            # Enhanced system prompt with detailed scoring guidance
            system_prompt = """You are an AI orchestrator for GreenCredit Score calculation in Kenya.
            Your role is to analyze evidence of sustainable business practices and calculate GreenScores fairly and consistently.

            SCORING PHILOSOPHY (Financial Product - Be Fair, Not Generous):
            - ONLY SCORE VERIFIABLE ECO-ACTIONS: Evidence must show clear sustainability investment or practice
            - SCORE RANGES:
              * 0-5 points: Minimal/unclear evidence, low-value actions (e.g., single LED bulb receipt)
              * 6-15 points: Basic sustainable practice with clear evidence (e.g., LED lighting set, small solar panel)
              * 16-25 points: Significant eco-investment with strong proof (e.g., solar system with invoice, drip irrigation)
              * 26-35 points: Major sustainability initiative with detailed documentation (e.g., biogas system, large solar array)
            - GIVE 0 POINTS: If evidence is unrelated, duplicate, unclear, or appears fraudulent
            - QUALITY MATTERS: Receipts + photos = higher score than photos alone

            EVIDENCE CATEGORIES & BASE SCORES:
            1. **Solar/Renewable Energy**: 15-30 points (panels, biogas, wind)
            2. **LED/Energy Efficiency**: 10-20 points (LED bulbs, efficient motors, insulation)
            3. **Water Conservation**: 10-25 points (rainwater harvest, drip irrigation, water recycling)
            4. **Waste Management**: 10-20 points (recycling, composting, waste reduction)
            5. **Sustainable Sourcing**: 8-18 points (organic inputs, local suppliers, eco-packaging)
            6. **Receipts/Purchases**: 8-15 points (show intent even if not installed yet)
            7. **Before/After Photos**: 12-22 points (demonstrate actual implementation)
            8. **Meters/Monitoring**: 10-20 points (shows data-driven sustainability)

            SECTOR-SPECIFIC PRIORITIES:
            - Agriculture: Water systems (25 pts), Solar pumps (30 pts), Organic fertilizer (15 pts)
            - Salon/Beauty: LED lighting (18 pts), Water recycling (20 pts), Eco-products (12 pts)
            - Welding/Manufacturing: Solar power (28 pts), Efficient equipment (22 pts), Scrap recycling (15 pts)
            - Transport: Electric/Hybrid vehicles (35 pts), Route optimization (10 pts), Maintenance logs (8 pts)
            - Other: General eco-actions (10-20 pts based on impact)

            CONFIDENCE SCORING:
            - High (0.7-0.95): Clear equipment visible, receipts with details, meter readings
            - Medium (0.5-0.69): Photos without receipts, unclear equipment, general sustainability
            - Low (0.3-0.49): Minimal evidence, could be misidentified
            - NEVER 0.0 confidence unless score is 0

            CO2 ESTIMATION (Kenya context - for informational explainers):
            - Solar panel (per kW): 1.2 tonnes CO2/year (Kenya grid: 0.6 kg CO2/kWh)
            - LED bulb (vs incandescent): 0.05 tonnes CO2/year per bulb
            - Drip irrigation: 0.3 tonnes CO2/year (reduces pump usage)
            - Biogas digester: 2.5 tonnes CO2/year (replaces firewood/charcoal)
            - Water recycling: 0.2 tonnes CO2/year (reduces pumping)

            NOTE: Provide rough co2_saved_tonnes estimate for context. Final CO2 calculations use real-time Climatiq API data.

            CRITICAL: Return ONLY valid JSON, no explanatory text before or after.

            Required JSON format (use EXACT keys):
            {
                "greenscore": 18,
                "subscores": {
                    "energy_efficiency": 25,
                    "water_conservation": 15,
                    "waste_management": 20,
                    "renewable_energy": 22
                },
                "co2_saved_tonnes": 0.8,
                "confidence": 0.65,
                "explainers": ["LED lighting installation saves 0.8 tonnes CO2/year, reducing energy costs by ~30%"],
                "actions": ["Add solar panels to power LEDs for +15 points and greater CO2 reduction"]
            }

            SUBSCORE GUIDELINES (0-100 scale for each category):
            1. **energy_efficiency**: LED lighting, efficient appliances, insulation, smart systems
            2. **water_conservation**: Rainwater harvest, drip irrigation, recycling, efficient fixtures
            3. **waste_management**: Recycling, composting, waste reduction, proper disposal
            4. **renewable_energy**: Solar panels, biogas, wind power, solar pumps, battery storage

            Return ONLY the JSON object above, nothing else."""

            # Build comprehensive prompt
            prompt = f"""
            {system_prompt}

            Evidence to analyze:
            - Type: {request.evidence.type}
            - Sector: {request.sector}
            - Region: {request.region}
            - File: {request.evidence.evidence_id}
            - Context: {context}

            Please analyze this evidence and provide a detailed GreenScore assessment.
            """

            # Call Gemini API through external client with retry logic
            import json
            import re

            gemini_response = None
            max_retries = 2

            for attempt in range(max_retries):
                try:
                    gemini_response = await api_client.call_gemini_api(prompt)

                    # Check if response is empty
                    if not gemini_response or not gemini_response.strip():
                        logger.warning(f"Gemini returned empty response (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            continue
                        else:
                            raise ValueError("Empty response from Gemini after retries")

                    response_text = gemini_response.strip()

                    # Strip markdown code fences if present (Gemini wraps JSON in ```json ... ```)
                    if response_text.startswith("```"):
                        # Remove ```json at start
                        response_text = re.sub(r'^```(?:json|JSON)?\s*\n?', '', response_text)
                        # Remove ``` at end
                        response_text = re.sub(r'\n?\s*```\s*$', '', response_text)
                        response_text = response_text.strip()

                    # Try to parse JSON
                    result_data = json.loads(response_text)
                    logger.info(f"✅ Successfully parsed Gemini JSON response (attempt {attempt + 1})")
                    break  # Success, exit retry loop

                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse Gemini response (attempt {attempt + 1}/{max_retries}): {e}")
                    if gemini_response:
                        logger.error(f"Full Gemini response: {gemini_response}")

                    if attempt < max_retries - 1:
                        logger.info("Retrying Gemini API call...")
                        continue
                    else:
                        logger.warning("All retries exhausted, using deterministic fallback")
                        result_data = await self._deterministic_processing(request)
                        result_data = result_data.__dict__

            # Calculate emissions using real-time Climatiq data (instead of Gemini's estimate)
            features = getattr(request.evidence, "features", None)
            if not features:
                from app.ai.models import EmissionFeatures
                features = EmissionFeatures()

            emission_result = await self.emission_calculator.calculate_emissions(
                evidence_id=request.evidence.evidence_id,
                sector=request.sector,
                features=features,
                region=request.region,
            )

            # Replace Gemini's CO2 estimate with Climatiq-calculated value
            calculated_co2_tonnes = emission_result.co2_kg_total / 1000.0  # Convert kg to tonnes
            logger.info(f"🌍 Climatiq CO2 calculation: {calculated_co2_tonnes:.3f} tonnes (method: {emission_result.method})")

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return AIOrchestrationResult(
                evidence_id=request.evidence.evidence_id,
                user_id=request.evidence.user_id,
                greenscore=result_data.get("greenscore", 50),
                subscores=result_data.get("subscores", {}),
                co2_saved_tonnes=calculated_co2_tonnes,  # Use Climatiq calculation, not Gemini estimate
                confidence=result_data.get("confidence", 0.8),
                explainers=result_data.get("explainers", []),
                actions=result_data.get("actions", []),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in LLM orchestration: {str(e)}")
            # Fallback to deterministic processing
            return await self._deterministic_processing(request)

    async def _execute_llm_workflow(self, prompt: str, request: AIOrchestrationRequest) -> Dict[str, Any]:
        """Execute the Gemini workflow with function calling"""
        max_iterations = 10
        iteration = 0
        
        ocr_result = None
        cv_result = None
        emission_result = None
        greenscore_result = None
        carbon_credits = []
        
        # Start chat with function calling enabled
        chat = self.model.start_chat(
            history=[],
            tools=[self.function_tool]
        )
        
        while iteration < max_iterations:
            try:
                if iteration == 0:
                    response = chat.send_message(prompt)
                else:
                    response = chat.send_message("Continue processing based on the function results.")
                
                # Check if Gemini wants to call a function
                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call'):
                            function_call = part.function_call
                            function_name = function_call.name
                            function_args = dict(function_call.args)
                            
                            logger.info(f"Gemini calling function: {function_name}")
                            
                            if function_name in self.available_functions:
                                function_result = await self.available_functions[function_name](**function_args)
                                
                                # Store results
                                if function_name == "process_evidence":
                                    ocr_result = function_result.get("ocr_result")
                                    cv_result = function_result.get("cv_result")
                                elif function_name == "calculate_emissions":
                                    emission_result = function_result
                                elif function_name == "compute_greenscore":
                                    greenscore_result = function_result
                                elif function_name == "calculate_carbon_credits":
                                    carbon_credits = function_result
                                
                                # Send function result back to Gemini
                                function_response = genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_name,
                                        response={"result": function_result}
                                    )
                                )
                                
                                response = chat.send_message(function_response)
                            else:
                                # Function not available
                                function_response = genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_name,
                                        response={"error": "Function not available"}
                                    )
                                )
                                response = chat.send_message(function_response)
                        
                        elif hasattr(part, 'text'):
                            # Gemini finished processing
                            explanation = part.text
                            break
                else:
                    break
                
                iteration += 1
                
            except Exception as e:
                logger.error(f"Error in Gemini iteration {iteration}: {str(e)}")
                break
        
        return {
            "greenscore_result": greenscore_result,
            "carbon_credits": carbon_credits,
            "explanation": explanation if 'explanation' in locals() else "Processing completed",
            "confidence": greenscore_result.confidence if greenscore_result else 0.5
        }

    def _build_context(self, request: AIOrchestrationRequest) -> str:
        """Build context string from evidence for LLM processing"""
        context_parts = []

        # OCR results
        if request.evidence.ocr and request.evidence.ocr.raw_text:
            context_parts.append(f"OCR Text: {request.evidence.ocr.raw_text[:500]}")  # Limit length
            if request.evidence.ocr.vendor:
                context_parts.append(f"Vendor: {request.evidence.ocr.vendor}")
            if request.evidence.ocr.amount_ksh:
                context_parts.append(f"Amount: KSH {request.evidence.ocr.amount_ksh}")

        # Computer Vision results
        if request.evidence.cv and request.evidence.cv.labels:
            context_parts.append(f"Detected: {', '.join(request.evidence.cv.labels[:10])}")

        # Features
        if request.evidence.features:
            features_list = []
            if request.evidence.features.solar_kwh_generated:
                features_list.append(f"Solar: {request.evidence.features.solar_kwh_generated} kWh/year")
            if request.evidence.features.kwh_saved:
                features_list.append(f"Energy Saved: {request.evidence.features.kwh_saved} kWh")
            if request.evidence.features.water_m3_saved:
                features_list.append(f"Water Saved: {request.evidence.features.water_m3_saved} m³")
            if features_list:
                context_parts.append("Features: " + ", ".join(features_list))

        # User profile
        if request.user_profile:
            profile_info = [f"{k}: {v}" for k, v in request.user_profile.items() if k != "user_id"]
            if profile_info:
                context_parts.append("User: " + ", ".join(profile_info[:5]))

        return " | ".join(context_parts) if context_parts else "No additional context"

    async def _deterministic_processing(self, request: AIOrchestrationRequest) -> AIOrchestrationResult:
        """Fallback deterministic processing without LLM"""
        start_time = datetime.now()
        
        try:
            # Step 1: Process evidence (already processed)
            ocr_result = request.evidence.ocr
            cv_result = request.evidence.cv
            features = getattr(request.evidence, "features", None)

            # Step 2: Calculate emissions
            # Note: EmissionCalculator only needs features, not raw OCR/CV results
            if not features:
                # If no features extracted, create empty EmissionFeatures
                from app.ai.models import EmissionFeatures
                features = EmissionFeatures()

            emission_result = await self.emission_calculator.calculate_emissions(
                evidence_id=request.evidence.evidence_id,
                sector=request.sector,
                features=features,
                region=request.region,
            )

            # Step 3: Estimate user metrics
            user_metrics = self.score_computer.estimate_user_metrics_from_evidence(
                emission_result=emission_result,
                sector=request.sector,
                ocr_data=ocr_result.model_dump() if ocr_result else {},
                cv_data=cv_result.model_dump() if cv_result else {},
                features=features,
            )

            # Step 4: Compute GreenScore
            greenscore_result = await self.score_computer.compute_score(
                user_id=request.evidence.user_id,
                evidence_id=request.evidence.evidence_id,
                sector=request.sector,
                emission_result=emission_result,
                user_metrics=user_metrics,
                region=request.region,
            )

            # Step 5: Calculate carbon credits
            carbon_credits = await self.carbon_credit_aggregator.calculate_carbon_credits(
                user_id=request.evidence.user_id,
                evidence_id=request.evidence.evidence_id,
                emission_result=emission_result,
                greenscore_result=greenscore_result,
                sector=request.sector,
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return AIOrchestrationResult(
                evidence_id=request.evidence.evidence_id,
                user_id=request.evidence.user_id,
                greenscore=greenscore_result.greenscore,
                subscores=greenscore_result.subscores,
                co2_saved_tonnes=greenscore_result.co2_saved_tonnes,
                confidence=greenscore_result.confidence,
                explainers=greenscore_result.explainers,
                actions=greenscore_result.actions,
                carbon_credits=carbon_credits[0] if carbon_credits else None,
                provenance={"processing_time_ms": processing_time},
            )

        except Exception as exc:
            logger.error("Error in deterministic processing: %s", exc)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return AIOrchestrationResult(
                evidence_id=request.evidence.evidence_id,
                user_id=request.evidence.user_id,
                greenscore=0,
                subscores={},
                co2_saved_tonnes=0.0,
                confidence=0.0,
                explainers=[f"Error: {exc}"],
                actions=[],
                provenance={"processing_time_ms": processing_time},
            )

    async def _calculate_emissions(
        self,
        evidence_id: str,
        ocr_result: Dict[str, Any],
        cv_result: Dict[str, Any],
        sector: str,
        region: str = "Kenya",
        features: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculate emissions wrapper for LLM"""
        ocr_obj = OCRResult(**ocr_result) if ocr_result else None
        cv_obj = CVResult(**cv_result) if cv_result else None
        
        features_obj = EmissionFeatures(**features) if features else None

        result = await self.emission_calculator.calculate_emissions(
            evidence_id=evidence_id,
            sector=sector,
            region=region,
            ocr_result=ocr_obj,
            cv_result=cv_obj,
            features=features_obj,
        )
        return result.model_dump()

    async def _process_evidence(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Process evidence wrapper for LLM compatibility."""
        evidence_obj = EvidenceData(**evidence)
        processed = await self.evidence_processor.process_evidence(evidence_obj)
        return {
            "ocr_result": processed.ocr.model_dump() if processed.ocr else None,
            "cv_result": processed.cv.model_dump() if processed.cv else None,
            "features": processed.features.model_dump() if processed.features else None,
        }

    async def _compute_greenscore(
        self,
        user_id: str,
        evidence_id: str,
        sector: str,
        emission_result: Dict[str, Any],
        user_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute GreenScore wrapper for LLM"""
        emission_obj = EmissionResult(**emission_result)
        
        result = await self.score_computer.compute_score(
            user_id=user_id,
            evidence_id=evidence_id,
            sector=sector,
            emission_result=emission_obj,
            user_metrics=user_metrics
        )
        return result.dict()

    async def _calculate_carbon_credits(
        self,
        user_id: str,
        evidence_id: str,
        emission_result: Dict[str, Any],
        greenscore_result: Dict[str, Any],
        sector: str
    ) -> List[Dict[str, Any]]:
        """Calculate carbon credits wrapper for LLM"""
        emission_obj = EmissionResult(**emission_result)
        greenscore_obj = GreenScoreResult(**greenscore_result)
        
        credits = await self.carbon_credit_aggregator.calculate_carbon_credits(
            user_id=user_id,
            evidence_id=evidence_id,
            emission_result=emission_obj,
            greenscore_result=greenscore_obj,
            sector=sector
        )
        return [credit.dict() for credit in credits]

    async def _get_sector_baseline(self, sector: str, region: str = "Kenya") -> Dict[str, Any]:
        """Get sector baseline wrapper for LLM"""
        baseline = await self.sector_baseline.get_baseline(sector, region)
        return baseline.dict()

    async def _estimate_user_metrics(
        self,
        emission_result: Dict[str, Any],
        sector: str,
        ocr_data: Dict[str, Any],
        cv_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate user metrics wrapper for LLM"""
        emission_obj = EmissionResult(**emission_result)
        
        metrics = self.score_computer.estimate_user_metrics_from_evidence(
            emission_result=emission_obj,
            sector=sector,
            ocr_data=ocr_data,
            cv_data=cv_data
        )
        return metrics

    async def _validate_evidence_quality(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Validate evidence quality for human-in-loop triggers"""
        try:
            # Basic quality checks
            quality_score = 0.8  # Default
            issues = []
            
            # Check file size and format
            if evidence.get("file_size_mb", 0) < 0.1:
                quality_score -= 0.2
                issues.append("File size too small")
            
            if evidence.get("file_size_mb", 0) > 50:
                quality_score -= 0.1
                issues.append("File size very large")
            
            # Check metadata completeness
            if not evidence.get("geolocation"):
                quality_score -= 0.1
                issues.append("No location data")
            
            return {
                "quality_score": max(0.0, quality_score),
                "issues": issues,
                "human_review_required": quality_score < 0.6
            }
            
        except Exception as e:
            return {
                "quality_score": 0.3,
                "issues": [f"Validation error: {str(e)}"],
                "human_review_required": True
            }
