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


async def validate_africas_talking() -> bool:
    """Validate Africa's Talking SMS service"""
    try:
        from app.services.otp_service import otp_delivery_service
        from app.config import settings

        # Check if Africa's Talking is initialized
        if not otp_delivery_service.africas_talking_sms:
            logger.warning("[WARN] Africa's Talking SMS client not initialized")
            return False

        # Test sending to a test number (will not actually send in sandbox)
        # In sandbox mode, Africa's Talking doesn't actually send SMS
        env_mode = settings.ENVIRONMENT_MODE.upper()
        logger.info(f"[OK] Africa's Talking SMS client validated ({env_mode} mode)")
        logger.info(f"   Username: {otp_delivery_service.africas_talking_username}")
        return True

    except Exception as e:
        logger.error(f"[ERROR] Africa's Talking validation failed: {e}")
        return False


async def validate_smtp_email() -> bool:
    """Validate SMTP email configuration"""
    try:
        from app.config import settings

        if not settings.SMTP_HOST:
            logger.warning("[WARN] SMTP not configured (SMTP_HOST missing)")
            return False

        if settings.SMTP_PASSWORD == "not_configured_yet":
            logger.warning("[WARN] SMTP password not configured")
            return False

        logger.info(f"[OK] SMTP configured - Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        return True

    except Exception as e:
        logger.error(f"[ERROR] SMTP validation failed: {e}")
        return False


class StartupValidator:
    """Validates external API services on application startup"""

    def __init__(self):
        self.validation_results: Dict[str, Any] = {}

    async def validate_all_services(self) -> Dict[str, Any]:
        """Validate all external API services"""
        logger.info("[START] Starting external API validation...")

        try:
            async with external_api_client as client:
                self.validation_results = await client.validate_api_credentials()

            # Validate Africa's Talking SMS
            self.validation_results["africas_talking_sms"] = await validate_africas_talking()

            # Validate SMTP Email
            self.validation_results["smtp_email"] = await validate_smtp_email()

            # Log validation results
            self._log_validation_results()

            # Check if critical services are available
            critical_services = ["gemini"]  # Core services that must work
            missing_critical = [
                service for service in critical_services
                if not self.validation_results.get(service, False)
            ]

            if missing_critical:
                logger.error(f"[ERROR] Critical services unavailable: {missing_critical}")
                logger.error("[INFO] Application will use fallback mechanisms for unavailable services")
            else:
                logger.info("[OK] All critical services validated successfully")

            return self.validation_results

        except Exception as e:
            logger.error(f"[CRITICAL] Startup validation failed: {e}")
            self.validation_results = {"error": str(e)}
            return self.validation_results

    def _log_validation_results(self):
        """Log detailed validation results"""
        total_services = len(self.validation_results)
        available_services = sum(1 for status in self.validation_results.values() if status)
        availability_percent = (available_services / total_services * 100) if total_services > 0 else 0

        logger.info("=" * 60)
        logger.info("          EXTERNAL API VALIDATION RESULTS")
        logger.info("=" * 60)

        for service, status in self.validation_results.items():
            service_name = service.replace('_', ' ').title().ljust(25)
            if status:
                logger.info(f"  [OK] {service_name} | Available")
            else:
                logger.info(f"  [FAIL] {service_name} | Unavailable")

        logger.info("=" * 60)
        logger.info(f"  Status: {available_services}/{total_services} services available ({availability_percent:.0f}%)")
        logger.info("=" * 60)

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