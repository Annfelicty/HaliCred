#!/usr/bin/env python3
"""
Comprehensive test runner for HaliCred backend Phase 6 testing.
Provides multiple test execution modes and detailed reporting.
"""

import subprocess
import sys
import argparse
import time
import os
from pathlib import Path


class TestRunner:
    """Advanced test runner with multiple execution modes."""

    def __init__(self):
        self.test_dir = Path(__file__).parent / "tests"
        self.backend_dir = Path(__file__).parent
        self.project_root = self.backend_dir.parent

    def run_command(self, cmd, description=""):
        """Run a command and capture output."""
        print(f"\n{'='*60}")
        if description:
            print(f"🔄 {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                check=False
            )

            duration = time.time() - start_time

            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            print(f"\n⏱️  Duration: {duration:.2f} seconds")
            print(f"📊 Exit Code: {result.returncode}")

            return result.returncode == 0, result

        except Exception as e:
            print(f"❌ Error running command: {e}")
            return False, None

    def run_unit_tests(self):
        """Run unit tests only."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-m", "unit",
            "--tb=short",
            "-v"
        ]
        return self.run_command(cmd, "Running Unit Tests")

    def run_integration_tests(self):
        """Run integration tests only."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-m", "integration",
            "--tb=short",
            "-v"
        ]
        return self.run_command(cmd, "Running Integration Tests")

    def run_api_tests(self):
        """Run API endpoint tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/test_api_comprehensive.py",
            "tests/test_auth_comprehensive.py",
            "tests/test_loan_system.py",
            "-v",
            "--tb=short"
        ]
        return self.run_command(cmd, "Running API Tests")

    def run_security_tests(self):
        """Run security and authentication tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-m", "security or auth",
            "-v",
            "--tb=short"
        ]
        return self.run_command(cmd, "Running Security Tests")

    def run_performance_tests(self):
        """Run performance tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance.py",
            "-v",
            "--tb=short",
            "-s"  # Don't capture output for performance tests
        ]
        return self.run_command(cmd, "Running Performance Tests")

    def run_ai_tests(self):
        """Run AI processing tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/test_ai_processing.py",
            "-v",
            "--tb=short"
        ]
        return self.run_command(cmd, "Running AI Processing Tests")

    def run_monitoring_tests(self):
        """Run monitoring and health check tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/test_monitoring_security.py",
            "-v",
            "--tb=short"
        ]
        return self.run_command(cmd, "Running Monitoring & Security Tests")

    def run_database_tests(self):
        """Run database integration tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/test_database_integration.py",
            "-v",
            "--tb=short"
        ]
        return self.run_command(cmd, "Running Database Tests")

    def run_all_fast_tests(self):
        """Run all tests except slow performance tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-m", "not slow",
            "--tb=short",
            "-v",
            "--durations=10"
        ]
        return self.run_command(cmd, "Running All Fast Tests")

    def run_all_tests(self):
        """Run complete test suite."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "--tb=short",
            "-v",
            "--durations=20",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ]
        return self.run_command(cmd, "Running Complete Test Suite")

    def run_coverage_report(self):
        """Generate detailed coverage report."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=term",
            "--cov-report=xml:coverage.xml",
            "--cov-fail-under=80"
        ]
        return self.run_command(cmd, "Generating Coverage Report")

    def run_lint_checks(self):
        """Run code quality checks."""
        print("\n🔍 Running Code Quality Checks...")

        success = True

        # Run flake8 if available
        try:
            cmd = ["python", "-m", "flake8", "app/", "--max-line-length=100"]
            result, _ = self.run_command(cmd, "Running Flake8 Linting")
            success = success and result
        except:
            print("⚠️  Flake8 not available, skipping...")

        # Run black check if available
        try:
            cmd = ["python", "-m", "black", "--check", "app/"]
            result, _ = self.run_command(cmd, "Running Black Format Check")
            success = success and result
        except:
            print("⚠️  Black not available, skipping...")

        return success

    def run_phase6_validation(self):
        """Run Phase 6 specific validation tests."""
        print("\n🎯 Running Phase 6 Validation Tests...")

        test_categories = [
            ("Backend Test Infrastructure", self.run_infrastructure_check),
            ("API Comprehensive Tests", self.run_api_tests),
            ("Authentication & Security", self.run_security_tests),
            ("AI Processing Tests", self.run_ai_tests),
            ("Database Integration", self.run_database_tests),
            ("Monitoring & Health", self.run_monitoring_tests),
        ]

        results = {}
        for category, test_func in test_categories:
            print(f"\n📋 {category}")
            success, _ = test_func()
            results[category] = success

        # Summary
        print(f"\n{'='*60}")
        print("📊 PHASE 6 VALIDATION SUMMARY")
        print(f"{'='*60}")

        total = len(results)
        passed = sum(results.values())

        for category, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {category}")

        print(f"\n🎯 Overall: {passed}/{total} categories passed")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")

        return passed == total

    def run_infrastructure_check(self):
        """Check if test infrastructure is properly set up."""
        required_files = [
            "tests/conftest.py",
            "tests/test_api_comprehensive.py",
            "tests/test_database_integration.py",
            "tests/test_auth_comprehensive.py",
            "tests/test_ai_processing.py",
            "tests/test_loan_system.py",
            "tests/test_monitoring_security.py",
            "tests/test_performance.py"
        ]

        missing_files = []
        for file_path in required_files:
            full_path = self.backend_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        if missing_files:
            print(f"❌ Missing required test files:")
            for file_path in missing_files:
                print(f"   - {file_path}")
            return False, None
        else:
            print("✅ All required test files present")
            return True, None

    def run_quick_smoke_test(self):
        """Run quick smoke test to verify basic functionality."""
        cmd = [
            "python", "-m", "pytest",
            "tests/conftest.py",
            "tests/test_api_comprehensive.py::TestHealthAPI::test_health_endpoints",
            "-v",
            "--tb=line"
        ]
        return self.run_command(cmd, "Running Quick Smoke Test")

    def print_help(self):
        """Print available test commands."""
        print("""
