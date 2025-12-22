import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import yaml

from contract_checker.contract.contract_base import Contract


@dataclass
class ValidationResult:
    """Represents the result of a validation check"""

    contract_file: str
    attribute: str
    check_type: str
    passed: bool
    message: str


@dataclass
class ContractValidationReport:
    """Summary report for a single contract validation"""

    contract_file: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: List[ValidationResult]

    @property
    def success(self) -> bool:
        return self.failed_checks == 0


class Check(ABC):
    """Abstract base class for all check types"""

    @abstractmethod
    def execute(
        self,
        field_path: str,
        values: List[Any],
        check_value: Any,  # noqa: ANN401
    ) -> List[ValidationResult]:
        """
        Execute the check

        Args:
            field_path: The field path being checked
            values: List of values to check
            check_value: The check configuration value

        Returns:
            List of ValidationResult objects (without contract_file,
            to be added by validator)
        """
        pass

    @property
    @abstractmethod
    def check_type(self) -> str:
        """Return the check type identifier"""
        pass


class RequiredCheck(Check):
    """Check if a required field exists and is not null"""

    @property
    def check_type(self) -> str:
        return "required"

    def execute(
        self, attribute_path: str, values: List[Any], check_value: bool
    ) -> List[ValidationResult]:
        if check_value:
            passed = len(values) > 0 and all(v is not None for v in values)
            message = (
                f"Attribute '{attribute_path}' is present"
                if passed
                else f"Required attribute '{attribute_path}' is missing or null"
            )
        else:
            passed = True
            message = f"Attribute '{attribute_path}' is optional"

        return [ValidationResult("", attribute_path, self.check_type, passed, message)]


class PatternCheck(Check):
    """Check if value matches a regex pattern"""

    @property
    def check_type(self) -> str:
        return "pattern"

    def execute(
        self, attribute_path: str, values: List[Any], pattern: str
    ) -> List[ValidationResult]:
        results = []

        for idx, value in enumerate(values):
            if value is None:
                results.append(
                    ValidationResult(
                        "",
                        attribute_path,
                        self.check_type,
                        False,
                        f"Attribute '{attribute_path}' is null, cannot match \
                            pattern '{pattern}'",
                    )
                )
                continue

            value_str = str(value)
            passed = re.match(pattern, value_str) is not None

            if passed:
                message = f"Attribute '{attribute_path}' value '{value_str}' matches \
                    pattern '{pattern}'"
            else:
                message = (
                    f"Attribute '{attribute_path}' value '{value_str}' does not match "
                    f"pattern '{pattern}'"
                )

            results.append(
                ValidationResult("", attribute_path, self.check_type, passed, message)
            )

        return results


class AcceptedValuesCheck(Check):
    """Check if a value is in a list of accepted values.
    This check can be applied to both a string attribute as well as a list attribute."""

    @property
    def check_type(self) -> str:
        return "accepted_values"

    def execute(
        self, attribute_path: str, value_list: List[Any], accepted_values: List[str]
    ) -> List[ValidationResult]:
        results = []
        for idx, value in enumerate(value_list):
            if value is None:
                continue

            if isinstance(value, str):
                value_list = [value]
            elif isinstance(value, list):
                value_list = value

            for value in values:
                value_str = str(value)
                passed = value_str in accepted_values

                if passed:
                    message = f"Attribute {attribute_path} value {value_str}"
                    "is in the list of accepted values"
                else:
                    message = (
                        f"Attribute '{attribute_path}' value {value_str} "
                        f"is not in the list of accepted values: '{accepted_values}'"
                    )

                results.append(
                    ValidationResult(
                        "", attribute_path, self.check_type, passed, message
                    )
                )

        return results


class MinItemsCheck(Check):
    """Check if list has minimum number of items"""

    @property
    def check_type(self) -> str:
        return "min_items"

    def execute(
        self, attribute_path: str, values: List[Any], min_count: int
    ) -> List[ValidationResult]:
        if not values:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    False,
                    f"Attribute '{attribute_path}' is missing, expected at least \
                          {min_count} items",
                )
            ]

        # Check if any value is a list and validate its length
        all_passed = True
        for value in values:
            if isinstance(value, list):
                if len(value) < min_count:
                    all_passed = False
                    break
            else:
                # If it's not a list but we expect min_items, that's a failure
                all_passed = False
                break

        passed = all_passed and len(values) > 0

        if passed:
            message = f"Attribute '{attribute_path}' has at least {min_count} items"
        else:
            message = f"Attribute '{attribute_path}' has fewer than {min_count} items"

        return [ValidationResult("", attribute_path, self.check_type, passed, message)]


class MaxItemsCheck(Check):
    """Check if list does not exceed maximum number of items"""

    @property
    def check_type(self) -> str:
        return "max_items"

    def execute(
        self, attribute_path: str, values: List[Any], max_count: int
    ) -> List[ValidationResult]:
        if not values:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    True,
                    f"Attribute '{attribute_path}' is missing \
                        (max_items check skipped)",
                )
            ]

        all_passed = True
        for value in values:
            if isinstance(value, list):
                if len(value) > max_count:
                    all_passed = False
                    break

        passed = all_passed

        if passed:
            message = f"Attribute '{attribute_path}' has at most {max_count} items"
        else:
            message = f"Attribute '{attribute_path}' has more than {max_count} items"

        return [ValidationResult("", attribute_path, self.check_type, passed, message)]


