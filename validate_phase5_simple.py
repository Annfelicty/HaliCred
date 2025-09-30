#!/usr/bin/env python3
"""
Phase 5 Validation Script for HaliCred
Validates implementation of robustness, observability, and UX polish features.
"""

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
        if not logger_file.exists():
            return False

        content = logger_file.read_text(encoding='utf-8')

        required_features = [
            "correlation_id",
            "StructuredLogger",
            "JSON",
            "log_api_request",
            "log_business_event"
        ]

        for feature in required_features:
            if feature not in content:
                print(f"[FAIL] Missing logging feature: {feature}")
                return False
            print(f"[PASS] Found logging feature: {feature}")

        return True

    def validate_health_checks(self) -> bool:
        """Validate health check implementation"""
        print("\n[INFO] Validating health checks...")

        health_file = self.project_root / "backend/app/monitoring/health.py"
        if not health_file.exists():
            print("[FAIL] Missing health.py")
            return False

        content = health_file.read_text(encoding='utf-8')
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
                print(f"[FAIL] Missing health check: {check}")
                return False
            print(f"[PASS] Found health check: {check}")

        return True

    def validate_error_handling(self) -> bool:
        """Validate standardized error handling"""
        print("\n[INFO] Validating error handling...")

        error_file = self.project_root / "backend/app/monitoring/error_handling.py"
        if not error_file.exists():
            print("[FAIL] Missing error_handling.py")
            return False

        content = error_file.read_text(encoding='utf-8')
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
                print(f"[FAIL] Missing error feature: {feature}")
                return False
            print(f"[PASS] Found error feature: {feature}")

        return True

    def validate_security_features(self) -> bool:
        """Validate security hardening implementation"""
        print("\n[INFO] Validating security features...")

        security_file = self.project_root / "backend/app/monitoring/security.py"
        if not security_file.exists():
            print("[FAIL] Missing security.py")
            return False

        content = security_file.read_text(encoding='utf-8')
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
                print(f"[FAIL] Missing security feature: {feature}")
                return False
            print(f"[PASS] Found security feature: {feature}")

        return True

    def validate_loading_states(self) -> bool:
        """Validate UX loading states implementation"""
        print("\n[INFO] Validating loading states...")

        loading_file = self.project_root / "frontend-web/src/Components/Ui/loading.tsx"
        if not loading_file.exists():
            print("[FAIL] Missing loading.tsx")
            return False

        content = loading_file.read_text(encoding='utf-8')
        required_components = [
            "Spinner",
            "LoadingButton",
            "LoadingOverlay",
            "UploadProgress",
            "DashboardSkeleton",
            "ErrorState"
        ]

        for component in required_components:
            if f"export function {component}" not in content and f"export const {component}" not in content:
                print(f"[FAIL] Missing loading component: {component}")
                return False
            print(f"[PASS] Found loading component: {component}")

        return True

    def validate_accessibility(self) -> bool:
        """Validate accessibility features implementation"""
        print("\n[INFO] Validating accessibility features...")

        accessibility_file = self.project_root / "frontend-web/src/Components/Ui/accessibility.tsx"
        if not accessibility_file.exists():
            print("[FAIL] Missing accessibility.tsx")
            return False

        content = accessibility_file.read_text(encoding='utf-8')
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
                print(f"[FAIL] Missing accessibility feature: {feature}")
                return False
            print(f"[PASS] Found accessibility feature: {feature}")

        return True

    def validate_monitoring_integration(self) -> bool:
        """Validate monitoring integration in main.py"""
        print("\n[INFO] Validating monitoring integration...")

        main_file = self.project_root / "backend/app/main.py"
        if not main_file.exists():
            print("[FAIL] Missing main.py")
            return False

        content = main_file.read_text(encoding='utf-8')
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
                print(f"[FAIL] Missing monitoring integration: {integration}")
                return False
            print(f"[PASS] Found monitoring integration: {integration}")

        return True

    def validate_frontend_enhancements(self) -> bool:
        """Validate frontend component enhancements"""
        print("\n[INFO] Validating frontend enhancements...")

        components_to_check = [
            "frontend-web/src/Components/SME/SMEDashboard.tsx",
            "frontend-web/src/Components/SME/EvidenceUpload.tsx",
            "frontend-web/src/Components/SME/LoanOffers.tsx"
        ]

        enhanced_features = ["LoadingButton", "LoadingOverlay", "ErrorState", "SkipLink"]

        for component_path in components_to_check:
            full_path = self.project_root / component_path
            if not full_path.exists():
                print(f"[FAIL] Missing component: {component_path}")
                return False

            content = full_path.read_text(encoding='utf-8')
            found_features = 0

            for feature in enhanced_features:
                if feature in content:
                    found_features += 1

            if found_features == 0:
                print(f"[FAIL] No UX enhancements found in: {component_path}")
                return False

            print(f"[PASS] Found {found_features} UX enhancements in: {component_path}")

        return True

    def run_validation(self) -> bool:
        """Run complete Phase 5 validation"""
        print("Starting Phase 5 Validation for HaliCred")
        print("=" * 60)

        # Run all validations
        validations = [
            ("Structured Logging", self.validate_structured_logging),
            ("Health Checks", self.validate_health_checks),
            ("Error Handling", self.validate_error_handling),
            ("Security Features", self.validate_security_features),
            ("Loading States", self.validate_loading_states),
            ("Accessibility", self.validate_accessibility),
            ("Monitoring Integration", self.validate_monitoring_integration),
            ("Frontend Enhancements", self.validate_frontend_enhancements)
        ]

        passed = 0
        total = len(validations)
        results = {}

        for name, validator in validations:
            try:
                result = validator()
                results[name] = result
                if result:
                    passed += 1
            except Exception as e:
                print(f"[ERROR] {name} validation failed: {e}")
                results[name] = False

        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        for name, result in results.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"{status} {name}")

        print("\n" + "=" * 60)
        success_rate = round((passed / total) * 100, 2)
        overall_status = "PHASE 5 COMPLETE" if passed == total else f"{total - passed} ITEMS NEED ATTENTION"

        print(f"OVERALL RESULT: {overall_status}")
        print(f"Success Rate: {success_rate}%")
        print(f"Passed: {passed}/{total}")

        # Generate JSON report
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "phase": "Phase 5 - Robustness, Observability, and UX Polish",
            "results": results,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": success_rate,
                "status": overall_status
            }
        }

        report_file = self.project_root / "PHASE5_VALIDATION_REPORT.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nDetailed report saved to: {report_file}")

        return passed == total

def main():
    """Main execution function"""
    validator = Phase5Validator()

    try:
        success = validator.run_validation()

        if success:
            print("\nPhase 5 validation completed successfully!")
            sys.exit(0)
        else:
            print("\nPhase 5 validation found issues that need attention.")
            sys.exit(1)

    except Exception as e:
        print(f"\nValidation failed with error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()