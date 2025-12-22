"""Validation result reporting and output formatting."""
from typing import Any, Dict, List, Union

from .models import ContractValidationReport, ValidationResult


class ValidationReporter:
    """Handles formatting and printing of validation results"""

    def print_results(
        self,
        reports: Union[ContractValidationReport, List[ContractValidationReport]],
        verbose: bool = True,
        summary_only: bool = False,
        detailed_failures: bool = True,
    ) -> None:
        """
        Print validation results in a readable format

        Args:
            reports: Single ContractValidationReport or list of reports
            verbose: If True, print all results; if False, only print failures
            summary_only: If True, only print summary without individual check details
            detailed_failures: If True, print a detailed failure report at the end
        """
        # Handle single report
        if isinstance(reports, ContractValidationReport):
            reports = [reports]

        # Overall statistics
        total_contracts = len(reports)
        successful_contracts = sum(1 for r in reports if r.success)
        failed_contracts = total_contracts - successful_contracts
        total_checks = sum(r.total_checks for r in reports)
        total_passed = sum(r.passed_checks for r in reports)

        print(f"\n{'=' * 80}")
        print("VALIDATION SUMMARY")
        print(f"{'=' * 80}")
        print(f"Contracts: {successful_contracts}/{total_contracts} passed")
        print(f"Checks: {total_passed}/{total_checks} passed")
        print(f"{'=' * 80}\n")

        if summary_only:
            # Print per-contract summary
            for report in reports:
                status = "✓" if report.success else "✗"
                print(
                    f"{status} {report.contract_file}: "
                    f"{report.passed_checks}/{report.total_checks} checks passed"
                )
            print()

            # Print detailed failures even in summary mode if requested
            if detailed_failures and failed_contracts > 0:
                self._print_detailed_failures(reports)

            return

        # Detailed results per contract
        for report in reports:
            status_symbol = "✓" if report.success else "✗"
            print(f"\n{status_symbol} Contract: {report.contract_file}")
            print(
                f"   Checks: {report.passed_checks} passed, "
                f"{report.failed_checks} failed"
            )
            print(f"   {'-' * 76}")

            for result in report.results:
                if verbose or not result.passed:
                    status = "  ✓" if result.passed else "  ✗"
                    print(f"  {status} [{result.check_type}] {result.message}")

            print()

        print(f"{'=' * 80}\n")

        # Print detailed failure report
        if detailed_failures and failed_contracts > 0:
            self._print_detailed_failures(reports)

    def _print_detailed_failures(self, reports: List[ContractValidationReport]) -> None:
        """
        Print a detailed report of all failures grouped by contract and check type

        Args:
            reports: List of ContractValidationReport objects
        """
        failed_reports = [r for r in reports if not r.success]

        if not failed_reports:
            return

        print(f"\n{'=' * 80}")
        print("DETAILED FAILURE REPORT")
        print(f"{'=' * 80}\n")

        for report in failed_reports:
            failed_results = [r for r in report.results if not r.passed]

            if not failed_results:
                continue

            print(f"Contract: {report.contract_file}")
            print(f"Failed Checks: {len(failed_results)}")
            print(f"{'-' * 80}")

            # Group failures by check type
            failures_by_type: Dict[str, List[ValidationResult]] = {}
            for result in failed_results:
                if result.check_type not in failures_by_type:
                    failures_by_type[result.check_type] = []
                failures_by_type[result.check_type].append(result)

            # Print grouped failures
            for check_type, failures in failures_by_type.items():
                print(f"\n  {check_type.upper()} FAILURES ({len(failures)}):")
                for failure in failures:
                    print(f"    ✗ Attribute: {failure.attribute}")
                    print(f"      Issue: {failure.message}")
                    print()

            print(f"{'=' * 80}\n")

        # Summary of failure patterns
        self._print_failure_patterns(failed_reports)

    def _print_failure_patterns(
        self, failed_reports: List[ContractValidationReport]
    ) -> None:
        """
        Print a summary of common failure patterns across all failed contracts

        Args:
            failed_reports: List of failed ContractValidationReport objects
        """
        print("FAILURE PATTERNS SUMMARY")
        print(f"{'-' * 80}")

        # Collect all failures
        all_failures = []
        for report in failed_reports:
            all_failures.extend([r for r in report.results if not r.passed])

        # Group by check type
        by_check_type: Dict[str, List[ValidationResult]] = {}
        for failure in all_failures:
            if failure.check_type not in by_check_type:
                by_check_type[failure.check_type] = []
            by_check_type[failure.check_type].append(failure)

        print("\nFailures by Check Type:")
        for check_type, failures in sorted(by_check_type.items()):
            print(f"  • {check_type}: {len(failures)} failure(s)")

        # Group by attribute
        by_attribute: Dict[str, List[ValidationResult]] = {}
        for failure in all_failures:
            if failure.attribute not in by_attribute:
                by_attribute[failure.attribute] = []
            by_attribute[failure.attribute].append(failure)

        print("\nMost Common Failing Attributes:")
        sorted_attrs = sorted(
            by_attribute.items(), key=lambda x: len(x[1]), reverse=True
        )
        for attribute, failures in sorted_attrs[:5]:  # Top 5
            contracts = set(f.contract_file for f in failures)
            print(
                f"  • {attribute}: {len(failures)} failure(s) across "
                f"{len(contracts)} contract(s)"
            )

        print(f"\n{'=' * 80}\n")

    def get_summary(self, reports: List[ContractValidationReport]) -> Dict[str, Any]:
        """
        Get a summary dictionary of validation results

        Args:
            reports: List of ContractValidationReport objects

        Returns:
            Dictionary with summary statistics
        """
        return {
            "total_contracts": len(reports),
            "passed_contracts": sum(1 for r in reports if r.success),
            "failed_contracts": sum(1 for r in reports if not r.success),
            "total_checks": sum(r.total_checks for r in reports),
            "passed_checks": sum(r.passed_checks for r in reports),
            "failed_checks": sum(r.failed_checks for r in reports),
            "contracts": [
                {
                    "file": r.contract_file,
                    "success": r.success,
                    "passed": r.passed_checks,
                    "failed": r.failed_checks,
                }
                for r in reports
            ],
        }
