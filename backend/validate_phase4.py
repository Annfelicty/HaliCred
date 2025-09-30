#!/usr/bin/env python3
"""
Phase 4 Validation Script for Loan Management System
Validates that all Phase 4 components are properly implemented and integrated.
"""

import os
import sys
import importlib
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase4Validator:
    """Validates Phase 4 implementation"""

    def __init__(self):
        self.validation_results = []
        self.warnings = []
        self.errors = []

    def run_validation(self):
        """Run complete Phase 4 validation"""
        logger.info("Starting Phase 4 validation...")

        print("=" * 60)
        print("PHASE 4 VALIDATION - Loan Management System")
        print("=" * 60)

        # 1. Check loan service structure
        self.validate_loan_service()

        # 2. Check loan endpoint integration
        self.validate_loan_endpoints()

        # 3. Check admin functionality
        self.validate_admin_functionality()

        # 4. Check status tracking
        self.validate_status_tracking()

        # 5. Check analytics and reporting
        self.validate_analytics_reporting()

        # 6. Generate final report
        self.generate_validation_report()

    def validate_loan_service(self):
        """Validate loan service implementation"""
        print("\n[LOAN SERVICE] Validating loan service...")

        try:
            from app.services.loan_service import loan_service, LoanManagementService
            print("  [PASS] Loan service initialized")

            # Check if service has required methods
            required_methods = [
                'generate_loan_quote',
                'assess_loan_eligibility',
                'submit_loan_application',
                'lock_quote_rate',
                'get_applications_for_review',
                'process_admin_decision',
                'process_bulk_action',
                'get_loan_analytics',
                'get_application_status'
            ]

            for method in required_methods:
                if hasattr(loan_service, method):
                    print(f"    [PASS] Method: {method}")
                else:
                    print(f"    [FAIL] Missing method: {method}")
                    self.errors.append(f"Missing method: {method}")

            # Check dataclasses
            required_classes = [
                'LoanQuote',
                'LoanEligibility',
                'LoanApplicationSubmission',
                'LoanApplicationReview',
                'LoanDecisionResult',
                'BulkActionResult',
                'LoanAnalytics',
                'ApplicationStatusDetails'
            ]

            from app.services import loan_service as ls_module
            for class_name in required_classes:
                if hasattr(ls_module, class_name):
                    print(f"    [PASS] Class: {class_name}")
                else:
                    print(f"    [FAIL] Missing class: {class_name}")
                    self.errors.append(f"Missing class: {class_name}")

            self.validation_results.append("[PASS] Loan service components validated")

        except Exception as e:
            print(f"  [FAIL] Loan service error: {str(e)}")
            self.errors.append(f"Loan service error: {str(e)}")

    def validate_loan_endpoints(self):
        """Validate loan endpoints in main.py"""
        print("\n[ENDPOINTS] Validating loan endpoints...")

        try:
            # Check if main.py has been updated with loan endpoints
            main_file = backend_dir / "app" / "main.py"
            if main_file.exists():
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for enhanced loan endpoints
                endpoint_checks = [
                    ("POST /loan/quote", "async def loan_quote"),
                    ("POST /loan/eligibility", "async def check_loan_eligibility"),
                    ("POST /loan/quote/{quote_id}/lock", "async def lock_quote_rate"),
                    ("POST /loan/apply", "async def loan_apply"),
                    ("GET /loan/status/{application_id}", "async def get_loan_status"),
                ]

                for endpoint_name, endpoint_pattern in endpoint_checks:
                    if endpoint_pattern in content:
                        print(f"    [PASS] {endpoint_name}")
                    else:
                        print(f"    [FAIL] Missing: {endpoint_name}")
                        self.errors.append(f"Missing endpoint: {endpoint_name}")

                # Check for loan service integration
                if "from app.services.loan_service import loan_service" in content:
                    print("    [PASS] Loan service integration")
                else:
                    print("    [FAIL] Loan service not integrated")
                    self.errors.append("Loan service not integrated in main.py")

                self.validation_results.append("[PASS] Loan endpoints validated")
            else:
                print("  [FAIL] main.py not found")
                self.errors.append("main.py not found")

        except Exception as e:
            print(f"  [FAIL] Endpoint validation error: {str(e)}")
            self.errors.append(f"Endpoint validation error: {str(e)}")

    def validate_admin_functionality(self):
        """Validate admin functionality"""
        print("\n[ADMIN] Validating admin functionality...")

        try:
            main_file = backend_dir / "app" / "main.py"
            if main_file.exists():
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for enhanced admin endpoints
                admin_checks = [
                    ("Enhanced application listing", "async def list_applications"),
                    ("Enhanced decision processing", "async def decide_application"),
                    ("Analytics dashboard", "async def get_loan_analytics"),
                    ("Bulk operations", "async def bulk_action_applications"),
                ]

                for check_name, check_pattern in admin_checks:
                    if check_pattern in content:
                        print(f"    [PASS] {check_name}")
                    else:
                        print(f"    [FAIL] Missing: {check_name}")
                        self.errors.append(f"Missing admin feature: {check_name}")

                self.validation_results.append("[PASS] Admin functionality validated")

        except Exception as e:
            print(f"  [FAIL] Admin validation error: {str(e)}")
            self.errors.append(f"Admin validation error: {str(e)}")

    def validate_status_tracking(self):
        """Validate status tracking functionality"""
        print("\n[STATUS] Validating status tracking...")

        try:
            from app.services.loan_service import LoanStatus, TimelineEvent, ApplicationStatusDetails
            print("  [PASS] Status tracking classes defined")

            # Check status enum values
            expected_statuses = [
                'DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'ADDITIONAL_INFO_REQUIRED',
                'APPROVED', 'DECLINED', 'DISBURSED', 'DEFAULTED', 'FULLY_PAID'
            ]

            for status in expected_statuses:
                if hasattr(LoanStatus, status):
                    print(f"    [PASS] Status: {status}")
                else:
                    print(f"    [WARN] Missing status: {status}")
                    self.warnings.append(f"Missing status: {status}")

            self.validation_results.append("[PASS] Status tracking validated")

        except Exception as e:
            print(f"  [FAIL] Status tracking error: {str(e)}")
            self.errors.append(f"Status tracking error: {str(e)}")

    def validate_analytics_reporting(self):
        """Validate analytics and reporting functionality"""
        print("\n[ANALYTICS] Validating analytics and reporting...")

        try:
            from app.services.loan_service import LoanAnalytics, RiskAssessment
            print("  [PASS] Analytics classes defined")

            # Check if analytics methods exist in service
            from app.services.loan_service import loan_service
            if hasattr(loan_service, 'get_loan_analytics'):
                print("    [PASS] Analytics generation method")
            else:
                print("    [FAIL] Missing analytics generation")
                self.errors.append("Missing analytics generation method")

            # Check if risk assessment is implemented
            if hasattr(loan_service, '_assess_application_risk'):
                print("    [PASS] Risk assessment method")
            else:
                print("    [FAIL] Missing risk assessment")
                self.errors.append("Missing risk assessment method")

            self.validation_results.append("[PASS] Analytics and reporting validated")

        except Exception as e:
            print(f"  [FAIL] Analytics validation error: {str(e)}")
            self.errors.append(f"Analytics validation error: {str(e)}")

    def generate_validation_report(self):
        """Generate final validation report"""
        print("\n" + "=" * 60)
        print("PHASE 4 VALIDATION REPORT")
        print("=" * 60)

        total_checks = len(self.validation_results) + len(self.warnings) + len(self.errors)
        passed_checks = len(self.validation_results)
        warning_checks = len(self.warnings)
        failed_checks = len(self.errors)

        print(f"Total Checks: {total_checks}")
        print(f"[PASS] Passed: {passed_checks}")
        print(f"[WARN] Warnings: {warning_checks}")
        print(f"[FAIL] Failed: {failed_checks}")

        if failed_checks == 0:
            if warning_checks == 0:
                print(f"\n[SUCCESS] PHASE 4 VALIDATION: COMPLETE SUCCESS!")
                print("All loan management components are properly implemented and integrated.")
                status = "COMPLETE"
            else:
                print(f"\n[SUCCESS] PHASE 4 VALIDATION: SUCCESS WITH WARNINGS")
                print("Core loan management is implemented, some enhancements recommended.")
                status = "SUCCESS_WITH_WARNINGS"
        else:
            print(f"\n[INCOMPLETE] PHASE 4 VALIDATION: INCOMPLETE")
            print("Some critical loan management components are missing or have errors.")
            status = "INCOMPLETE"

        # Print detailed results
        if self.validation_results:
            print(f"\n[PASS] SUCCESSFUL VALIDATIONS:")
            for result in self.validation_results:
                print(f"  {result}")

        if self.warnings:
            print(f"\n[WARN] WARNINGS:")
            for warning in self.warnings:
                print(f"  [WARN] {warning}")

        if self.errors:
            print(f"\n[FAIL] ERRORS:")
            for error in self.errors:
                print(f"  [FAIL] {error}")

        # Phase 4 acceptance criteria check
        print(f"\n[CRITERIA] PHASE 4 ACCEPTANCE CRITERIA:")

        criteria = [
            ("Real Data Integration", "Loan service" in str(self.validation_results)),
            ("Quote Engine Enhancement", "Loan endpoints" in str(self.validation_results)),
            ("Application Workflow", "Loan endpoints" in str(self.validation_results)),
            ("Admin Interface", "Admin functionality" in str(self.validation_results)),
            ("Status Tracking", "Status tracking" in str(self.validation_results)),
            ("Analytics & Reporting", "Analytics" in str(self.validation_results)),
        ]

        all_criteria_met = True
        for criterion, met in criteria:
            status_icon = "[PASS]" if met else "[FAIL]"
            print(f"  {status_icon} {criterion}")
            if not met:
                all_criteria_met = False

        if all_criteria_met:
            print(f"\n[READY] PHASE 4 READY FOR PRODUCTION!")
            print("Complete loan management system is implemented and ready for use.")
        else:
            print(f"\n[WORK NEEDED] PHASE 4 NEEDS ADDITIONAL WORK")
            print("Some loan management features require implementation or fixes.")

        return {
            "total_checks": total_checks,
            "passed": passed_checks,
            "warnings": warning_checks,
            "failed": failed_checks,
            "all_criteria_met": all_criteria_met,
            "status": status
        }


def main():
    """Run Phase 4 validation"""
    validator = Phase4Validator()
    validator.run_validation()


if __name__ == "__main__":
    main()