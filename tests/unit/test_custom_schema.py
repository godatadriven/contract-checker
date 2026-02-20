"""Tests for the custom schema validation feature."""

import tempfile
from pathlib import Path

import pytest

from contract_checker.checks.validator import DataContractValidator
from contract_checker.contract.contract_base import Contract
from contract_checker.utils.contract_utils import load_contracts


class TestCustomSchemaValidation:
    """Unit tests for DataContractValidator._validate_against_custom_schema()."""

    @pytest.fixture
    def valid_contract(
        self, custom_fixtures_path: Path, custom_schema_path: Path
    ) -> Contract:
        return Contract(
            contract_path=custom_fixtures_path / "valid-ecommerce-contract.yaml",
            contract_content=_load_yaml(
                custom_fixtures_path / "valid-ecommerce-contract.yaml"
            ),
            contract_specification="custom",
            contract_specification_version="custom",
            custom_schema_path=custom_schema_path,
        )

    @pytest.fixture
    def invalid_contract(
        self, custom_fixtures_path: Path, custom_schema_path: Path
    ) -> Contract:
        return Contract(
            contract_path=custom_fixtures_path / "invalid-ecommerce-contract.yaml",
            contract_content=_load_yaml(
                custom_fixtures_path / "invalid-ecommerce-contract.yaml"
            ),
            contract_specification="custom",
            contract_specification_version="custom",
            custom_schema_path=custom_schema_path,
        )

    @pytest.fixture
    def validator(self, custom_checks_config_path: Path) -> DataContractValidator:
        return DataContractValidator(str(custom_checks_config_path))

    def test_valid_contract_passes(
        self, validator: DataContractValidator, valid_contract: Contract
    ) -> None:
        results = validator._validate_against_custom_schema(valid_contract)
        assert len(results) == 1
        assert results[0].passed is True
        assert "validates against" in results[0].message

    def test_invalid_contract_fails(
        self, validator: DataContractValidator, invalid_contract: Contract
    ) -> None:
        results = validator._validate_against_custom_schema(invalid_contract)
        assert all(r.passed is False for r in results)

    def test_invalid_contract_produces_multiple_errors(
        self, validator: DataContractValidator, invalid_contract: Contract
    ) -> None:
        results = validator._validate_against_custom_schema(invalid_contract)
        assert len(results) >= 6

    def test_required_field_missing_produces_error(
        self, validator: DataContractValidator, invalid_contract: Contract
    ) -> None:
        results = validator._validate_against_custom_schema(invalid_contract)
        messages = [r.message for r in results]
        assert any("required" in m.lower() or "required" in m for m in messages)

    def test_pattern_violation_produces_error(
        self, validator: DataContractValidator, invalid_contract: Contract
    ) -> None:
        results = validator._validate_against_custom_schema(invalid_contract)
        contract_id_errors = [r for r in results if r.attribute == "contract_id"]
        assert len(contract_id_errors) >= 1

    def test_enum_violation_produces_error(
        self, validator: DataContractValidator, invalid_contract: Contract
    ) -> None:
        results = validator._validate_against_custom_schema(invalid_contract)
        assert any(
            "unknown" in r.message
            or "is not valid" in r.message
            or "not one of" in r.message.lower()
            for r in results
        )

    def test_nested_field_error_path(
        self, validator: DataContractValidator, invalid_contract: Contract
    ) -> None:
        results = validator._validate_against_custom_schema(invalid_contract)
        non_root_results = [r for r in results if r.attribute != "root"]
        assert len(non_root_results) >= 1

    def test_missing_schema_file_returns_error_result(
        self, custom_fixtures_path: Path, custom_checks_config_path: Path
    ) -> None:
        contract = Contract(
            contract_path=custom_fixtures_path / "valid-ecommerce-contract.yaml",
            contract_content=_load_yaml(
                custom_fixtures_path / "valid-ecommerce-contract.yaml"
            ),
            contract_specification="custom",
            contract_specification_version="custom",
            custom_schema_path=Path("/nonexistent/schema.json"),
        )
        validator = DataContractValidator(str(custom_checks_config_path))
        results = validator._validate_against_custom_schema(contract)
        assert len(results) == 1
        assert results[0].passed is False

    def test_invalid_json_schema_returns_error_result(
        self, custom_fixtures_path: Path, custom_checks_config_path: Path
    ) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{ this is not valid json }")
            bad_schema_path = Path(f.name)

        try:
            contract = Contract(
                contract_path=custom_fixtures_path / "valid-ecommerce-contract.yaml",
                contract_content=_load_yaml(
                    custom_fixtures_path / "valid-ecommerce-contract.yaml"
                ),
                contract_specification="custom",
                contract_specification_version="custom",
                custom_schema_path=bad_schema_path,
            )
            validator = DataContractValidator(str(custom_checks_config_path))
            results = validator._validate_against_custom_schema(contract)
            assert len(results) == 1
            assert results[0].passed is False
        finally:
            bad_schema_path.unlink(missing_ok=True)

    def test_all_results_have_check_type_json_schema(
        self, validator: DataContractValidator, invalid_contract: Contract
    ) -> None:
        results = validator._validate_against_custom_schema(invalid_contract)
        assert all(r.check_type == "json_schema" for r in results)


