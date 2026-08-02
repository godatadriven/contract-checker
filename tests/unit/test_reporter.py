"""Unit tests for ValidationReporter."""

from __future__ import annotations

from contract_checker.checks.models import ContractValidationReport, ValidationResult
from contract_checker.checks.reporting import ValidationReporter, github_annotations


def _make_result(passed: bool, check_type: str = "required") -> ValidationResult:
    """Helper to build a ValidationResult."""
    return ValidationResult(
        contract_file="some_contract.yml",
        attribute="some.attribute",
        check_type=check_type,
        passed=passed,
        message="ok" if passed else "failed",
    )


def _make_report(contract_file: str, results: list[ValidationResult]) -> ContractValidationReport:
    """Helper to build a ContractValidationReport from a list of results."""
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    return ContractValidationReport(
        contract_file=contract_file,
        total_checks=len(results),
        passed_checks=passed,
        failed_checks=failed,
        results=results,
    )


class TestValidationReporter:
    """Test ValidationReporter.get_summary() aggregation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.reporter = ValidationReporter()

    def test_get_summary_all_pass(self) -> None:
        """Test summary with two reports where all checks pass."""
        report_a = _make_report("a.yml", [_make_result(True), _make_result(True)])
        report_b = _make_report("b.yml", [_make_result(True)])

        summary = self.reporter.get_summary([report_a, report_b])

        assert summary["total_contracts"] == 2
        assert summary["passed_contracts"] == 2
        assert summary["failed_contracts"] == 0
        assert summary["total_checks"] == 3
        assert summary["passed_checks"] == 3
        assert summary["failed_checks"] == 0

    def test_get_summary_with_failures(self) -> None:
        """Test summary with one passing and one failing report."""
        passing_report = _make_report("pass.yml", [_make_result(True), _make_result(True)])
        failing_report = _make_report("fail.yml", [_make_result(True), _make_result(False), _make_result(False)])

        summary = self.reporter.get_summary([passing_report, failing_report])

        assert summary["total_contracts"] == 2
        assert summary["failed_contracts"] == 1
        assert summary["passed_contracts"] == 1
        assert summary["total_checks"] == 5
        assert summary["passed_checks"] == 3
        assert summary["failed_checks"] == 2

    def test_get_summary_empty(self) -> None:
        """Test summary with an empty list of reports."""
        summary = self.reporter.get_summary([])

        assert summary["total_contracts"] == 0
        assert summary["passed_contracts"] == 0
        assert summary["failed_contracts"] == 0
        assert summary["total_checks"] == 0
        assert summary["passed_checks"] == 0
        assert summary["failed_checks"] == 0

    def test_get_summary_includes_per_check_results(self) -> None:
        """Each contract entry carries its individual check results."""
        report = _make_report("a.yml", [_make_result(True), _make_result(False)])

        summary = self.reporter.get_summary([report])

        contract = summary["contracts"][0]
        assert contract["file"] == "a.yml"
        assert len(contract["results"]) == 2
        failed = [r for r in contract["results"] if not r["passed"]]
        assert failed[0]["check_type"] == "required"
        assert failed[0]["attribute"] == "some.attribute"
        assert failed[0]["message"] == "failed"


class TestGithubAnnotations:
    """Test GitHub Actions workflow-command generation."""

    def test_one_line_per_failed_check(self) -> None:
        """Only failed checks produce annotation lines."""
        report = _make_report("a.yml", [_make_result(True), _make_result(False), _make_result(False)])

        lines = github_annotations([report])

        assert len(lines) == 2
        assert all(line.startswith("::error file=") for line in lines)
        assert all("title=required" in line for line in lines)
        assert all(line.endswith("::failed") for line in lines)

    def test_no_failures_no_lines(self) -> None:
        """A fully passing report yields no annotations."""
        report = _make_report("a.yml", [_make_result(True)])
        assert github_annotations([report]) == []

    def test_message_newlines_are_escaped(self) -> None:
        """Newlines in messages are escaped so annotations stay one line."""
        result = ValidationResult(
            contract_file="a.yml",
            attribute="x",
            check_type="pattern",
            passed=False,
            message="line one\nline two",
        )
        report = _make_report("a.yml", [result])

        lines = github_annotations([report])

        assert len(lines) == 1
        assert "\n" not in lines[0]
        assert "line one%0Aline two" in lines[0]
