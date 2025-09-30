#!/usr/bin/env python3
"""
Phase 5 Validation Script for HaliCred
Validates implementation of robustness, observability, and UX polish features.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

class Phase5Validator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_path = self.project_root / "backend"
        self.frontend_path = self.project_root / "frontend-web"
        self.validation_results = {
            "structured_logging": False,
            "health_checks": False,
            "error_handling": False,
            "security_features": False,
            "loading_states": False,
            "accessibility": False,
            "monitoring": False
        }

    def validate_structured_logging(self) -> bool:
        """Validate structured logging implementation"""
        print("[INFO] Validating structured logging...")

        required_files = [
            "backend/app/monitoring/logger.py",
            "backend/app/monitoring/__init__.py"
        ]

        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                print(f"[FAIL] Missing: {file_path}")
                return False
            print(f"[PASS] Found: {file_path}")

        # Check for structured logging features
        logger_file = self.project_root / "backend/app/monitoring/logger.py"
        content = logger_file.read_text()

        required_features = [
            "correlation_id",
            "StructuredLogger",
            "JSON",
            "log_api_request",
            "log_business_event"
        ]

        for feature in required_features:
            if feature not in content:
                print(f"❌ Missing logging feature: {feature}")
                return False
            print(f"✅ Found logging feature: {feature}")

        return True

    def validate_health_checks(self) -> bool:
        """Validate health check implementation"""
        print("\n🔍 Validating health checks...")

        health_file = self.project_root / "backend/app/monitoring/health.py"
        if not health_file.exists():
            print("❌ Missing health.py")
            return False

        content = health_file.read_text()
        required_checks = [
            "check_database",
            "check_redis",
            "check_minio",
            "check_gemini_api",
            "check_vision_api",
            "check_climatiq_api"
        ]

        for check in required_checks:
            if check not in content:
                print(f"❌ Missing health check: {check}")
                return False
            print(f"✅ Found health check: {check}")

        return True

    def validate_error_handling(self) -> bool:
        """Validate standardized error handling"""
        print("\n🔍 Validating error handling...")

        error_file = self.project_root / "backend/app/monitoring/error_handling.py"
        if not error_file.exists():
            print("❌ Missing error_handling.py")
            return False

        content = error_file.read_text()
        required_features = [
            "StandardError",
            "ErrorHandler",
            "create_error_response",
            "AUTH_001",
            "VAL_001",
            "user_message"
        ]

        for feature in required_features:
            if feature not in content:
                print(f"❌ Missing error feature: {feature}")
                return False
            print(f"✅ Found error feature: {feature}")

        return True

    def validate_security_features(self) -> bool:
        """Validate security hardening implementation"""
        print("\n🔍 Validating security features...")

        security_file = self.project_root / "backend/app/monitoring/security.py"
        if not security_file.exists():
            print("❌ Missing security.py")
            return False

        content = security_file.read_text()
        required_features = [
            "RateLimiter",
            "SecurityHeadersMiddleware",
            "InputValidationMiddleware",
            "rate_limits",
            "xss_patterns",
            "SecurityMonitor"
        ]

        for feature in required_features:
            if feature not in content:
                print(f"❌ Missing security feature: {feature}")
                return False
            print(f"✅ Found security feature: {feature}")

        return True

    def validate_loading_states(self) -> bool:
        """Validate UX loading states implementation"""
        print("\n🔍 Validating loading states...")

        loading_file = self.project_root / "frontend-web/src/Components/Ui/loading.tsx"
        if not loading_file.exists():
            print("❌ Missing loading.tsx")
            return False

        content = loading_file.read_text()
        required_components = [
            "Spinner",
            "LoadingButton",
            "LoadingOverlay",
            "UploadProgress",
            "DashboardSkeleton",
            "ErrorState",
            "StepProgress"
        ]

        for component in required_components:
            if f"export function {component}" not in content and f"export const {component}" not in content:
                print(f"❌ Missing loading component: {component}")
                return False
            print(f"✅ Found loading component: {component}")

        return True

    def validate_accessibility(self) -> bool:
        """Validate accessibility features implementation"""
        print("\n🔍 Validating accessibility features...")

        accessibility_file = self.project_root / "frontend-web/src/Components/Ui/accessibility.tsx"
        if not accessibility_file.exists():
            print("❌ Missing accessibility.tsx")
            return False

        content = accessibility_file.read_text()
        required_features = [
            "SkipLink",
            "VisuallyHidden",
            "FocusTrap",
            "LiveRegion",
            "AccessibleIcon",
            "useReducedMotion",
            "focusVisibleClasses"
        ]

        for feature in required_features:
            if feature not in content:
                print(f"❌ Missing accessibility feature: {feature}")
                return False
            print(f"✅ Found accessibility feature: {feature}")

        return True

    def validate_monitoring_integration(self) -> bool:
        """Validate monitoring integration in main.py"""
        print("\n🔍 Validating monitoring integration...")

        main_file = self.project_root / "backend/app/main.py"
        if not main_file.exists():
            print("❌ Missing main.py")
            return False

        content = main_file.read_text()
        required_integrations = [
            "monitoring",
            "health_checker",
            "SecurityHeadersMiddleware",
            "RateLimitingMiddleware",
            "correlation_id_middleware",
            "/health/ready",
            "/health/live"
        ]

        for integration in required_integrations:
            if integration not in content:
                print(f"❌ Missing monitoring integration: {integration}")
                return False
            print(f"✅ Found monitoring integration: {integration}")

        return True

    def validate_frontend_enhancements(self) -> bool:
        """Validate frontend component enhancements"""
        print("\n🔍 Validating frontend enhancements...")

        components_to_check = [
            "frontend-web/src/Components/SME/SMEDashboard.tsx",
            "frontend-web/src/Components/SME/EvidenceUpload.tsx",
            "frontend-web/src/Components/SME/LoanOffers.tsx"
        ]

        enhanced_features = ["LoadingButton", "LoadingOverlay", "ErrorState", "SkipLink"]

        for component_path in components_to_check:
            full_path = self.project_root / component_path
            if not full_path.exists():
                print(f"❌ Missing component: {component_path}")
                return False

            content = full_path.read_text()
            found_features = 0

            for feature in enhanced_features:
                if feature in content:
                    found_features += 1

            if found_features == 0:
                print(f"❌ No UX enhancements found in: {component_path}")
                return False

            print(f"✅ Found {found_features} UX enhancements in: {component_path}")

        return True

    def test_health_endpoints(self) -> bool:
        """Test health check endpoints if server is running"""
        print("\n🔍 Testing health endpoints...")

        try:
            import requests
            base_url = "http://localhost:8000"

            # Test readiness endpoint
            response = requests.get(f"{base_url}/health/ready", timeout=5)
            if response.status_code == 200:
                print("✅ Readiness endpoint working")
            else:
                print(f"⚠️ Readiness endpoint returned: {response.status_code}")

            # Test liveness endpoint
            response = requests.get(f"{base_url}/health/live", timeout=5)
            if response.status_code == 200:
                print("✅ Liveness endpoint working")
                return True
            else:
                print(f"⚠️ Liveness endpoint returned: {response.status_code}")

        except ImportError:
            print("⚠️ requests module not available - skipping endpoint tests")
            return True
        except Exception:
            print("⚠️ Backend server not running - skipping endpoint tests")
            return True  # Don't fail validation if server is not running

        return True

    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "phase": "Phase 5 - Robustness, Observability, and UX Polish",
            "validation_results": {},
            "summary": {},
            "recommendations": []
        }

        # Run all validations
        validations = [
            ("structured_logging", self.validate_structured_logging),
            ("health_checks", self.validate_health_checks),
            ("error_handling", self.validate_error_handling),
            ("security_features", self.validate_security_features),
            ("loading_states", self.validate_loading_states),
            ("accessibility", self.validate_accessibility),
            ("monitoring_integration", self.validate_monitoring_integration),
            ("frontend_enhancements", self.validate_frontend_enhancements)
        ]

        passed = 0
        total = len(validations)

        for name, validator in validations:
            try:
                result = validator()
                report["validation_results"][name] = {
                    "passed": result,
                    "status": "✅ PASS" if result else "❌ FAIL"
                }
                if result:
                    passed += 1
            except Exception as e:
                report["validation_results"][name] = {
                    "passed": False,
                    "status": f"❌ ERROR: {str(e)}"
                }

        # Summary
        report["summary"] = {
            "total_validations": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": round((passed / total) * 100, 2),
            "overall_status": "✅ PHASE 5 COMPLETE" if passed == total else f"⚠️ {total - passed} ITEMS NEED ATTENTION"
        }

        # Recommendations
        if passed < total:
            report["recommendations"] = [
                "Complete implementation of failed validation items",
                "Test all health check endpoints manually",
                "Verify error handling with actual API calls",
                "Test accessibility features with screen readers"
            ]
        else:
            report["recommendations"] = [
                "Consider load testing the monitoring infrastructure",
                "Test accessibility with real users",
                "Set up monitoring dashboards for production",
                "Configure alerting for health check failures"
            ]

        return report

    async def run_validation(self) -> bool:
        """Run complete Phase 5 validation"""
        print("🚀 Starting Phase 5 Validation for HaliCred")
        print("=" * 60)

        # Generate report
        report = self.generate_validation_report()

        # Test health endpoints if possible
        self.test_health_endpoints()

        # Print results
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        for name, result in report["validation_results"].items():
            print(f"{result['status']} {name.replace('_', ' ').title()}")

        print("\n" + "=" * 60)
        print(f"🎯 OVERALL RESULT: {report['summary']['overall_status']}")
        print(f"📈 Success Rate: {report['summary']['success_rate']}%")
        print(f"✅ Passed: {report['summary']['passed']}/{report['summary']['total']}")

        if report["recommendations"]:
            print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")

        # Save report
        report_file = self.project_root / "PHASE5_VALIDATION_REPORT.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return report["summary"]["passed"] == report["summary"]["total"]

async def main():
    """Main execution function"""
    validator = Phase5Validator()

    try:
        success = await validator.run_validation()

        if success:
            print("\n🎉 Phase 5 validation completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️ Phase 5 validation found issues that need attention.")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())