class TestCustomSchemaContractLoading:
    """Tests for load_contracts() with a custom schema path."""

    def test_load_single_contract_with_custom_schema(
        self, custom_fixtures_path: Path, custom_schema_path: Path
    ) -> None:
        contracts = load_contracts(
            contract_path=custom_fixtures_path / "valid-ecommerce-contract.yaml",
            contract_specification="custom",
            custom_schema_path=custom_schema_path,
        )
        assert len(contracts) == 1

    def test_load_directory_with_custom_schema(
        self, custom_fixtures_path: Path, custom_schema_path: Path
    ) -> None:
        contracts = load_contracts(
            contract_path=custom_fixtures_path,
            contract_specification="custom",
            custom_schema_path=custom_schema_path,
        )
        yaml_files = list(custom_fixtures_path.rglob("*.yaml"))
        assert len(contracts) == len(yaml_files)

    def test_specification_set_to_custom(
        self, custom_fixtures_path: Path, custom_schema_path: Path
    ) -> None:
        contracts = load_contracts(
            contract_path=custom_fixtures_path / "valid-ecommerce-contract.yaml",
            contract_specification="custom",
            custom_schema_path=custom_schema_path,
        )
        assert contracts[0].contract_specification == "custom"

    def test_version_set_to_custom(
        self, custom_fixtures_path: Path, custom_schema_path: Path
    ) -> None:
        contracts = load_contracts(
            contract_path=custom_fixtures_path / "valid-ecommerce-contract.yaml",
            contract_specification="custom",
            custom_schema_path=custom_schema_path,
        )
        assert contracts[0].contract_specification_version == "custom"

    def test_custom_schema_path_attached_to_contract(
        self, custom_fixtures_path: Path, custom_schema_path: Path
    ) -> None:
        contracts = load_contracts(
            contract_path=custom_fixtures_path,
            contract_specification="custom",
            custom_schema_path=custom_schema_path,
        )
        assert all(c.custom_schema_path == custom_schema_path for c in contracts)


class TestCustomSchemaReport:
    """End-to-end tests via DataContractValidator.validate()."""

    @pytest.fixture
    def validator(self, custom_checks_config_path: Path) -> DataContractValidator:
        return DataContractValidator(str(custom_checks_config_path))

    @pytest.fixture
    def valid_contracts(
        self, custom_fixtures_path: Path, custom_schema_path: Path
    ) -> list:
        return load_contracts(
            contract_path=custom_fixtures_path / "valid-ecommerce-contract.yaml",
            contract_specification="custom",
            custom_schema_path=custom_schema_path,
        )

    @pytest.fixture
    def invalid_contracts(
        self, custom_fixtures_path: Path, custom_schema_path: Path
    ) -> list:
        return load_contracts(
            contract_path=custom_fixtures_path / "invalid-ecommerce-contract.yaml",
            contract_specification="custom",
            custom_schema_path=custom_schema_path,
        )

    def test_valid_contract_report_success(
        self, validator: DataContractValidator, valid_contracts: list
    ) -> None:
        reports = validator.validate(valid_contracts)
        assert len(reports) == 1
        assert reports[0].success is True
        assert reports[0].failed_checks == 0

    def test_invalid_contract_report_failure(
        self, validator: DataContractValidator, invalid_contracts: list
    ) -> None:
        reports = validator.validate(invalid_contracts)
        assert len(reports) == 1
        assert reports[0].success is False
        assert reports[0].failed_checks > 0

    def test_valid_contract_report_counts(
        self, validator: DataContractValidator, valid_contracts: list
    ) -> None:
        reports = validator.validate(valid_contracts)
        report = reports[0]
        assert report.total_checks == 1
        assert report.passed_checks == 1

    def test_invalid_contract_report_counts(
        self, validator: DataContractValidator, invalid_contracts: list
    ) -> None:
        reports = validator.validate(invalid_contracts)
        report = reports[0]
        assert report.total_checks == report.passed_checks + report.failed_checks

    def test_report_contains_contract_file_path(
        self, validator: DataContractValidator, valid_contracts: list
    ) -> None:
        reports = validator.validate(valid_contracts)
        report = reports[0]
        assert report.contract_file is not None
        assert all(r.contract_file is not None for r in report.results)


def _load_yaml(path: Path) -> dict:
    """Helper to load a YAML file into a dict."""
    import yaml

    with open(path, "r") as f:
        return yaml.safe_load(f)
