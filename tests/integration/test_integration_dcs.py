"""Integration tests for DCS (Data Contract Specification) contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from contract_checker.checks.base_check import DataContractValidator
from contract_checker.utils.contract_utils import load_contracts


class TestDCSContractsIntegration:
    """Integration tests using DCS fixture contracts."""

    @pytest.fixture
    def dcs_fixtures_path(self) -> Path:
        """Return path to DCS fixtures."""
        return Path("tests/fixtures/dcs")

    @pytest.fixture
    def dcs_checks_config(self, tmp_path: Path) -> str:
        """Create a checks configuration for DCS contracts."""
        checks_content = """
data_contract_standard: dcs
data_contract_checks:
  - attribute: dataContractSpecification
    checks:
      - required: true
      - pattern: '^[0-9]+\\.[0-9]+\\.[0-9]+$'
  - attribute: id
    checks:
      - required: true
  - attribute: info.title
    checks:
      - required: true
  - attribute: info.version
    checks:
      - required: false
  - attribute: models
    checks:
      - required: true
"""
        checks_file = tmp_path / "dcs_checks.yaml"
        checks_file.write_text(checks_content)
        return str(checks_file)

    def test_covid_cases_contract(
        self, dcs_fixtures_path: Path, dcs_checks_config: str
    ) -> None:
        """Test validation of covid_cases.yaml contract."""
        contract_path = dcs_fixtures_path / "0.9.3" / "covid_cases.yaml"

        if not contract_path.exists():
            pytest.skip(f"Fixture not found: {contract_path}")

        contracts = load_contracts(contract_path, "dcs")
        assert len(contracts) == 1, "Should load exactly one contract"

        # Verify contract loaded correctly
        contract = contracts[0]
        assert contract.contract_content["id"] == "covid_cases"
        assert "models" in contract.contract_content
        assert "covid_cases" in contract.contract_content["models"]

        # Run validation
        validator = DataContractValidator(dcs_checks_config)
        reports = validator.validate(contracts)

        assert len(reports) == 1
        report = reports[0]

        # Basic structure checks should pass
        assert report.total_checks > 0

        # Check specific validations
        id_checks = [r for r in report.results if r.attribute == "id"]
        assert len(id_checks) > 0
        assert all(r.passed for r in id_checks), "ID checks should pass"

        title_checks = [r for r in report.results if r.attribute == "info.title"]
        assert len(title_checks) > 0
        assert all(r.passed for r in title_checks), "Title checks should pass"

    def test_orders_latest_contract_v120(
        self, dcs_fixtures_path: Path, dcs_checks_config: str
    ) -> None:
        """Test validation of orders-latest.yaml contract from version 1.2.0."""
        contract_path = dcs_fixtures_path / "1.2.0" / "orders-latest.yaml"

        if not contract_path.exists():
            pytest.skip(f"Fixture not found: {contract_path}")

        contracts = load_contracts(contract_path, "dcs")
        assert len(contracts) == 1

        # Verify contract loaded correctly
        contract = contracts[0]
        assert contract.contract_specification_version == "1.2.0"

        # Run validation
        validator = DataContractValidator(dcs_checks_config)
        reports = validator.validate(contracts)

        assert len(reports) == 1
        assert reports[0].total_checks > 0

    def test_all_dcs_contracts(
        self, dcs_fixtures_path: Path, dcs_checks_config: str
    ) -> None:
        """Test validation of all DCS contracts across all versions."""
        if not dcs_fixtures_path.exists():
            pytest.skip(f"DCS fixtures directory not found: {dcs_fixtures_path}")

        # Load all contracts recursively
        contracts = load_contracts(dcs_fixtures_path, "dcs")

        if len(contracts) == 0:
            pytest.skip("No DCS contracts found in fixtures")

        print(f"\nLoaded {len(contracts)} DCS contracts")

        # Verify we loaded contracts from different versions
        versions = set(c.contract_specification_version for c in contracts)
        print(f"Versions found: {versions}")

        # Run validation
        validator = DataContractValidator(dcs_checks_config)
        reports = validator.validate(contracts)

        assert len(reports) == len(contracts)
        assert all(isinstance(r.contract_file, Path) for r in reports)

        # Get summary
        summary = validator.get_summary(reports)
        assert summary["total_contracts"] == len(contracts)
        assert summary["total_checks"] > 0

        print(f"Total checks: {summary['total_checks']}")
        print(f"Passed: {summary['passed_checks']}, Failed: {summary['failed_checks']}")

    def test_dcs_version_093_contracts(
        self, dcs_fixtures_path: Path, dcs_checks_config: str
    ) -> None:
        """Test all DCS 0.9.3 contracts."""
        version_path = dcs_fixtures_path / "0.9.3"

        if not version_path.exists():
            pytest.skip(f"Version directory not found: {version_path}")

        contracts = load_contracts(version_path, "dcs")

        if len(contracts) == 0:
            pytest.skip("No DCS 0.9.3 contracts found")

        print(f"\nLoaded {len(contracts)} contracts from version 0.9.3")

        # Verify contract IDs
        contract_ids = [c.contract_content.get("id") for c in contracts]
        print(f"Contract IDs: {contract_ids}")

        # Run validation
        validator = DataContractValidator(dcs_checks_config)
        reports = validator.validate(contracts)

        assert len(reports) == len(contracts)

        # All should be version 0.9.3
        assert all(c.contract_specification_version == "0.9.3" for c in contracts)

    def test_dcs_version_120_contracts(
        self, dcs_fixtures_path: Path, dcs_checks_config: str
    ) -> None:
        """Test all DCS 1.2.0 contracts."""
        version_path = dcs_fixtures_path / "1.2.0"

        if not version_path.exists():
            pytest.skip(f"Version directory not found: {version_path}")

        contracts = load_contracts(version_path, "dcs")

        if len(contracts) == 0:
            pytest.skip("No DCS 1.2.0 contracts found")

        print(f"\nLoaded {len(contracts)} contracts from version 1.2.0")

        # Run validation
        validator = DataContractValidator(dcs_checks_config)
        reports = validator.validate(contracts)

        assert len(reports) == len(contracts)

        # All should be version 1.2.0
        assert all(c.contract_specification_version == "1.2.0" for c in contracts)

    def test_dcs_version_121_contracts(
        self, dcs_fixtures_path: Path, dcs_checks_config: str
    ) -> None:
        """Test all DCS 1.2.1 contracts."""
        version_path = dcs_fixtures_path / "1.2.1"

        if not version_path.exists():
            pytest.skip(f"Version directory not found: {version_path}")

        contracts = load_contracts(version_path, "dcs")

        if len(contracts) == 0:
            pytest.skip("No DCS 1.2.1 contracts found")

        print(f"\nLoaded {len(contracts)} contracts from version 1.2.1")

        # Run validation
        validator = DataContractValidator(dcs_checks_config)
        reports = validator.validate(contracts)

        assert len(reports) == len(contracts)

        # All should be version 1.2.1
        assert all(c.contract_specification_version == "1.2.1" for c in contracts)


class TestDCSErrorHandling:
    """Test error handling with DCS contracts."""

    @pytest.fixture
    def dcs_fixtures_path(self) -> Path:
        """Return path to DCS fixtures."""
        return Path("tests/fixtures/dcs")

    def test_missing_required_field_validation(
        self, dcs_fixtures_path: Path, tmp_path: Path
    ) -> None:
        """Test validation catches missing required fields."""
        contract_path = dcs_fixtures_path / "0.9.3" / "covid_cases.yaml"

        if not contract_path.exists():
            pytest.skip(f"Fixture not found: {contract_path}")

        # Check for a field that doesn't exist
        checks_content = """
data_contract_standard: dcs
data_contract_checks:
  - attribute: nonexistent.field
    checks:
      - required: true
"""
        checks_file = tmp_path / "missing_field_checks.yaml"
        checks_file.write_text(checks_content)

        contracts = load_contracts(contract_path, "dcs")
        validator = DataContractValidator(str(checks_file))
        report = validator.run_checks(contracts[0])

        # Should have failures for missing fields
        assert report.failed_checks > 0
        assert not report.success
