"""Integration tests for JSON Schema linting of standard (DCS/ODCS) contracts.

These exercise the ``lint`` toggle against the vendored standard schemas: a
conforming contract passes, a non-conforming one fails, and — crucially —
nothing is schema-checked unless linting is explicitly enabled.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from contract_checker.checks.validator import DataContractValidator, _to_json_compatible
from contract_checker.contract.contract_base import Contract
from contract_checker.utils.utils import parse_yml_to_dict, resolve_lint

FIXTURES = Path(__file__).parent.parent / "fixtures"
VALID_DCS = FIXTURES / "dcs" / "1.2.1" / "time_data_type_example.yaml"
INVALID_DCS = FIXTURES / "dcs" / "1.2.1" / "invalid_field_type.yaml"
VALID_ODCS = FIXTURES / "odcs" / "3.0.2" / "all" / "full-example.odcs.yaml"
# Contains an unquoted date (``- 2022-10-03``) that YAML parses into a ``date``.
UNQUOTED_DATE_ODCS = Path("fundamentals") / "table-column-description.odcs.yaml"


def _load_standard_contract(contract_file: Path, specification: str, version: str) -> Contract:
    """Build a Contract in standard-schema mode from a fixture file."""
    return Contract(
        contract_path=str(contract_file),
        contract_content=parse_yml_to_dict(contract_file),
        contract_specification=specification,
        contract_specification_version=version,
    )


def test_valid_dcs_contract_passes_standard_schema() -> None:
    """A conforming DCS contract reports no failures when linted."""
    contract = _load_standard_contract(VALID_DCS, "dcs", "1.2.1")
    report = DataContractValidator({"data_contract_checks": []}, lint=True).run_checks(contract)

    assert report.failed_checks == 0
    assert any(r.check_type == "json_schema" and r.passed for r in report.results)


def test_valid_odcs_contract_passes_standard_schema() -> None:
    """A conforming ODCS contract reports no failures when linted."""
    contract = _load_standard_contract(VALID_ODCS, "odcs", "3.0.2")
    report = DataContractValidator({"data_contract_checks": []}, lint=True).run_checks(contract)

    assert report.failed_checks == 0, [r.message for r in report.results if not r.passed]
    assert any(r.check_type == "json_schema" and r.passed for r in report.results)


@pytest.mark.parametrize("version", ["3.0.0", "3.1.0"])
def test_unquoted_yaml_date_passes_standard_schema(version: str) -> None:
    """Unquoted YAML dates are validated as strings, not rejected as ``date`` objects."""
    contract = _load_standard_contract(FIXTURES / "odcs" / version / UNQUOTED_DATE_ODCS, "odcs", version)
    assert isinstance(contract.contract_content["schema"][0]["properties"][0]["examples"][0], date)

    report = DataContractValidator({"data_contract_checks": []}, lint=True).run_checks(contract)

    assert report.failed_checks == 0, [r.message for r in report.results if not r.passed]


def test_to_json_compatible_renders_dates_as_iso_strings() -> None:
    """Dates and datetimes become ISO strings at any depth; other values are untouched."""
    content = {
        "a": date(2022, 10, 3),
        "b": [datetime(2022, 10, 3, 10, 0)],
        "c": {"n": 1, "flag": True, "s": "x", "none": None},
    }

    assert _to_json_compatible(content) == {
        "a": "2022-10-03",
        "b": ["2022-10-03T10:00:00"],
        "c": {"n": 1, "flag": True, "s": "x", "none": None},
    }


def test_invalid_dcs_contract_fails_standard_schema() -> None:
    """A DCS contract with an illegal field type fails when linted."""
    contract = _load_standard_contract(INVALID_DCS, "dcs", "1.2.1")
    report = DataContractValidator({"data_contract_checks": []}, lint=True).run_checks(contract)

    assert report.failed_checks > 0
    failures = [r for r in report.results if not r.passed]
    assert failures
    assert all(r.check_type == "json_schema" for r in failures)
    assert any("is not one of" in r.message for r in failures)


def test_standard_schema_not_checked_when_lint_disabled() -> None:
    """With linting off (the default), an invalid standard contract is not schema-checked."""
    contract = _load_standard_contract(INVALID_DCS, "dcs", "1.2.1")
    report = DataContractValidator({"data_contract_checks": []}).run_checks(contract)

    assert report.failed_checks == 0
    assert not any(r.check_type == "json_schema" for r in report.results)


def test_lint_from_config_enables_standard_schema_validation() -> None:
    """The 'lint' key in the checks config, resolved by resolve_lint, enables standard-schema validation."""
    checks_config = {"lint": True, "data_contract_checks": []}
    contract = _load_standard_contract(INVALID_DCS, "dcs", "1.2.1")
    report = DataContractValidator(checks_config, lint=resolve_lint(None, checks_config)).run_checks(contract)

    assert report.failed_checks > 0
    assert all(r.check_type == "json_schema" for r in report.results if not r.passed)