🧪 HaliCred Backend Test Runner - Phase 6

Available Commands:
  unit                 Run unit tests only
  integration         Run integration tests only
  api                 Run API endpoint tests
  security            Run security & auth tests
  performance         Run performance tests
  ai                  Run AI processing tests
  monitoring          Run monitoring & health tests
  database            Run database tests
  fast                Run all fast tests (exclude slow)
  all                 Run complete test suite
  coverage            Generate coverage report
  lint                Run code quality checks
  phase6              Run Phase 6 validation
  smoke               Run quick smoke test
  help                Show this help message

Examples:
  python run_tests.py api
  python run_tests.py phase6
  python run_tests.py all --coverage
  python run_tests.py performance --verbose
        """)


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="HaliCred Backend Test Runner")
    parser.add_argument("test_type", nargs="?", default="help",
                      choices=["unit", "integration", "api", "security", "performance",
                              "ai", "monitoring", "database", "fast", "all", "coverage",
                              "lint", "phase6", "smoke", "help"])
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true",
                      help="Include coverage report")

    args = parser.parse_args()

    runner = TestRunner()

    print("🚀 HaliCred Backend Test Runner - Phase 6")
    print(f"📁 Test Directory: {runner.test_dir}")
    print(f"🎯 Test Type: {args.test_type}")

    if args.test_type == "help":
        runner.print_help()
        return 0

    # Map commands to methods
    test_methods = {
        "unit": runner.run_unit_tests,
        "integration": runner.run_integration_tests,
        "api": runner.run_api_tests,
        "security": runner.run_security_tests,
        "performance": runner.run_performance_tests,
        "ai": runner.run_ai_tests,
        "monitoring": runner.run_monitoring_tests,
        "database": runner.run_database_tests,
        "fast": runner.run_all_fast_tests,
        "all": runner.run_all_tests,
        "coverage": runner.run_coverage_report,
        "lint": runner.run_lint_checks,
        "phase6": runner.run_phase6_validation,
        "smoke": runner.run_quick_smoke_test
    }

    start_time = time.time()

    if args.test_type in test_methods:
        success, _ = test_methods[args.test_type]()

        if args.coverage and args.test_type not in ["coverage", "lint"]:
            print("\n📊 Generating Coverage Report...")
            runner.run_coverage_report()

        total_time = time.time() - start_time
        print(f"\n⏱️  Total Execution Time: {total_time:.2f} seconds")

        if success:
            print("✅ All tests completed successfully!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1
    else:
        print(f"❌ Unknown test type: {args.test_type}")
        runner.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())