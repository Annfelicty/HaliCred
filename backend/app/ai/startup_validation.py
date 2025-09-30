"""
Startup validation for external API services.
Validates API credentials and connectivity on application startup.
"""

import asyncio
import logging
import sys
from typing import Dict, Any
from .api_client import external_api_client

logger = logging.getLogger(__name__)


class StartupValidator:
    """Validates external API services on application startup"""

    def __init__(self):
        self.validation_results: Dict[str, Any] = {}

    async def validate_all_services(self) -> Dict[str, Any]:
        """Validate all external API services"""
        logger.info("🚀 Starting external API validation...")

        try:
            async with external_api_client as client:
                self.validation_results = await client.validate_api_credentials()

            # Log validation results
            self._log_validation_results()

            # Check if critical services are available
            critical_services = ["gemini"]  # Core services that must work
            missing_critical = [
                service for service in critical_services
                if not self.validation_results.get(service, False)
            ]

            if missing_critical:
                logger.error(f"❌ Critical services unavailable: {missing_critical}")
                logger.error("💡 Application will use fallback mechanisms for unavailable services")
            else:
                logger.info("✅ All critical services validated successfully")

            return self.validation_results

        except Exception as e:
            logger.error(f"💥 Startup validation failed: {e}")
            self.validation_results = {"error": str(e)}
            return self.validation_results

    def _log_validation_results(self):
        """Log detailed validation results"""
        logger.info("📊 External API Validation Results:")
        logger.info("=" * 50)

        for service, status in self.validation_results.items():
            if status:
                logger.info(f"✅ {service.replace('_', ' ').title()}: Available")
            else:
                logger.warning(f"❌ {service.replace('_', ' ').title()}: Unavailable")

        logger.info("=" * 50)

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation results summary"""
        if not self.validation_results:
            return {"status": "not_validated", "services": {}}

        total_services = len(self.validation_results)
        available_services = sum(1 for status in self.validation_results.values() if status)

        return {
            "status": "completed",
            "total_services": total_services,
            "available_services": available_services,
            "availability_percentage": (available_services / total_services * 100) if total_services > 0 else 0,
            "services": self.validation_results,
            "critical_services_available": self.validation_results.get("gemini", False)
        }

    def is_service_available(self, service_name: str) -> bool:
        """Check if specific service is available"""
        return self.validation_results.get(service_name, False)

    def get_unavailable_services(self) -> list:
        """Get list of unavailable services"""
        return [
            service for service, status in self.validation_results.items()
            if not status
        ]


# Global startup validator instance
startup_validator = StartupValidator()


async def validate_on_startup() -> Dict[str, Any]:
    """Convenience function to run startup validation"""
    return await startup_validator.validate_all_services()


def create_health_check_endpoint():
    """Create health check data for external services"""
    return {
        "external_apis": startup_validator.get_validation_summary(),
        "circuit_breakers": external_api_client.get_health_status(),
        "timestamp": asyncio.get_event_loop().time()
    }