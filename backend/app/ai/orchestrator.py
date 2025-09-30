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
            result.review_required = self._requires_human_review(result)

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
                explainers=[f"Processing error: {str(e)}"],
                actions=[],
                processing_time_ms=processing_time * 1000,
                review_required=True,  # Always require review for failed processing
                error_details=str(e)
            )

    async def _llm_orchestrated_processing(self, request: AIOrchestrationRequest, api_client) -> AIOrchestrationResult:
        """LLM-guided processing with function calling"""
        start_time = datetime.now()
        
        try:
            # Create context for LLM
            context = self._build_context(request)

            # System prompt for the orchestrator LLM
            system_prompt = """You are an AI orchestrator for GreenCredit Score calculation.
            Your role is to analyze evidence of sustainable business practices and coordinate
            microservices to calculate accurate GreenScores and carbon credits.

            Analyze the evidence step by step:
            1. Identify what type of sustainable action this evidence represents
            2. Extract quantitative information (costs, quantities, timeframes)
            3. Calculate environmental impact and CO2 savings
            4. Determine GreenScore contribution (0-100 scale)
            5. Provide specific improvement recommendations

            Return a JSON response with:
            {
                "greenscore": 75,
                "subscores": {"energy": 80, "water": 70, "waste": 75, "behavior": 80},
                "co2_saved_tonnes": 1.2,
                "confidence": 0.85,
                "explainers": ["Solar panel installation saves 1.2 tonnes CO2/year"],
                "actions": ["Consider adding battery storage for +10 points"]
            }"""

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

            # Call Gemini API through external client
            gemini_response = await api_client.call_gemini_api(prompt)

            # Parse JSON response
            try:
                import json
                result_data = json.loads(gemini_response)
            except json.JSONDecodeError:
                logger.warning("Failed to parse Gemini JSON response, using deterministic fallback")
                result_data = await self._deterministic_processing(request)
                result_data = result_data.__dict__

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return AIOrchestrationResult(
                evidence_id=request.evidence.evidence_id,
                user_id=request.evidence.user_id,
                greenscore=result_data.get("greenscore", 50),
                subscores=result_data.get("subscores", {}),
                co2_saved_tonnes=result_data.get("co2_saved_tonnes", 0.0),
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

    async def _deterministic_processing(self, request: AIOrchestrationRequest) -> AIOrchestrationResult:
        """Fallback deterministic processing without LLM"""
        start_time = datetime.now()
        
        try:
            # Step 1: Process evidence (already processed)
            ocr_result = request.evidence.ocr
            cv_result = request.evidence.cv
            features = getattr(request.evidence, "features", None)

            # Step 2: Calculate emissions
            emission_result = await self.emission_calculator.calculate_emissions(
                evidence_id=request.evidence.evidence_id,
                sector=request.sector,
                region=request.region,
                ocr_result=ocr_result,
                cv_result=cv_result,
                features=features,
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
