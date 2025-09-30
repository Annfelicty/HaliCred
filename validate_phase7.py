#!/usr/bin/env python3
"""
Phase 7 Validation Script - Documentation & Handover Validation
Validates all Phase 7 requirements for HaliCred project.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

class Phase7Validator:
    """Phase 7 validation for documentation and handover completion."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.docs_dir = self.project_root / "docs"
        self.results = {}

    def print_result(self, test_name: str, passed: bool) -> bool:
        """Print test result."""
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}")
        return passed

    def validate_documentation_infrastructure(self) -> bool:
        """Validate documentation infrastructure and organization."""
        print("\n=== Documentation Infrastructure ===")

        success = True
        required_files = [
            "README.md",
            "architecture.md",
            "api-documentation.md",
            "database-schema.md",
            "ai-pipeline.md",
            "deployment-guide.md",
            "monitoring-runbook.md",
            "user-guide-sme.md",
            "user-guide-bank.md",
            "troubleshooting.md",
            "knowledge-transfer.md",
            "developer-guide.md"
        ]

        for file_name in required_files:
            file_path = self.docs_dir / file_name
            passed = file_path.exists()
            success &= self.print_result(f"Documentation file: {file_name}", passed)

        # Check documentation directory structure
        success &= self.print_result("Documentation directory exists", self.docs_dir.exists())

        self.results["Documentation Infrastructure"] = success
        return success

    def validate_technical_documentation(self) -> bool:
        """Validate technical documentation completeness."""
        print("\n=== Technical Documentation ===")

        success = True

        # Check API documentation content
        api_doc = self.docs_dir / "api-documentation.md"
        if api_doc.exists():
            content = api_doc.read_text(encoding='utf-8')
            api_checks = [
                ("Authentication endpoints", "/auth/" in content),
                ("Evidence endpoints", "/evidence/" in content),
                ("AI engine endpoints", "/ai/" in content),
                ("Error codes reference", "Error Code" in content),
                ("Rate limiting", "Rate Limiting" in content)
            ]

            for check_name, check_result in api_checks:
                success &= self.print_result(f"API doc includes {check_name}", check_result)

        # Check architecture documentation
        arch_doc = self.docs_dir / "architecture.md"
        if arch_doc.exists():
            content = arch_doc.read_text(encoding='utf-8')
            arch_checks = [
                ("System overview", "Overview" in content),
                ("AI pipeline", "AI" in content and "pipeline" in content.lower()),
                ("Database design", "PostgreSQL" in content or "Database" in content),
                ("External integrations", "Gemini" in content or "Vision" in content)
            ]

            for check_name, check_result in arch_checks:
                success &= self.print_result(f"Architecture doc includes {check_name}", check_result)

        # Check database schema documentation
        db_doc = self.docs_dir / "database-schema.md"
        if db_doc.exists():
            content = db_doc.read_text(encoding='utf-8')
            db_checks = [
                ("Core tables", "users" in content.lower()),
                ("Relationships", "relationship" in content.lower()),
                ("Indexes", "index" in content.lower()),
                ("Data types", "UUID" in content or "JSONB" in content)
            ]

            for check_name, check_result in db_checks:
                success &= self.print_result(f"Database doc includes {check_name}", check_result)

        self.results["Technical Documentation"] = success
        return success

    def validate_operational_documentation(self) -> bool:
        """Validate operational documentation completeness."""
        print("\n=== Operational Documentation ===")

        success = True

        # Check deployment guide
        deploy_doc = self.docs_dir / "deployment-guide.md"
        if deploy_doc.exists():
            content = deploy_doc.read_text(encoding='utf-8')
            deploy_checks = [
                ("Prerequisites", "Prerequisites" in content),
                ("Environment setup", "Environment" in content),
                ("Database setup", "PostgreSQL" in content or "Database" in content),
                ("SSL configuration", "SSL" in content or "certificate" in content.lower()),
                ("Docker deployment", "Docker" in content)
            ]

            for check_name, check_result in deploy_checks:
                success &= self.print_result(f"Deployment guide includes {check_name}", check_result)

        # Check monitoring runbook
        monitor_doc = self.docs_dir / "monitoring-runbook.md"
        if monitor_doc.exists():
            content = monitor_doc.read_text(encoding='utf-8')
            monitor_checks = [
                ("Health checks", "health" in content.lower()),
                ("Alerting", "alert" in content.lower()),
                ("Metrics", "metric" in content.lower()),
                ("Incident response", "incident" in content.lower()),
                ("Troubleshooting", "troubleshoot" in content.lower())
            ]

            for check_name, check_result in monitor_checks:
                success &= self.print_result(f"Monitoring runbook includes {check_name}", check_result)

        self.results["Operational Documentation"] = success
        return success

    def validate_user_documentation(self) -> bool:
        """Validate user documentation completeness."""
        print("\n=== User Documentation ===")

        success = True

        # Check SME user guide
        sme_doc = self.docs_dir / "user-guide-sme.md"
        if sme_doc.exists():
            content = sme_doc.read_text(encoding='utf-8')
            sme_checks = [
                ("Getting started", "Getting Started" in content),
                ("Evidence upload", "evidence" in content.lower() and "upload" in content.lower()),
                ("Green score", "green score" in content.lower()),
                ("Loan application", "loan" in content.lower()),
                ("Troubleshooting", "troubleshoot" in content.lower() or "problem" in content.lower())
            ]

            for check_name, check_result in sme_checks:
                success &= self.print_result(f"SME guide includes {check_name}", check_result)

        # Check bank user guide
        bank_doc = self.docs_dir / "user-guide-bank.md"
        if bank_doc.exists():
            content = bank_doc.read_text(encoding='utf-8')
            bank_checks = [
                ("Portal overview", "Portal" in content or "Dashboard" in content),
                ("Application review", "application" in content.lower() and "review" in content.lower()),
                ("Risk assessment", "risk" in content.lower()),
                ("Decision making", "decision" in content.lower()),
                ("Portfolio management", "portfolio" in content.lower())
            ]

            for check_name, check_result in bank_checks:
                success &= self.print_result(f"Bank guide includes {check_name}", check_result)

        # Check troubleshooting guide
        trouble_doc = self.docs_dir / "troubleshooting.md"
        if trouble_doc.exists():
            content = trouble_doc.read_text(encoding='utf-8')
            trouble_checks = [
                ("Common issues", "issue" in content.lower() or "problem" in content.lower()),
                ("Error codes", "error" in content.lower() and "code" in content.lower()),
                ("Solutions", "solution" in content.lower() or "fix" in content.lower()),
                ("Support contact", "support" in content.lower()),
                ("Escalation", "escalat" in content.lower() or "contact" in content.lower())
            ]

            for check_name, check_result in trouble_checks:
                success &= self.print_result(f"Troubleshooting guide includes {check_name}", check_result)

        self.results["User Documentation"] = success
        return success

    def validate_knowledge_transfer(self) -> bool:
        """Validate knowledge transfer documentation."""
        print("\n=== Knowledge Transfer ===")

        success = True

        # Check knowledge transfer document
        kt_doc = self.docs_dir / "knowledge-transfer.md"
        if kt_doc.exists():
            content = kt_doc.read_text(encoding='utf-8')
            kt_checks = [
                ("Project overview", "overview" in content.lower() or "summary" in content.lower()),
                ("Technical architecture", "architecture" in content.lower()),
                ("Codebase structure", "codebase" in content.lower() or "structure" in content.lower()),
                ("Critical knowledge", "critical" in content.lower() or "important" in content.lower()),
                ("Team handover", "handover" in content.lower() or "transfer" in content.lower()),
                ("Support procedures", "support" in content.lower() or "contact" in content.lower())
            ]

            for check_name, check_result in kt_checks:
                success &= self.print_result(f"Knowledge transfer includes {check_name}", check_result)

        # Check developer guide
        dev_doc = self.docs_dir / "developer-guide.md"
        if dev_doc.exists():
            content = dev_doc.read_text(encoding='utf-8')
            dev_checks = [
                ("Setup instructions", "setup" in content.lower() or "install" in content.lower()),
                ("Development workflow", "workflow" in content.lower() or "process" in content.lower()),
                ("Coding standards", "standard" in content.lower() or "convention" in content.lower()),
                ("Testing guidelines", "test" in content.lower()),
                ("Contributing", "contribut" in content.lower())
            ]

            for check_name, check_result in dev_checks:
                success &= self.print_result(f"Developer guide includes {check_name}", check_result)

        self.results["Knowledge Transfer"] = success
        return success

    def validate_documentation_quality(self) -> bool:
        """Validate documentation quality and completeness."""
        print("\n=== Documentation Quality ===")

        success = True

        # Count documentation files
        doc_files = list(self.docs_dir.glob("*.md"))
        file_count = len(doc_files)
        success &= self.print_result(f"Sufficient documentation files ({file_count} >= 10)", file_count >= 10)

        # Check total content volume
        total_lines = 0
        for doc_file in doc_files:
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    total_lines += lines
            except Exception:
                continue

        success &= self.print_result(f"Sufficient content volume ({total_lines} lines >= 5000)", total_lines >= 5000)

        # Check for README index
        readme_path = self.docs_dir / "README.md"
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding='utf-8')
            readme_checks = [
                ("Documentation index", "documentation" in readme_content.lower()),
                ("Structure explanation", "structure" in readme_content.lower()),
                ("Navigation links", ".md" in readme_content),
                ("Quick start", "quick" in readme_content.lower() or "start" in readme_content.lower())
            ]

            for check_name, check_result in readme_checks:
                success &= self.print_result(f"README includes {check_name}", check_result)

        # Check for consistent versioning
        version_files = 0
        for doc_file in doc_files[:5]:  # Check first 5 files
            try:
                content = doc_file.read_text(encoding='utf-8')
                if "7.0.0" in content or "Version" in content:
                    version_files += 1
            except Exception:
                continue

        success &= self.print_result(f"Consistent versioning ({version_files} files have version info)", version_files >= 3)

        self.results["Documentation Quality"] = success
        return success

    def generate_report(self) -> dict:
        """Generate validation report."""
        print("\n=== Phase 7 Validation Summary ===")

        total = len(self.results)
        passed = sum(self.results.values())
        success_rate = (passed / total) * 100 if total > 0 else 0

        for category, result in self.results.items():
            status = "PASS" if result else "FAIL"
            print(f"[{status}] {category}")

        print(f"\nSummary: {passed}/{total} categories passed ({success_rate:.1f}%)")

        overall_status = "PHASE 7 COMPLETE" if all(self.results.values()) else "PHASE 7 INCOMPLETE"
        print(f"Status: {overall_status}")

        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 7 - Documentation & Handover",
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
        print("Starting Phase 7 Validation...")
        print(f"Project Root: {self.project_root}")
        print(f"Time: {datetime.now()}")

        # Run all validations
        self.validate_documentation_infrastructure()
        self.validate_technical_documentation()
        self.validate_operational_documentation()
        self.validate_user_documentation()
        self.validate_knowledge_transfer()
        self.validate_documentation_quality()

        # Generate report
        report = self.generate_report()

        # Save report
        report_file = self.project_root / "PHASE7_VALIDATION_REPORT.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved to: {report_file}")

        return report["summary"]["status"] == "PHASE 7 COMPLETE"

def main():
    """Main entry point."""
    validator = Phase7Validator()

    try:
        success = validator.run_validation()
        if success:
            print("\nValidation completed successfully!")
            print("Phase 7 - Documentation & Handover is COMPLETE!")
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