"""
AI Orchestrator with LLM Function Calling
Coordinates evidence processing, scoring, and carbon credit calculation
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .models import (
    EvidenceData, OCRResult, CVResult, EmissionResult, 
    GreenScoreResult, CarbonCredit, AIOrchestrationRequest, AIOrchestrationResult
)
from .evidence_processor import EvidenceProcessor
from .emission_calculator import EmissionCalculator
from .score_computer import ScoreComputer
from .sector_baseline import SectorBaselineService
from .carbon_credit import CarbonCreditAggregator

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """LLM-powered orchestrator that coordinates AI microservices"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AI Orchestrator with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini AI if available
        if genai:
            genai.configure(api_key=config.get('gemini_api_key', ''))
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
        
        # Initialize microservices
        self.evidence_processor = EvidenceProcessor()
        self.emission_calculator = EmissionCalculator()
        self.score_computer = ScoreComputer()
        self.sector_baseline = SectorBaselineService()
        self.carbon_credit_aggregator = CarbonCreditAggregator()
        
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

    async def process_request(self, request: AIOrchestrationRequest) -> AIOrchestrationResult:
        """Main orchestration method - processes AI request end-to-end"""
        try:
            logger.info(f"Processing AI request for user {request.evidence.user_id}, evidence {request.evidence.evidence_id}")
            
            # If Gemini is available, use LLM orchestration
            if self.model:
                return await self._llm_orchestrated_processing(request)
            else:
                # Fallback to deterministic processing
                return await self._deterministic_processing(request)
                
        except Exception as e:
            logger.error(f"Error in AI orchestration: {str(e)}")
            return AIOrchestrationResult(
                evidence_id=request.evidence.evidence_id,
                user_id=request.evidence.user_id,
                greenscore=0,
                subscores={},
                co2_saved_tonnes=0.0,
                confidence=0.0,
                explainers=[f"Error: {str(e)}"],
                actions=[]
            )

    async def _llm_orchestrated_processing(self, request: AIOrchestrationRequest) -> AIOrchestrationResult:
        """LLM-guided processing with function calling"""
        start_time = datetime.now()
        
        try:
            # Create context for LLM
            context = self._build_context(request)
            
            # System prompt for the orchestrator LLM
            system_prompt = """You are an AI orchestrator for GreenCredit Score calculation. 
            Your role is to analyze evidence of sustainable business practices and coordinate 
            microservices to calculate accurate GreenScores and carbon credits.

            Process flow:
            1. Process evidence using OCR and computer vision
            2. Calculate CO2 emissions from the evidence
            3. Estimate user sustainability metrics
            4. Compute GreenScore using sector baselines
            5. Calculate eligible carbon credits
            
            Always call functions in logical order and use results from previous functions.
            Be thorough but efficient. Provide clear explanations for your decisions."""
            
            # Initial LLM call
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Process this evidence: {context}"}
            ]
            
            # Execute LLM orchestration
            result_data = await self._execute_llm_workflow(context, request)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            greenscore_result = result_data.get("greenscore_result", {})
            return AIOrchestrationResult(
                evidence_id=request.evidence.evidence_id,
                user_id=request.evidence.user_id,
                greenscore=greenscore_result.get("greenscore", 0),
                subscores=greenscore_result.get("subscores", {}),
                co2_saved_tonnes=greenscore_result.get("co2_saved_tonnes", 0.0),
                confidence=result_data.get("confidence", 0.8),
                explainers=greenscore_result.get("explainers", []),
                actions=greenscore_result.get("actions", []),
                carbon_credits=result_data.get("carbon_credits")
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
            
            # Step 2: Calculate emissions
            emission_result = await self.emission_calculator.calculate_emissions(
                ocr_result=ocr_result,
                cv_result=cv_result,
                sector=request.sector,
                region=request.region
            )
            
            # Step 3: Estimate user metrics
            user_metrics = self.score_computer.estimate_user_metrics_from_evidence(
                emission_result=emission_result,
                sector=request.sector,
                ocr_data=ocr_result.dict() if ocr_result else {},
                cv_data=cv_result.dict() if cv_result else {}
            )
            
            # Step 4: Compute GreenScore
            greenscore_result = await self.score_computer.compute_score(
                user_id=request.evidence.user_id,
                evidence_id=request.evidence.evidence_id,
                sector=request.sector,
                emission_result=emission_result,
                user_metrics=user_metrics,
                region=request.region
            )
            
            # Step 5: Calculate carbon credits
            carbon_credits = await self.carbon_credit_aggregator.calculate_carbon_credits(
                user_id=request.evidence.user_id,
                evidence_id=request.evidence.evidence_id,
                emission_result=emission_result,
                greenscore_result=greenscore_result,
                sector=request.sector
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
                carbon_credits=carbon_credits[0] if carbon_credits else None
            )
            
        except Exception as e:
            logger.error(f"Error in deterministic processing: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return AIOrchestrationResult(
                evidence_id=request.evidence.evidence_id,
                user_id=request.evidence.user_id,
                greenscore=0,
                subscores={},
                co2_saved_tonnes=0.0,
                confidence=0.0,
                explainers=[f"Error: {str(e)}"],
                actions=[]
            )

    def _build_context(self, request: AIOrchestrationRequest) -> str:
        """Build context string for LLM"""
        context = f"""
        Evidence Processing Request:
        - User ID: {request.evidence.user_id}
        - Evidence ID: {request.evidence.evidence_id}
        - Evidence Type: {request.evidence.type}
        - Sector: {request.sector}
        - Region: {request.region}
        - Timestamp: {request.evidence.timestamp}
        
        Please process this evidence to calculate GreenScore and carbon credits.
        """
        return context

    # Function implementations for LLM calls
    async def _process_evidence(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Process evidence wrapper for LLM"""
        evidence_obj = EvidenceData(**evidence)
        result = await self.evidence_processor.process_evidence(evidence_obj)
        return {
            "ocr_result": result["ocr_result"].dict() if result["ocr_result"] else None,
            "cv_result": result["cv_result"].dict() if result["cv_result"] else None
        }

    async def _calculate_emissions(
        self, 
        ocr_result: Dict[str, Any], 
        cv_result: Dict[str, Any], 
        sector: str, 
        region: str = "Kenya"
    ) -> Dict[str, Any]:
        """Calculate emissions wrapper for LLM"""
        ocr_obj = OCRResult(**ocr_result) if ocr_result else None
        cv_obj = CVResult(**cv_result) if cv_result else None
        
        result = await self.emission_calculator.calculate_emissions(
            ocr_result=ocr_obj,
            cv_result=cv_obj,
            sector=sector,
            region=region
        )
        return result.dict()

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
