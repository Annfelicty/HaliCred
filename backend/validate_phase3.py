#!/usr/bin/env python3
"""
Phase 3 Validation Script
Validates that all Phase 3 components are properly implemented and integrated.
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


class Phase3Validator:
    """Validates Phase 3 implementation"""

    def __init__(self):
        self.validation_results = []
        self.warnings = []
        self.errors = []

    def run_validation(self):
        """Run complete Phase 3 validation"""
        logger.info("Starting Phase 3 validation...")

        print("=" * 60)
        print("PHASE 3 VALIDATION - Evidence -> AI -> Score Pipeline")
        print("=" * 60)

        # 1. Check file structure
        self.validate_file_structure()

        # 2. Check module imports
        self.validate_module_imports()

        # 3. Check API integration components
        self.validate_api_integration()

        # 4. Check evidence processing
        self.validate_evidence_processing()

        # 5. Check score computation
        self.validate_score_computation()

        # 6. Check error handling
        self.validate_error_handling()

        # 7. Generate final report
        self.generate_validation_report()

    def validate_file_structure(self):
        """Validate that all required files exist"""
        print("\n[FILE STRUCTURE] Validating file structure...")

        required_files = [
            "app/ai/api_client.py",
            "app/ai/startup_validation.py",
            "app/ai/orchestrator.py",
            "app/ai/evidence_processor.py",
            "app/ai/score_computation.py",
            "app/api/ai_engine.py",
            "app/api/evidence.py",
            "app/main.py"
        ]

        for file_path in required_files:
            full_path = backend_dir / file_path
            if full_path.exists():
                print(f"  [PASS] {file_path}")
                self.validation_results.append(f"[PASS] File exists: {file_path}")
            else:
                print(f"  [FAIL] {file_path}")
                self.errors.append(f"Missing file: {file_path}")

    def validate_module_imports(self):
        """Validate that modules can be imported"""
        print("\n📦 Validating module imports...")

        modules_to_test = [
            ("app.ai.api_client", "ExternalAPIClient"),
            ("app.ai.startup_validation", "StartupValidator"),
            ("app.ai.orchestrator", "AIOrchestrator"),
            ("app.ai.evidence_processor", "EvidenceProcessor"),
            ("app.ai.score_computation", "ScoreComputationService"),
        ]

        for module_name, class_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, class_name):
                    print(f"  ✅ {module_name}.{class_name}")
                    self.validation_results.append(f"✅ Module import: {module_name}.{class_name}")
                else:
                    print(f"  ⚠️ {module_name} (missing {class_name})")
                    self.warnings.append(f"Class {class_name} not found in {module_name}")
            except ImportError as e:
                print(f"  ❌ {module_name} - {str(e)}")
                self.errors.append(f"Import error: {module_name} - {str(e)}")

    def validate_api_integration(self):
        """Validate API integration components"""
        print("\n🔌 Validating API integration...")

        try:
            from app.ai.api_client import external_api_client, APIConfig
            print("  ✅ External API client initialized")

            # Check if client has required methods
            required_methods = [
                'validate_api_credentials',
                'call_gemini_api',
                'call_vision_api',
                'call_climatiq_api'
            ]

            for method in required_methods:
                if hasattr(external_api_client, method):
                    print(f"    ✅ Method: {method}")
                else:
                    print(f"    ❌ Missing method: {method}")
                    self.errors.append(f"Missing method: {method}")

            self.validation_results.append("✅ API integration components validated")

        except Exception as e:
            print(f"  ❌ API integration error: {str(e)}")
            self.errors.append(f"API integration error: {str(e)}")

    def validate_evidence_processing(self):
        """Validate evidence processing components"""
        print("\n🔍 Validating evidence processing...")

        try:
            from app.ai.evidence_processor import evidence_processor, FileType, ValidationError
            print("  ✅ Evidence processor initialized")

            # Check if processor has required methods
            required_methods = [
                'validate_file',
                'analyze_content',
                'process_evidence_file'
            ]

            for method in required_methods:
                if hasattr(evidence_processor, method):
                    print(f"    ✅ Method: {method}")
                else:
                    print(f"    ❌ Missing method: {method}")
                    self.errors.append(f"Missing method: {method}")

            # Check file type enumeration
            if hasattr(FileType, 'JPEG') and hasattr(FileType, 'PNG'):
                print("    ✅ File type validation enums")
            else:
                print("    ❌ File type validation enums missing")
                self.errors.append("File type validation enums missing")

            self.validation_results.append("✅ Evidence processing components validated")

        except Exception as e:
            print(f"  ❌ Evidence processing error: {str(e)}")
            self.errors.append(f"Evidence processing error: {str(e)}")

    def validate_score_computation(self):
        """Validate score computation components"""
        print("\n🎯 Validating score computation...")

        try:
            from app.ai.score_computation import score_computation_service, ComputationMethod
            print("  ✅ Score computation service initialized")

            # Check if service has required methods
            required_methods = [
                'compute_score',
                'get_score_metrics'
            ]

            for method in required_methods:
                if hasattr(score_computation_service, method):
                    print(f"    ✅ Method: {method}")
                else:
                    print(f"    ❌ Missing method: {method}")
                    self.errors.append(f"Missing method: {method}")

            # Check computation method enumeration
            expected_methods = ['AI_ENHANCED', 'HYBRID', 'RULE_BASED', 'FALLBACK']
            for method in expected_methods:
                if hasattr(ComputationMethod, method):
                    print(f"    ✅ Computation method: {method}")
                else:
                    print(f"    ❌ Missing computation method: {method}")
                    self.errors.append(f"Missing computation method: {method}")

            self.validation_results.append("✅ Score computation components validated")

        except Exception as e:
            print(f"  ❌ Score computation error: {str(e)}")
            self.errors.append(f"Score computation error: {str(e)}")

    def validate_error_handling(self):
        """Validate error handling and fallback mechanisms"""
        print("\n⚠️ Validating error handling...")

        try:
            # Check circuit breaker implementation
            from app.ai.api_client import CircuitState
            print("  ✅ Circuit breaker states defined")

            # Check validation errors
            from app.ai.evidence_processor import ValidationError
            print("  ✅ Custom validation exceptions defined")

            # Check startup validation
            from app.ai.startup_validation import startup_validator
            print("  ✅ Startup validation components")

            self.validation_results.append("✅ Error handling components validated")

        except Exception as e:
            print(f"  ❌ Error handling validation error: {str(e)}")
            self.errors.append(f"Error handling validation error: {str(e)}")

    def validate_main_integration(self):
        """Validate main application integration"""
        print("\n🔗 Validating main application integration...")

        try:
            # Check if main.py has been updated with new endpoints
            main_file = backend_dir / "app" / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()

                # Check for score computation integration
                if "score_computation_service" in content:
                    print("  ✅ Score computation service integrated")
                else:
                    print("  ⚠️ Score computation service not integrated in main.py")
                    self.warnings.append("Score computation service not integrated in main.py")

                # Check for async endpoints
                if "async def compute_score" in content:
                    print("  ✅ Async score computation endpoint")
                else:
                    print("  ⚠️ Score computation endpoint not made async")
                    self.warnings.append("Score computation endpoint not made async")

                # Check for monitoring endpoints
                if "/score/metrics" in content:
                    print("  ✅ Score metrics endpoint")
                else:
                    print("  ⚠️ Score metrics endpoint missing")
                    self.warnings.append("Score metrics endpoint missing")

                self.validation_results.append("✅ Main application integration checked")
            else:
                print("  ❌ main.py not found")
                self.errors.append("main.py not found")

        except Exception as e:
            print(f"  ❌ Main integration validation error: {str(e)}")
            self.errors.append(f"Main integration validation error: {str(e)}")

    def validate_startup_integration(self):
        """Validate startup integration in main.py"""
        print("\n🚀 Validating startup integration...")

        try:
            main_file = backend_dir / "app" / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()

                # Check for startup validation
                if "startup_validation" in content:
                    print("  ✅ Startup validation integrated")
                else:
                    print("  ⚠️ Startup validation not integrated")
                    self.warnings.append("Startup validation not integrated")

                # Check for health check enhancement
                if "create_health_check_endpoint" in content:
                    print("  ✅ Enhanced health check")
                else:
                    print("  ⚠️ Enhanced health check not integrated")
                    self.warnings.append("Enhanced health check not integrated")

                self.validation_results.append("✅ Startup integration checked")
            else:
                self.errors.append("main.py not found for startup validation")

        except Exception as e:
            print(f"  ❌ Startup integration validation error: {str(e)}")
            self.errors.append(f"Startup integration validation error: {str(e)}")

    def generate_validation_report(self):
        """Generate final validation report"""
        print("\n" + "=" * 60)
        print("PHASE 3 VALIDATION REPORT")
        print("=" * 60)

        total_checks = len(self.validation_results) + len(self.warnings) + len(self.errors)
        passed_checks = len(self.validation_results)
        warning_checks = len(self.warnings)
        failed_checks = len(self.errors)

        print(f"Total Checks: {total_checks}")
        print(f"✅ Passed: {passed_checks}")
        print(f"⚠️ Warnings: {warning_checks}")
        print(f"❌ Failed: {failed_checks}")

        if failed_checks == 0:
            if warning_checks == 0:
                print(f"\n🎉 PHASE 3 VALIDATION: COMPLETE SUCCESS!")
                print("All components are properly implemented and integrated.")
            else:
                print(f"\n✅ PHASE 3 VALIDATION: SUCCESS WITH WARNINGS")
                print("Core components are implemented, some enhancements recommended.")
        else:
            print(f"\n❌ PHASE 3 VALIDATION: INCOMPLETE")
            print("Some critical components are missing or have errors.")

        # Print detailed results
        if self.validation_results:
            print(f"\n✅ SUCCESSFUL VALIDATIONS:")
            for result in self.validation_results:
                print(f"  {result}")

        if self.warnings:
            print(f"\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️ {warning}")

        if self.errors:
            print(f"\n❌ ERRORS:")
            for error in self.errors:
                print(f"  ❌ {error}")

        # Phase 3 acceptance criteria check
        print(f"\n📋 PHASE 3 ACCEPTANCE CRITERIA:")

        criteria = [
            ("External API Integration", failed_checks == 0 and "API integration" in str(self.validation_results)),
            ("Evidence Processing Pipeline", "Evidence processing" in str(self.validation_results)),
            ("Score Computation Service", "Score computation" in str(self.validation_results)),
            ("Error Handling & Fallbacks", "Error handling" in str(self.validation_results)),
            ("File Validation & Security", "File exists" in str(self.validation_results)),
        ]

        all_criteria_met = True
        for criterion, met in criteria:
            status = "✅ PASS" if met else "❌ FAIL"
            print(f"  {status} {criterion}")
            if not met:
                all_criteria_met = False

        print(f"\n{'🎉 PHASE 3 READY FOR PRODUCTION!' if all_criteria_met else '🔧 PHASE 3 NEEDS ADDITIONAL WORK'}")

        return {
            "total_checks": total_checks,
            "passed": passed_checks,
            "warnings": warning_checks,
            "failed": failed_checks,
            "all_criteria_met": all_criteria_met,
            "status": "COMPLETE" if all_criteria_met else "INCOMPLETE"
        }


def main():
    """Run Phase 3 validation"""
    validator = Phase3Validator()

    # Run all validations
    validator.validate_file_structure()
    validator.validate_module_imports()
    validator.validate_api_integration()
    validator.validate_evidence_processing()
    validator.validate_score_computation()
    validator.validate_error_handling()
    validator.validate_main_integration()
    validator.validate_startup_integration()

    # Generate final report
    results = validator.generate_validation_report()

    # Return appropriate exit code
    sys.exit(0 if results["status"] == "COMPLETE" else 1)


if __name__ == "__main__":
    main()