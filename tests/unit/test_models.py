"""Unit tests for ValidationResult and ContractValidationReport models."""

from __future__ import annotations

from contract_checker.checks.models import ContractValidationReport, ValidationResult


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_create_passing_result(self) -> None:
        """A passing result should store all fields correctly."""
        result = ValidationResult(
            contract_file="test.yaml",
            attribute="info.title",
            check_type="required",
            passed=True,
            message="Attribute 'info.title' is present",
        )

        assert result.contract_file == "test.yaml"
        assert result.attribute == "info.title"
        assert result.check_type == "required"
        assert result.passed is True
        assert "is present" in result.message

    def test_create_failing_result(self) -> None:
        """A failing result should store passed=False."""
        result = ValidationResult(
            contract_file="test.yaml",
            attribute="info.title",
            check_type="required",
            passed=False,
            message="Required attribute 'info.title' is missing",
        )

        assert result.passed is False

    def test_fields_are_mutable(self) -> None:
        """Dataclass fields should be mutable (used by validator to set contract_file)."""
        result = ValidationResult("", "attr", "required", True, "msg")
        result.contract_file = "updated.yaml"

        assert result.contract_file == "updated.yaml"


class TestContractValidationReport:
    """Test ContractValidationReport dataclass."""

    def test_success_when_no_failures(self) -> None:
        """Report should be successful when failed_checks is 0."""
        report = ContractValidationReport(
            contract_file="test.yaml",
            total_checks=3,
            passed_checks=3,
            failed_checks=0,
            results=[],
        )

        assert report.success is True

    def test_not_success_when_failures(self) -> None:
        """Report should not be successful when any checks fail."""
        report = ContractValidationReport(
            contract_file="test.yaml",
            total_checks=3,
            passed_checks=2,
            failed_checks=1,
            results=[],
        )

        assert report.success is False

    def test_success_with_zero_checks(self) -> None:
        """Report with zero checks should be successful (no failures)."""
        report = ContractValidationReport(
            contract_file="test.yaml",
            total_checks=0,
            passed_checks=0,
            failed_checks=0,
            results=[],
        )

        assert report.success is True

    def test_success_ignores_total_checks_invariant(self) -> None:
        """Documents current behavior: success only inspects failed_checks.

        The dataclass does NOT validate that
        total_checks == passed_checks + failed_checks. If the caller
        constructs an inconsistent report (e.g. totals that don't sum),
        `success` still returns True as long as `failed_checks == 0`.
        This test pins the current contract; add invariant validation
        to the dataclass if callers should be forced to keep counts
        consistent.
        """
        report = ContractValidationReport(
            contract_file="test.yaml",
            total_checks=10,
            passed_checks=3,
            failed_checks=0,
            results=[],
        )

        assert report.success is True

    def test_results_list_stored(self) -> None:
        """Report should store the full list of ValidationResult objects."""
        results = [
            ValidationResult("test.yaml", "info.title", "required", True, "pass"),
            ValidationResult("test.yaml", "info.version", "required", False, "fail"),
        ]
        report = ContractValidationReport(
            contract_file="test.yaml",
            total_checks=2,
            passed_checks=1,
            failed_checks=1,
            results=results,
        )

        assert len(report.results) == 2
        assert report.results[0].passed is True
        assert report.results[1].passed is False
