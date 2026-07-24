"""Integration tests for custom JSON Schema validation.

These exercise the full custom-schema path: loading a contract, attaching a
custom schema, and running it through DataContractValidator.run_checks. They
also cover an "extended standard" schema that layers in-house rules on top of
the built-in ODCS schema, and the fact that attribute-level
``data_contract_checks`` compose with (rather than replace) a custom schema.
"""

from __future__ import annotations

from pathlib import Path

from contract_checker.checks.validator import DataContractValidator
from contract_checker.contract.contract_base import Contract
from contract_checker.utils.utils import parse_yml_to_dict

CUSTOM_FIXTURES = Path(__file__).parent.parent / "fixtures" / "custom"
ECOMMERCE_SCHEMA = CUSTOM_FIXTURES / "ecommerce-product-schema.json"
ODCS_EXTENDED_SCHEMA = CUSTOM_FIXTURES / "odcs-extended-schema.json"


def _load_contract(contract_file: Path, schema: Path) -> Contract:
    """Build a Contract in custom-schema mode from a fixture file."""
    return Contract(
        contract_path=str(contract_file),
        contract_content=parse_yml_to_dict(contract_file),
        contract_specification="custom",
        contract_specification_version="custom",
        custom_schema_path=schema,
    )


def test_valid_contract_passes_custom_schema() -> None:
    """A conforming contract reports no failures against the custom schema."""
    contract = _load_contract(CUSTOM_FIXTURES / "valid-ecommerce-contract.yaml", ECOMMERCE_SCHEMA)
    report = DataContractValidator({"data_contract_checks": []}).run_checks(contract)

    assert report.failed_checks == 0
    assert all(r.check_type == "json_schema" for r in report.results)


def test_invalid_contract_fails_custom_schema() -> None:
    """A non-conforming contract reports schema failures."""
    contract = _load_contract(CUSTOM_FIXTURES / "invalid-ecommerce-contract.yaml", ECOMMERCE_SCHEMA)
    report = DataContractValidator({"data_contract_checks": []}).run_checks(contract)

    assert report.failed_checks > 0
    assert all(r.check_type == "json_schema" for r in report.results)


def test_custom_schema_with_no_checks_config() -> None:
    """A custom schema validates even when the checks config is absent (None).

    This is the schema-only case driven entirely by --custom-schema-path with no
    (or an empty/unparseable) checks file, which must not crash.
    """
    contract = _load_contract(CUSTOM_FIXTURES / "valid-ecommerce-contract.yaml", ECOMMERCE_SCHEMA)
    report = DataContractValidator(None).run_checks(contract)  # type: ignore[arg-type]

    assert report.failed_checks == 0
    assert all(r.check_type == "json_schema" for r in report.results)


def test_custom_schema_and_attribute_checks_run_together() -> None:
    """A custom schema does not replace ``data_contract_checks``; both run.

    The contract passes the JSON Schema, but an attribute check on a value the
    schema does not constrain still fails — proving the checks run *in addition*
    to the schema validation.
    """
    contract = _load_contract(CUSTOM_FIXTURES / "valid-ecommerce-contract.yaml", ECOMMERCE_SCHEMA)
    checks_config = {
        "data_contract_checks": [
            {
                "attribute": "contract_id",
                "checks": [{"required": True}],
            },
            {
                # The schema accepts any semantic version; this check rejects it.
                "attribute": "version",
                "checks": [{"pattern": r"^9\."}],
            },
        ]
    }
    report = DataContractValidator(checks_config).run_checks(contract)

    check_types = {r.check_type for r in report.results}
    assert "json_schema" in check_types
    assert check_types - {"json_schema"}, "attribute-level checks should also run"
    # The JSON Schema passes, so every failure comes from the attribute checks.
    assert report.failed_checks > 0
    assert all(r.check_type != "json_schema" for r in report.results if not r.passed)


def test_valid_contract_passes_extended_odcs_schema() -> None:
    """A contract satisfying base ODCS and the in-house rules passes."""
    contract = _load_contract(CUSTOM_FIXTURES / "valid-odcs-extended-contract.yaml", ODCS_EXTENDED_SCHEMA)
    report = DataContractValidator({"data_contract_checks": []}).run_checks(contract)

    assert report.failed_checks == 0
    assert all(r.check_type == "json_schema" for r in report.results)


def test_invalid_contract_fails_extended_odcs_schema() -> None:
    """A contract that is valid ODCS but breaks the in-house rules fails."""
    contract = _load_contract(CUSTOM_FIXTURES / "invalid-odcs-extended-contract.yaml", ODCS_EXTENDED_SCHEMA)
    report = DataContractValidator({"data_contract_checks": []}).run_checks(contract)

    assert report.failed_checks > 0
    assert all(r.check_type == "json_schema" for r in report.results)
