"""Integration tests for loading and version-resolving real contract files."""

from __future__ import annotations

from pathlib import Path

from contract_checker.utils.contract_utils import load_contracts


class TestLoadOdcsContract:
    """End-to-end: a `vX.Y.Z` ODCS contract must resolve to a supported schema."""

    def test_v_prefixed_odcs_contract_is_supported(self, odcs_fixtures_path: Path) -> None:
        """Regression: `apiVersion: v3.0.2` must not raise "version not supported".

        The version is normalised to bare semver (`3.0.2`) so it matches the
        vendored schema folder. Before the fix this raised a ValueError.
        """
        contract_file = odcs_fixtures_path / "3.0.2" / "basic-four-dpo.odcs.yaml"

        contracts = load_contracts(contract_file, contract_specification="odcs").contracts

        assert len(contracts) == 1
        assert contracts[0].contract_specification == "odcs"
        assert contracts[0].contract_specification_version == "3.0.2"
