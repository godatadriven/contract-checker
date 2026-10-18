"""Unit tests for checks-config validation: config errors are raised once, up front."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from contract_checker.checks.registry import CheckRegistry
from contract_checker.checks.validator import ChecksConfigError, DataContractValidator, validate_checks_config


def _config(*checks: dict[str, Any], attribute: str = "info.title") -> dict:
    return {"data_contract_checks": [{"attribute": attribute, "checks": list(checks)}]}


class TestValidateChecksConfigShape:
    """The structure of data_contract_checks is validated before any check value."""

    def test_absent_or_empty_config_is_fine(self) -> None:
        validate_checks_config(None)
        validate_checks_config({})
        validate_checks_config({"data_contract_checks": None})
        validate_checks_config({"data_contract_checks": []})

    def test_valid_config_passes(self) -> None:
        validate_checks_config(_config({"required": True}, {"pattern": "^Orders"}, {"accepted_values": ["a"]}))

    def test_checks_block_must_be_a_list(self) -> None:
        with pytest.raises(ChecksConfigError, match="must be a list"):
            validate_checks_config({"data_contract_checks": {"attribute": "x"}})

    def test_entry_must_be_a_mapping(self) -> None:
        with pytest.raises(ChecksConfigError, match="entry 1 must be a mapping"):
            validate_checks_config({"data_contract_checks": ["info.title"]})

    def test_entry_needs_attribute(self) -> None:
        with pytest.raises(ChecksConfigError, match="entry 1 is missing a non-empty 'attribute'"):
            validate_checks_config({"data_contract_checks": [{"checks": [{"required": True}]}]})

    def test_entry_needs_checks_list(self) -> None:
        with pytest.raises(ChecksConfigError, match=r"entry 1 \('info.title'\) must have a 'checks' list"):
            validate_checks_config({"data_contract_checks": [{"attribute": "info.title", "checks": None}]})

    def test_multi_key_check_is_rejected_not_silently_truncated(self) -> None:
        with pytest.raises(ChecksConfigError, match="single-key mapping"):
            validate_checks_config(_config({"pattern": "^a", "required": True}))

    def test_unknown_check_type_names_the_entry_and_lists_available(self) -> None:
        with pytest.raises(ChecksConfigError, match=r"entry 1 \('info.title'\): unknown check type 'patern'") as exc:
            validate_checks_config(_config({"patern": "^a"}))
        assert "Available: required, pattern" in str(exc.value)

    def test_later_entry_is_numbered_correctly(self) -> None:
        config = {
            "data_contract_checks": [
                {"attribute": "info.title", "checks": [{"required": True}]},
                {"attribute": "info.version", "checks": [{"nope": 1}]},
            ]
        }
        with pytest.raises(ChecksConfigError, match=r"entry 2 \('info.version'\)"):
            validate_checks_config(config)

    def test_custom_registry_is_consulted(self) -> None:
        registry = CheckRegistry()
        with pytest.raises(ChecksConfigError, match="unknown check type 'required'"):
            validate_checks_config(_config({"required": True}), registry=_EmptyRegistry())
        validate_checks_config(_config({"required": True}), registry=registry)


class _EmptyRegistry(CheckRegistry):
    def _register_default_checks(self) -> None:
        pass


class TestBuiltinValidateConfig:
    """Each built-in check rejects values its execute() cannot handle."""

    @pytest.mark.parametrize(
        ("check", "message"),
        [
            ({"required": None}, r"'required' has no value \(did you mean 'required: true'\?\)"),
            ({"required": "yes"}, "'required' expects true or false"),
            ({"required": 1}, "'required' expects true or false"),
            ({"pattern": "^Orders("}, "'pattern' is not a valid regular expression"),
            ({"pattern": 123}, "'pattern' expects a regular expression string, got int"),
            ({"accepted_values": 1.0}, "'accepted_values' expects a non-empty list"),
            ({"accepted_values": []}, "'accepted_values' expects a non-empty list"),
            ({"accepted_values": {"a": 1}}, "'accepted_values' expects a non-empty list"),
            ({"accepted_values": None}, "'accepted_values' expects a non-empty list"),
            ({"min_items": "1"}, "'min_items' expects a non-negative integer"),
            ({"min_items": True}, "'min_items' expects a non-negative integer"),
            ({"min_items": -1}, "'min_items' expects a non-negative integer"),
            ({"max_items": 2.5}, "'max_items' expects a non-negative integer"),
            ({"at_least_one": True}, "'at_least_one' expects a single-key mapping"),
            ({"at_least_one": {}}, "'at_least_one' expects a single-key mapping"),
            ({"at_least_one": {"a": 1, "b": 2}}, "'at_least_one' expects a single-key mapping"),
            ({"exactly_one": "primaryKey"}, "'exactly_one' expects a single-key mapping"),
        ],
    )
    def test_rejected_values(self, check: dict[str, Any], message: str) -> None:
        with pytest.raises(ChecksConfigError, match=r"entry 1 \('info.title'\): " + message):
            validate_checks_config(_config(check))

    @pytest.mark.parametrize(
        "check",
        [
            {"required": True},
            {"required": False},
            {"pattern": r"^\d+\.\d+\.\d+$"},
            {"accepted_values": ["a", "b"]},
            {"accepted_values": "0.0.1"},  # single-value shorthand, as documented
            {"min_items": 0},
            {"max_items": 10},
            {"at_least_one": {"unique": True}},
            {"exactly_one": {"primaryKey": True}},
        ],
    )
    def test_accepted_values(self, check: dict[str, Any]) -> None:
        validate_checks_config(_config(check))


class _FakeContract:
    contract_path = "orders.yaml"
    custom_schema_path = None
    contract_content: ClassVar[dict] = {"info": {"title": "Orders"}}


class TestValidatorRunsConfigValidation:
    """validate() refuses a malformed config instead of blaming every contract."""

    def test_validate_raises_for_bad_config(self) -> None:
        v = DataContractValidator(_config({"pattern": "("}))
        with pytest.raises(ChecksConfigError, match="not a valid regular expression"):
            v.validate([_FakeContract()])  # type: ignore[list-item]

    def test_validate_with_good_config_still_reports_check_failures(self) -> None:
        v = DataContractValidator(_config({"pattern": "^Users"}))
        reports = v.validate([_FakeContract()])  # type: ignore[list-item]
        assert reports[0].failed_checks == 1
        assert "Error processing file" not in reports[0].results[0].message