class CheckRegistry:
    """Registry for all available check types"""

    def __init__(self) -> None:
        self._checks: Dict[str, Check] = {}
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register all default check types"""
        default_checks = [
            RequiredCheck(),
            PatternCheck(),
            AcceptedValuesCheck(),
            MinItemsCheck(),
            MaxItemsCheck(),
        ]

        for check in default_checks:
            self.register(check)

    def register(self, check: Check) -> None:
        """Register a new check type"""
        self._checks[check.check_type] = check

    def get(self, check_type: str) -> Check:
        """Get a check by type"""
        if check_type not in self._checks:
            raise ValueError(f"Unknown check type: {check_type}")
        return self._checks[check_type]

    def list_available(self) -> List[str]:
        """List all available check types"""
        return list(self._checks.keys())


class DataContractValidator:
    """Validates data contract YAML files against defined checks"""

    def __init__(
        self, checks_file: str, check_registry: Optional[CheckRegistry] = None
    ) -> None:
        """
        Initialize validator with checks configuration

        Args:
            checks_file: Path to the checks YAML file
            check_registry: Optional custom CheckRegistry instance
        """
        with open(checks_file, "r") as f:
            self.checks_config = yaml.safe_load(f)

        self.registry = check_registry or CheckRegistry()

    def run_checks(self, data_contract: Contract) -> ContractValidationReport:
        """
        Run checks on a single data contract

        Args:
            data_contract: Contract object representing the data contract

        Returns:
            ContractValidationReport with results
        """

        results = []

        for check_group in self.checks_config["data_contract_checks"]:
            attribute_path = check_group["attribute"]
            checks = check_group["checks"]

            # Get the value(s) at the specified attribute path
            values = self._get_attribute_values(
                data_contract.contract_content, attribute_path
            )

            # Run all checks for this attribute
            for check_config in checks:
                check_type = next(iter(check_config.keys()))
                check_value = check_config[check_type]

                # Get the appropriate check handler from registry
                check_handler = self.registry.get(check_type)

                # Execute the check
                check_results = check_handler.execute(
                    attribute_path, values, check_value
                )

                # Add contract file to each result
                for result in check_results:
                    result.contract_file = data_contract.contract_path

                results.extend(check_results)

        # Create report
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        return ContractValidationReport(
            contract_file=data_contract.contract_path,
            total_checks=len(results),
            passed_checks=passed,
            failed_checks=failed,
            results=results,
        )

    def validate(
        self, data_contracts: List[Contract]
    ) -> List[ContractValidationReport]:
        """
        Validate multiple data contract YAML files

        Args:
            data_contracts: List of Contract objects

        Returns:
            List of ContractValidationReport objects
        """
        reports = []

        for contract in data_contracts:
            try:
                report = self.run_checks(contract)
                reports.append(report)
            except Exception as e:
                # Create a failed report for files that can't be processed
                error_result = ValidationResult(
                    contract_file=contract.contract_path,
                    attribute="file",
                    check_type="validation",
                    passed=False,
                    message=f"Error processing file: {e!s}",
                )
                reports.append(
                    ContractValidationReport(
                        contract_file=contract.contract_path,
                        total_checks=1,
                        passed_checks=0,
                        failed_checks=1,
                        results=[error_result],
                    )
                )

        return reports

    def _get_attribute_values(self, data: Dict, attribute_path: str) -> List[Any]:
        """
        Extract values from nested data structure based on attribute path

        Args:
            data: The data dictionary
            attribute_path: Dot-separated attribute path (e.g., 'models.fields.unique')
                Supports wildcard '*' to match all items (e.g., 'models.*.fields')

        Returns:
            List of values found at the attribute path
        """
        parts = attribute_path.split(".")
        return self._traverse_path(data, parts, [])

    def _traverse_path(
        self,
        data: Any,  # noqa: ANN401
        parts: List[str],
        current_path: List[str],
    ) -> List[Any]:
        """
        Recursively traverse the data structure following the field path

        Args:
            data: Current data node
            parts: Remaining parts of the field path
            current_path: Current traversed path for context

        Returns:
            List of values found
        """
        if not parts:
            return [data] if data is not None else []

        current_part = parts[0]
        remaining_parts = parts[1:]

        if data is None:
            return []

        # Handle dictionary
        if isinstance(data, dict):
            if current_part in data:
                return self._traverse_path(
                    data[current_part], remaining_parts, [*current_path, current_part]
                )
            else:
                return []

        # Handle list - traverse all items
        elif isinstance(data, list):
            results = []
            for item in data:
                results.extend(self._traverse_path(item, parts, current_path))
            return results

        return []

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
                    f"{status} {report.contract_file}: \
                      {report.passed_checks}/{report.total_checks} checks passed"
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
                f"   Checks: {report.passed_checks} passed, \
                  {report.failed_checks} failed"
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
            print(f" FAILURES BY TYPE: {failures_by_type}")

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
                f"  • {attribute}: {len(failures)} failure(s) across \
                  {len(contracts)} contract(s)"
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
