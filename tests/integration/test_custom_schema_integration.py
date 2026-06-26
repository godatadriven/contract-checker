"""Integration tests for custom JSON Schema validation.

These exercise the full custom-schema path: loading a contract, attaching a
custom schema, and running it through DataContractValidator.run_checks.
"""

from __future__ import annotations

from pathlib import Path

from contract_checker.checks.validator import DataContractValidator
from contract_checker.contract.contract_base import Contract
from contract_checker.utils.utils import parse_yml_to_dict

CUSTOM_FIXTURES = Path(__file__).parent.parent / "fixtures" / "custom"
SCHEMA = CUSTOM_FIXTURES / "ecommerce-product-schema.json"


def _load_contract(contract_file: Path) -> Contract:
    """Build a Contract in custom-schema mode from a fixture file."""
    return Contract(
        contract_path=str(contract_file),
        contract_content=parse_yml_to_dict(contract_file),
        contract_specification="custom",
        contract_specification_version="custom",
        custom_schema_path=SCHEMA,
    )


def test_valid_contract_passes_custom_schema() -> None:
    """A conforming contract reports no failures against the custom schema."""
    contract = _load_contract(CUSTOM_FIXTURES / "valid-ecommerce-contract.yaml")
    report = DataContractValidator({"data_contract_checks": []}).run_checks(contract)

    assert report.failed_checks == 0
    assert all(r.check_type == "json_schema" for r in report.results)


def test_invalid_contract_fails_custom_schema() -> None:
    """A non-conforming contract reports schema failures."""
    contract = _load_contract(CUSTOM_FIXTURES / "invalid-ecommerce-contract.yaml")
    report = DataContractValidator({"data_contract_checks": []}).run_checks(contract)

    assert report.failed_checks > 0
    assert all(r.check_type == "json_schema" for r in report.results)
