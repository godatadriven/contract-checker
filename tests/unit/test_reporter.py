"""Unit tests for ValidationReporter."""

from __future__ import annotations

import io

from rich.console import Console

from contract_checker.checks.models import ContractValidationReport, ValidationResult
from contract_checker.checks.reporting import ValidationReporter, display_path, github_annotations


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


class TestDisplayPath:
    """Test contract path display."""

    def test_relative_path_is_kept_relative(self) -> None:
        """A repo-relative path stays as-is (normalized)."""
        assert display_path("contracts/sales/datacontract.yaml") == "contracts/sales/datacontract.yaml"

    def test_absolute_path_under_cwd_becomes_relative(self, tmp_path: object) -> None:
        """An absolute path below the working directory is shown relative to it."""
        import os

        absolute = os.path.join(os.getcwd(), "contracts", "datacontract.yaml")
        assert display_path(absolute) == os.path.join("contracts", "datacontract.yaml")


class TestSameNamedContracts:
    """Contracts sharing a filename in different folders must stay distinguishable."""

    def test_report_shows_folder_for_same_named_files(self) -> None:
        """Both directory names appear in the printed report."""
        reporter = ValidationReporter()
        reporter.console = Console(file=io.StringIO(), width=200)
        reports = [
            _make_report("contracts/sales/datacontract.yaml", [_make_result(False)]),
            _make_report("contracts/marketing/datacontract.yaml", [_make_result(False)]),
        ]

        reporter.print_results(reports)

        output = reporter.console.file.getvalue()  # type: ignore[union-attr]
        assert "sales" in output
        assert "marketing" in output


class TestScoreboard:
    """Test the summary-mode scoreboard."""

    def _print(self, reports: list[ContractValidationReport]) -> str:
        buffer = io.StringIO()
        reporter = ValidationReporter()
        reporter.console = Console(file=buffer, width=200)
        reporter.print_results(reports, output_mode="summary")
        return buffer.getvalue()

    def test_failing_contracts_listed_before_passing(self) -> None:
        """Failing contracts come first; passing ones still appear."""
        reports = [
            _make_report("a_passing.yml", [_make_result(True)]),
            _make_report("b_failing.yml", [_make_result(False)]),
        ]

        output = self._print(reports)

        assert output.index("b_failing.yml") < output.index("a_passing.yml")

    def test_failed_check_types_shown_without_messages(self) -> None:
        """Failing lines carry the failed check types, deduplicated, no messages."""
        results = [
            ValidationResult("a.yml", "some.attribute", "required", False, "distinctive-failure-message"),
            ValidationResult("a.yml", "other.attribute", "required", False, "distinctive-failure-message"),
            ValidationResult("a.yml", "third.attribute", "pattern", False, "distinctive-failure-message"),
        ]
        reports = [_make_report("a.yml", results)]

        output = self._print(reports)

        assert "pattern, required" in output
        assert "distinctive-failure-message" not in output

    def test_counts_are_explicit_about_failed_vs_passed(self) -> None:
        """Row counts say 'N/M failed' or 'N/M passed', never a bare ratio."""
        reports = [
            _make_report("bad.yml", [_make_result(False), _make_result(False), _make_result(True)]),
            _make_report("good.yml", [_make_result(True), _make_result(True)]),
        ]

        output = self._print(reports)

        assert "2/3 failed" in output
        assert "2/2 passed" in output

    def test_all_passing_still_shows_scoreboard(self) -> None:
        """Even a fully green run lists the contracts that were checked."""
        reports = [_make_report("a.yml", [_make_result(True)])]

        output = self._print(reports)

        assert "a.yml" in output
        assert "1/1 passed" in output


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
