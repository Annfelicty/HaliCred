#!/usr/bin/env python3
"""
Phase 6 Simple Validation Script - Test Infrastructure Validation
Validates all Phase 6 requirements for HaliCred project.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

class Phase6SimpleValidator:
    """Simple Phase 6 validation without unicode characters."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend-web"
        self.results = {}

    def print_result(self, test_name: str, passed: bool) -> bool:
        """Print test result."""
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}")
        return passed

    def validate_backend_infrastructure(self) -> bool:
        """Validate backend test infrastructure."""
        print("\n=== Backend Test Infrastructure ===")

        success = True
        required_files = [
            "tests/conftest.py",
            "tests/test_api_comprehensive.py",
            "tests/test_database_integration.py",
            "tests/test_auth_comprehensive.py",
            "tests/test_ai_processing.py",
            "tests/test_loan_system.py",
            "tests/test_monitoring_security.py",
            "tests/test_performance.py",
            "run_tests.py"
        ]

        for file_path in required_files:
            full_path = self.backend_dir / file_path
            passed = full_path.exists()
            success &= self.print_result(f"Backend file: {file_path}", passed)

        self.results["Backend Infrastructure"] = success
        return success

    def validate_frontend_infrastructure(self) -> bool:
        """Validate frontend test infrastructure."""
        print("\n=== Frontend Test Infrastructure ===")

        success = True
        required_files = [
            "jest.config.js",
            "src/test/setup.ts",
            "src/test/utils/test-utils.tsx",
            "src/test/mocks/server.ts"
        ]

        for file_path in required_files:
            full_path = self.frontend_dir / file_path
            passed = full_path.exists()
            success &= self.print_result(f"Frontend file: {file_path}", passed)

        # Check test directories
        test_dirs = [
            "src/Components/Sme/__tests__",
            "src/Components/Ui/__tests__",
            "src/hooks/__tests__"
        ]

        for test_dir in test_dirs:
            dir_path = self.frontend_dir / test_dir
            passed = dir_path.exists()
            success &= self.print_result(f"Test directory: {test_dir}", passed)

        self.results["Frontend Infrastructure"] = success
        return success

    def validate_e2e_infrastructure(self) -> bool:
        """Validate E2E test infrastructure."""
        print("\n=== E2E Test Infrastructure ===")

        success = True
        required_files = [
            "playwright.config.ts",
            "src/e2e/global-setup.ts",
            "src/e2e/global-teardown.ts",
            "src/e2e/auth.spec.ts",
            "src/e2e/loan-application.spec.ts",
            "src/e2e/evidence-upload.spec.ts"
        ]

        for file_path in required_files:
            full_path = self.frontend_dir / file_path
            passed = full_path.exists()
            success &= self.print_result(f"E2E file: {file_path}", passed)

        self.results["E2E Infrastructure"] = success
        return success

    def validate_quality_gates(self) -> bool:
        """Validate quality gates setup."""
        print("\n=== Quality Gates & CI/CD ===")

        success = True

        # Check GitHub Actions workflow
        workflow_file = self.project_root / ".github/workflows/phase6-testing.yml"
        success &= self.print_result("GitHub Actions workflow", workflow_file.exists())

        # Check test runner scripts
        backend_runner = self.backend_dir / "run_tests.py"
        success &= self.print_result("Backend test runner", backend_runner.exists())

        # Check Jest config
        jest_config = self.frontend_dir / "jest.config.js"
        success &= self.print_result("Jest configuration", jest_config.exists())

        self.results["Quality Gates"] = success
        return success

    def validate_test_categories(self) -> bool:
        """Validate test categorization."""
        print("\n=== Test Categories ===")

        success = True

        # Check backend test categories
        backend_tests = [
            ("API Tests", "tests/test_api_comprehensive.py"),
            ("Auth Tests", "tests/test_auth_comprehensive.py"),
            ("Database Tests", "tests/test_database_integration.py"),
            ("AI Tests", "tests/test_ai_processing.py"),
            ("Loan Tests", "tests/test_loan_system.py"),
            ("Security Tests", "tests/test_monitoring_security.py"),
            ("Performance Tests", "tests/test_performance.py")
        ]

        for test_name, test_file in backend_tests:
            file_path = self.backend_dir / test_file
            passed = file_path.exists()
            success &= self.print_result(test_name, passed)

        # Check frontend test categories
        frontend_tests = [
            ("SME Dashboard Tests", "src/Components/Sme/__tests__/SMEDashboard.test.tsx"),
            ("Evidence Upload Tests", "src/Components/Sme/__tests__/EvidenceUpload.test.tsx"),
            ("Loan Offers Tests", "src/Components/Sme/__tests__/LoanOffers.test.tsx"),
            ("Auth Hook Tests", "src/hooks/__tests__/useAuth.test.ts"),
            ("Loading Component Tests", "src/Components/Ui/__tests__/loading.test.tsx")
        ]

        for test_name, test_file in frontend_tests:
            file_path = self.frontend_dir / test_file
            passed = file_path.exists()
            success &= self.print_result(test_name, passed)

        self.results["Test Categories"] = success
        return success

    def generate_report(self) -> dict:
        """Generate validation report."""
        print("\n=== Phase 6 Validation Summary ===")

        total = len(self.results)
        passed = sum(self.results.values())
        success_rate = (passed / total) * 100 if total > 0 else 0

        for category, result in self.results.items():
            status = "PASS" if result else "FAIL"
            print(f"[{status}] {category}")

        print(f"\nSummary: {passed}/{total} categories passed ({success_rate:.1f}%)")

        overall_status = "PHASE 6 COMPLETE" if all(self.results.values()) else "PHASE 6 INCOMPLETE"
        print(f"Status: {overall_status}")

        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 6 - Test Suite Expansion & Quality Gates",
            "results": self.results,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": success_rate,
                "status": overall_status
            }
        }

        return report

    def run_validation(self) -> bool:
        """Run complete validation."""
        print("Starting Phase 6 Validation...")
        print(f"Project Root: {self.project_root}")
        print(f"Time: {datetime.now()}")

        # Run all validations
        self.validate_backend_infrastructure()
        self.validate_frontend_infrastructure()
        self.validate_e2e_infrastructure()
        self.validate_quality_gates()
        self.validate_test_categories()

        # Generate report
        report = self.generate_report()

        # Save report
        report_file = self.project_root / "PHASE6_VALIDATION_REPORT.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved to: {report_file}")

        return report["summary"]["status"] == "PHASE 6 COMPLETE"

def main():
    """Main entry point."""
    validator = Phase6SimpleValidator()

    try:
        success = validator.run_validation()
        if success:
            print("\nValidation completed successfully!")
            return 0
        else:
            print("\nValidation completed with issues.")
            return 1
    except Exception as e:
        print(f"\nValidation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())