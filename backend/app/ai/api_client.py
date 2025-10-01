"""
External API client with retry logic, circuit breakers, and credential validation.
Implements production-ready patterns for Gemini, Google Vision, and Climatiq APIs.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Callable, List
import aiohttp
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
import json
import os

logger = logging.getLogger(__name__)




class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class APIConfig:
    """Configuration for external API client"""
    timeout: float = 30.0
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    next_attempt_time: float = 0


class ExternalAPIClient:
    """Production-ready external API client with reliability patterns"""

    def __init__(self, config: APIConfig):
        self.config = config
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.session: Optional[aiohttp.ClientSession] = None

        # API credentials
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.google_vision_api_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        self.climatiq_api_key = os.getenv("CLIMATIQ_API_KEY", "")
        # Initialize services
        self._init_gemini()
        self._init_google_vision()

    def _init_gemini(self):
        """Initialize Gemini AI client"""
        logger.info(f"[INIT] Initializing Gemini AI with model: gemini-2.5-flash")
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")
                logger.info("[OK] Gemini AI client initialized successfully")
            except Exception as e:
                logger.error(f"[ERROR] Failed to initialize Gemini AI: {e}")
                # Try alternative model name
                try:
                    self.gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
                    logger.info("[OK] Gemini AI client initialized with alternative model")
                except Exception as e2:
                    logger.error(f"[ERROR] Failed to initialize Gemini AI with alternative model: {e2}")
                    self.gemini_model = None
        else:
            logger.warning("[WARN] Gemini API key not configured")
            self.gemini_model = None

    def _init_google_vision(self):
        """Initialize Google Vision client"""
        logger.info(f"[INIT] Initializing Google Vision client")
        try:
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            logger.info(f"[FILE] Google Vision credentials path: {credentials_path}")
            
            if credentials_path and os.path.exists(credentials_path):
                logger.info(f"[OK] Found credentials file: {credentials_path}")
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("[OK] Google Vision client initialized successfully")
            else:
                logger.warning(f"[WARN] Google Vision credentials file not found at: {credentials_path}")
                self.vision_client = None
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize Google Vision: {e}")
            self.vision_client = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _get_circuit_breaker(self, service_name: str) -> CircuitBreakerState:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreakerState()
        return self.circuit_breakers[service_name]

    def _should_attempt_call(self, service_name: str) -> bool:
        """Check if call should be attempted based on circuit breaker state"""
        breaker = self._get_circuit_breaker(service_name)
        current_time = time.time()

        if breaker.state == CircuitState.CLOSED:
            return True
        elif breaker.state == CircuitState.OPEN:
            if current_time >= breaker.next_attempt_time:
                breaker.state = CircuitState.HALF_OPEN
                return True
            return False
        elif breaker.state == CircuitState.HALF_OPEN:
            return True

        return False

    def _record_success(self, service_name: str):
        """Record successful API call"""
        breaker = self._get_circuit_breaker(service_name)
        breaker.failure_count = 0
        breaker.state = CircuitState.CLOSED
        logger.debug(f"✓ {service_name} API call successful, circuit closed")

    def _record_failure(self, service_name: str, error: Exception):
        """Record failed API call and update circuit breaker"""
        breaker = self._get_circuit_breaker(service_name)
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()

        if breaker.failure_count >= self.config.circuit_breaker_threshold:
            breaker.state = CircuitState.OPEN
            breaker.next_attempt_time = time.time() + self.config.circuit_breaker_timeout
            logger.warning(f"[WARN] {service_name} circuit breaker OPENED after {breaker.failure_count} failures")

        logger.error(f"[FAIL] {service_name} API call failed: {error}")

    async def _retry_with_backoff(self, func: Callable, service_name: str, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry logic"""

        if not self._should_attempt_call(service_name):
            raise Exception(f"{service_name} circuit breaker is OPEN")

        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                self._record_success(service_name)
                return result

            except Exception as e:
                last_exception = e

                if attempt == self.config.max_retries:
                    self._record_failure(service_name, e)
                    break

                # Calculate exponential backoff delay
                delay = min(
                    self.config.retry_base_delay * (2 ** attempt),
                    self.config.retry_max_delay
                )

                logger.warning(f"[WARN] {service_name} attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)

        raise last_exception

    async def validate_api_credentials(self) -> Dict[str, bool]:
        """Validate all external API credentials"""
        results = {}

        # Test Gemini API
        logger.info("[TEST] Testing Gemini API...")
        try:
            if self.gemini_model:
                logger.info("[OK] Gemini model exists, running test...")
                await self._retry_with_backoff(self._test_gemini_connection, "gemini")
                results["gemini"] = True
                logger.info("[OK] Gemini API validation successful")
            else:
                logger.warning("[WARN] Gemini model not initialized")
                results["gemini"] = False
        except Exception as e:
            logger.error(f"[ERROR] Gemini credential validation failed: {e}")
            results["gemini"] = False

        # Test Google Vision API
        try:
            if self.vision_client:
                await self._retry_with_backoff(
                    self._test_vision_connection, "google_vision"
                )
                results["google_vision"] = True
                logger.info("[OK] Google Vision API validation successful")
            else:
                results["google_vision"] = False
                logger.warning("[WARN] Google Vision API validation failed: Vision client not initialized")
        except Exception as e:
            logger.error(f"Google Vision credential validation failed: {e}")
            results["google_vision"] = False

        # Test Climatiq API
        try:
            if self.climatiq_api_key:
                await self._retry_with_backoff(
                    self._test_climatiq_connection, "climatiq"
                )
                results["climatiq"] = True
                logger.info("[OK] Climatiq API validation successful")
            else:
                results["climatiq"] = False
                logger.warning("[WARN] Climatiq API validation failed: API key not configured")
        except Exception as e:
            logger.error(f"Climatiq credential validation failed: {e}")
            results["climatiq"] = False

        return results

    async def _test_gemini_connection(self):
        """Test Gemini API connectivity"""
        start_time = time.time()

        if not self.gemini_model:
            raise Exception("Gemini model not initialized")

        response = self.gemini_model.generate_content("Test connection")
        if not response.text:
            raise Exception("Empty response from Gemini API")

        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        logger.info(f"[OK] Gemini API connection test successful - Model ready for inference ({response_time:.2f}ms)")

    async def _test_vision_connection(self):
        """Test Google Vision API connectivity"""
        start_time = time.time()

        if not self.vision_client:
            raise Exception("Vision client not initialized")

        try:
            # Use the actual solar panel image file
            image_path = "sample-data/solar-panel.jpg"  # Path relative to backend folder

            with open(image_path, 'rb') as image_file:
                image_content = image_file.read()

            test_image = vision.Image(content=image_content)
            response = self.vision_client.text_detection(image=test_image)

            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")

            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            logger.info(f"[OK] Google Vision API validation successful - OCR ready ({response_time:.2f}ms)")
        except FileNotFoundError:
            raise Exception(f"Test image file not found: {image_path}")
        except Exception as e:
            logger.error(f"Vision API test failed: {e}")
            raise

    async def _test_climatiq_connection(self):
        """Test Climatiq API connectivity"""
        start_time = time.time()

        if not self.session:
            raise Exception("HTTP session not initialized")

        headers = {
            "Authorization": f"Bearer {self.climatiq_api_key}",
            "Content-Type": "application/json"
        }

        async with self.session.get(
            "https://api.climatiq.io/data/v1/search",
            headers=headers,
            params = {
                "activity_id": "electricity-supply_grid-source_residual_mix",
                "region": "GLO",
                "results_per_page": 1,
                "data_version": "26.26",
            }
        ) as response:
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"Climatiq API error {response.status}: {error_text}")

        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        logger.info(f"[OK] Climatiq API connection test successful - Emissions data accessible ({response_time:.2f}ms)")

    async def call_gemini_api(self, prompt: str, **kwargs) -> str:
        """Call Gemini API with retry logic"""
        async def _call():
            if not self.gemini_model:
                raise Exception("Gemini model not initialized")

            response = self.gemini_model.generate_content(prompt, **kwargs)
            if not response.text:
                raise Exception("Empty response from Gemini API")

            return response.text

        return await self._retry_with_backoff(_call, "gemini")

    async def call_vision_api(self, image_content: bytes) -> Dict[str, Any]:
        """Call Google Vision API with retry logic"""
        async def _call():
            if not self.vision_client:
                raise Exception("Vision client not initialized")

            image = vision.Image(content=image_content)
            response = self.vision_client.text_detection(image=image)

            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")

            # Extract text annotations
            texts = []
            for text in response.text_annotations:
                texts.append({
                    "description": text.description,
                    "bounding_poly": {
                        "vertices": [
                            {"x": vertex.x, "y": vertex.y}
                            for vertex in text.bounding_poly.vertices
                        ]
                    }
                })

            return {"text_annotations": texts}

        return await self._retry_with_backoff(_call, "google_vision")

    async def call_climatiq_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call Climatiq API with retry logic"""
        async def _call():
            if not self.session:
                raise Exception("HTTP session not initialized")

            headers = {
                "Authorization": f"Bearer {self.climatiq_api_key}",
                "Content-Type": "application/json"
            }

            url = f"https://api.climatiq.io{endpoint}"

            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"Climatiq API error {response.status}: {error_text}")

                return await response.json()

        return await self._retry_with_backoff(_call, "climatiq")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all external services"""
        status = {}

        for service_name, breaker in self.circuit_breakers.items():
            status[service_name] = {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "last_failure_time": breaker.last_failure_time,
                "healthy": breaker.state == CircuitState.CLOSED
            }

        return status


# Global API client instance
api_client_config = APIConfig()
external_api_client = ExternalAPIClient(api_client_config)