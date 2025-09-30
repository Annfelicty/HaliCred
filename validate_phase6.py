#!/usr/bin/env python3
"""
Phase 6 Validation Script - Comprehensive Testing Infrastructure Validation
Validates all Phase 6 requirements and objectives for HaliCred project.
"""

import os
import sys
import json
import subprocess
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

class Phase6Validator:
    """Comprehensive Phase 6 validation and testing."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend-web"
        self.results = {}
        self.start_time = time.time()

    def print_header(self, title: str):
        """Print formatted section header."""
        print(f"\n{'='*60}")
        print(f"🎯 {title}")
        print(f"{'='*60}")

    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result with formatting."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        return passed

    def run_command(self, cmd: List[str], cwd: Path = None, timeout: int = 300) -> Tuple[bool, str]:
        """Run command and return success status and output."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, str(e)

    def validate_backend_test_infrastructure(self) -> bool:
        """Validate backend test infrastructure is properly set up."""
        self.print_header("Backend Test Infrastructure Validation")

        success = True

        # Check test files exist
        required_test_files = [
            "tests/conftest.py",
            "tests/test_api_comprehensive.py",
            "tests/test_database_integration.py",
            "tests/test_auth_comprehensive.py",
            "tests/test_ai_processing.py",
            "tests/test_loan_system.py",
            "tests/test_monitoring_security.py",
            "tests/test_performance.py",
            "tests/pytest.ini",
            "run_tests.py"
        ]

        for test_file in required_test_files:
            file_path = self.backend_dir / test_file
            passed = file_path.exists()
            success &= self.print_result(f"Test file exists: {test_file}", passed)

        # Check test configuration
        pytest_ini = self.backend_dir / "tests" / "pytest.ini"
        if pytest_ini.exists():
            with open(pytest_ini, 'r') as f:
                content = f.read()
                has_markers = "markers =" in content
                has_coverage = "cov=" in content
                success &= self.print_result("Pytest configuration has markers", has_markers)
                success &= self.print_result("Pytest configuration has coverage", has_coverage)

        # Test the test runner
        success_runner, output = self.run_command(
            ["python", "run_tests.py", "smoke"],
            cwd=self.backend_dir,
            timeout=60
        )
        success &= self.print_result("Test runner executes", success_runner, output[:100] if output else "")

        self.results["backend_infrastructure"] = success
        return success

    def validate_backend_test_coverage(self) -> bool:
        """Run backend tests and validate coverage."""
        self.print_header("Backend Test Coverage Validation")

        success = True

        # Run different test categories
        test_categories = [
            ("unit", "Unit tests"),
            ("integration", "Integration tests"),
            ("api", "API tests"),
            ("security", "Security tests"),
            ("monitoring", "Monitoring tests")
        ]

        for category, description in test_categories:
            test_success, output = self.run_command(
                ["python", "run_tests.py", category],
                cwd=self.backend_dir,
                timeout=120
            )
            success &= self.print_result(f"{description}", test_success)

        # Run coverage report
        coverage_success, coverage_output = self.run_command(
            ["python", "run_tests.py", "coverage"],
            cwd=self.backend_dir,
            timeout=180
        )

        if coverage_success:
            # Parse coverage from output
            lines = coverage_output.split('\n')
            coverage_line = next((line for line in lines if 'TOTAL' in line), None)
            if coverage_line:
                try:
                    coverage_pct = int(coverage_line.split()[-1].replace('%', ''))
                    coverage_meets_threshold = coverage_pct >= 80
                    success &= self.print_result(
                        f"Backend coverage meets 80% threshold ({coverage_pct}%)",
                        coverage_meets_threshold
                    )
                except:
                    success &= self.print_result("Backend coverage parsing", False, "Could not parse coverage")
            else:
                success &= self.print_result("Backend coverage report", False, "No coverage total found")
        else:
            success &= self.print_result("Backend coverage generation", False)

        self.results["backend_coverage"] = success
        return success

    def validate_frontend_test_infrastructure(self) -> bool:
        """Validate frontend test infrastructure."""
        self.print_header("Frontend Test Infrastructure Validation")

        success = True

        # Check test configuration files
        required_files = [
            "jest.config.js",
            "src/test/setup.ts",
            "src/test/utils/test-utils.tsx",
            "src/test/mocks/server.ts"
        ]

        for file_path in required_files:
            full_path = self.frontend_dir / file_path
            passed = full_path.exists()
            success &= self.print_result(f"Frontend test file: {file_path}", passed)

        # Check test files exist
        test_directories = [
            "src/Components/Sme/__tests__",
            "src/Components/Ui/__tests__",
            "src/hooks/__tests__"
        ]

        for test_dir in test_directories:
            dir_path = self.frontend_dir / test_dir
            if dir_path.exists():
                test_files = list(dir_path.glob("*.test.{ts,tsx}"))
                has_tests = len(test_files) > 0
                success &= self.print_result(f"Test files in {test_dir}", has_tests, f"Found {len(test_files)} test files")
            else:
                success &= self.print_result(f"Test directory: {test_dir}", False)

        # Check package.json has test scripts
        package_json = self.frontend_dir / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                package_data = json.load(f)
                scripts = package_data.get('scripts', {})
                has_test_scripts = all(script in scripts for script in ['test', 'test:coverage'])
                success &= self.print_result("Package.json has test scripts", has_test_scripts)

        self.results["frontend_infrastructure"] = success
        return success

    def validate_frontend_test_coverage(self) -> bool:
        """Run frontend tests and validate coverage."""
        self.print_header("Frontend Test Coverage Validation")

        success = True

        # Install dependencies first
        install_success, _ = self.run_command(
            ["npm", "ci"],
            cwd=self.frontend_dir,
            timeout=300
        )

        if not install_success:
            success &= self.print_result("Frontend dependencies installation", False)
            self.results["frontend_coverage"] = False
            return False

        # Run tests with coverage
        test_success, test_output = self.run_command(
            ["npm", "run", "test:coverage"],
            cwd=self.frontend_dir,
            timeout=300
        )

        success &= self.print_result("Frontend tests execution", test_success)

        if test_success:
            # Check for coverage report
            coverage_dir = self.frontend_dir / "coverage"
            lcov_file = coverage_dir / "lcov.info"

            coverage_exists = lcov_file.exists()
            success &= self.print_result("Coverage report generated", coverage_exists)

            # Try to parse coverage percentage
            if "%" in test_output:
                try:
                    # Extract coverage percentage from output
                    lines = test_output.split('\n')
                    coverage_lines = [line for line in lines if '%' in line and ('All files' in line or 'Statements' in line)]
                    if coverage_lines:
                        # Parse coverage percentage (simplified)
                        coverage_line = coverage_lines[0]
                        import re
                        match = re.search(r'(\d+\.?\d*)%', coverage_line)
                        if match:
                            coverage_pct = float(match.group(1))
                            coverage_meets_threshold = coverage_pct >= 75
                            success &= self.print_result(
                                f"Frontend coverage meets 75% threshold ({coverage_pct}%)",
                                coverage_meets_threshold
                            )
                except:
                    success &= self.print_result("Frontend coverage parsing", False)

        self.results["frontend_coverage"] = success
        return success

    def validate_e2e_test_infrastructure(self) -> bool:
        """Validate E2E test infrastructure."""
        self.print_header("E2E Test Infrastructure Validation")

        success = True

        # Check E2E configuration files
        e2e_files = [
            "playwright.config.ts",
            "src/e2e/global-setup.ts",
            "src/e2e/global-teardown.ts"
        ]

        for file_path in e2e_files:
            full_path = self.frontend_dir / file_path
            passed = full_path.exists()
            success &= self.print_result(f"E2E config file: {file_path}", passed)

        # Check E2E test files
        e2e_test_files = [
            "src/e2e/auth.spec.ts",
            "src/e2e/loan-application.spec.ts",
            "src/e2e/evidence-upload.spec.ts"
        ]

        for test_file in e2e_test_files:
            full_path = self.frontend_dir / test_file
            passed = full_path.exists()
            success &= self.print_result(f"E2E test file: {test_file}", passed)

        # Check fixtures directory
        fixtures_dir = self.frontend_dir / "src/e2e/fixtures"
        fixtures_script = fixtures_dir / "create-test-files.js"

        success &= self.print_result("E2E fixtures directory", fixtures_dir.exists())
        success &= self.print_result("E2E fixtures script", fixtures_script.exists())

        # Check Playwright installation
        if (self.frontend_dir / "node_modules/@playwright").exists():
            success &= self.print_result("Playwright installation", True)
        else:
            success &= self.print_result("Playwright installation", False, "Run: npx playwright install")

        self.results["e2e_infrastructure"] = success
        return success

    def validate_quality_gates_setup(self) -> bool:
        """Validate quality gates and CI/CD configuration."""
        self.print_header("Quality Gates & CI/CD Validation")

        success = True

        # Check GitHub Actions workflow
        workflow_file = self.project_root / ".github/workflows/phase6-testing.yml"
        success &= self.print_result("GitHub Actions workflow exists", workflow_file.exists())

        if workflow_file.exists():
            with open(workflow_file, 'r') as f:
                content = f.read()

                # Check for essential jobs
                required_jobs = [
                    "code-quality",
                    "backend-tests",
                    "frontend-tests",
                    "e2e-tests",
                    "quality-gates"
                ]

                for job in required_jobs:
                    has_job = job in content
                    success &= self.print_result(f"Workflow has {job} job", has_job)

                # Check for coverage requirements
                has_coverage_gates = "coverage" in content and "fail-under" in content
                success &= self.print_result("Workflow has coverage gates", has_coverage_gates)

        # Check for other quality gate files
        quality_files = [
            ".github/workflows/phase6-testing.yml",
            "backend/run_tests.py",
            "frontend-web/jest.config.js"
        ]

        for file_path in quality_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            success &= self.print_result(f"Quality gate file: {file_path}", exists)

        self.results["quality_gates"] = success
        return success

    def validate_documentation_completeness(self) -> bool:
        """Validate Phase 6 documentation completeness."""
        self.print_header("Documentation Completeness Validation")

        success = True

        # Check for test documentation
        doc_files = [
            "backend/tests/README.md",
            "frontend-web/src/test/README.md",
            "backend/run_tests.py",  # Should have help/documentation
        ]

        for doc_file in doc_files:
            full_path = self.project_root / doc_file
            if full_path.exists():
                success &= self.print_result(f"Documentation file: {doc_file}", True)
            else:
                # Some documentation files are optional
                print(f"⚠️  Optional documentation: {doc_file} (missing)")

        # Check test files have docstrings
        test_files_to_check = [
            self.backend_dir / "tests/test_api_comprehensive.py",
            self.frontend_dir / "src/Components/Sme/__tests__/SMEDashboard.test.tsx"
        ]

        for test_file in test_files_to_check:
            if test_file.exists():
                with open(test_file, 'r') as f:
                    content = f.read()
                    has_docstring = '"""' in content or "'''" in content
                    success &= self.print_result(f"Test file has documentation: {test_file.name}", has_docstring)

        self.results["documentation"] = success
        return success

    def validate_performance_requirements(self) -> bool:
        """Validate performance testing capabilities."""
        self.print_header("Performance Testing Validation")

        success = True

        # Check performance test files exist
        perf_files = [
            "backend/tests/test_performance.py",
            "frontend-web/src/Components/Ui/__tests__/loading.test.tsx"  # Performance-related UI tests
        ]

        for perf_file in perf_files:
            full_path = self.project_root / perf_file
            passed = full_path.exists()
            success &= self.print_result(f"Performance test file: {perf_file}", passed)

        # Check for performance testing markers/categories
        backend_conftest = self.backend_dir / "tests/conftest.py"
        if backend_conftest.exists():
            with open(backend_conftest, 'r') as f:
                content = f.read()
                has_perf_marker = "performance" in content
                success &= self.print_result("Backend has performance test markers", has_perf_marker)

        # Check for load testing capabilities
        backend_run_tests = self.backend_dir / "run_tests.py"
        if backend_run_tests.exists():
            with open(backend_run_tests, 'r') as f:
                content = f.read()
                has_perf_tests = "performance" in content
                success &= self.print_result("Test runner supports performance tests", has_perf_tests)

        self.results["performance"] = success
        return success

    def generate_phase6_report(self) -> Dict[str, Any]:
        """Generate comprehensive Phase 6 validation report."""
        self.print_header("Phase 6 Validation Summary")

        total_time = time.time() - self.start_time

        # Calculate overall success
        all_passed = all(self.results.values())
        passed_count = sum(self.results.values())
        total_count = len(self.results)

        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 6 - Test Suite Expansion & Quality Gates",
            "validation_time_seconds": round(total_time, 2),
            "results": self.results,
            "summary": {
                "total_categories": total_count,
                "passed_categories": passed_count,
                "failed_categories": total_count - passed_count,
                "success_rate": round((passed_count / total_count) * 100, 1),
                "overall_status": "PHASE 6 COMPLETE" if all_passed else "PHASE 6 INCOMPLETE"
            }
        }

        # Print summary
        for category, passed in self.results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            category_name = category.replace("_", " ").title()
            print(f"{status} {category_name}")

        print(f"\n📊 Overall Success Rate: {report['summary']['success_rate']}%")
        print(f"⏱️  Validation Time: {report['validation_time_seconds']} seconds")
        print(f"🎯 Status: {report['summary']['overall_status']}")

        return report

    def save_report(self, report: Dict[str, Any]):
        """Save validation report to file."""
        report_file = self.project_root / "PHASE6_VALIDATION_REPORT.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📝 Validation report saved to: {report_file}")

    def run_complete_validation(self) -> bool:
        """Run complete Phase 6 validation."""
        print("🚀 Starting Phase 6 Comprehensive Validation")
        print(f"📁 Project Root: {self.project_root}")
        print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run all validation categories
        validation_steps = [
            self.validate_backend_test_infrastructure,
            self.validate_backend_test_coverage,
            self.validate_frontend_test_infrastructure,
            self.validate_frontend_test_coverage,
            self.validate_e2e_test_infrastructure,
            self.validate_quality_gates_setup,
            self.validate_documentation_completeness,
            self.validate_performance_requirements
        ]

        for validation_step in validation_steps:
            try:
                validation_step()
            except Exception as e:
                print(f"❌ Validation step failed: {e}")
                # Continue with other validations

        # Generate and save report
        report = self.generate_phase6_report()
        self.save_report(report)

        return report["summary"]["overall_status"] == "PHASE 6 COMPLETE"

def main():
    """Main validation entry point."""
    validator = Phase6Validator()

    try:
        success = validator.run_complete_validation()
        exit_code = 0 if success else 1

        if success:
            print("\n🎉 Phase 6 validation completed successfully!")
            print("✅ All testing infrastructure and quality gates are properly implemented.")
        else:
            print("\n⚠️  Phase 6 validation completed with issues.")
            print("❌ Some requirements may not be fully met. Check the report for details.")

        return exit_code

    except KeyboardInterrupt:
        print("\n⏸️  Validation interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())