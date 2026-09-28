"""Unit tests for the Contract model."""

from __future__ import annotations

from pathlib import Path

import pytest

from contract_checker.contract.contract_base import Contract


class TestContractVersionValidation:
    """Tests for Contract.validate_version."""

    def test_schema_directory_is_independent_of_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Supported versions must resolve even when run outside the repo root."""
        monkeypatch.chdir(tmp_path)

        contract = Contract(
            contract_path=Path("contract.yaml"),
            contract_content={},
            contract_specification="odcs",
            contract_specification_version="3.1.0",
        )

        assert contract.contract_specification_version == "3.1.0"

    def test_unsupported_version_message_names_spec_and_version(self) -> None:
        """The error must say which spec and which version is unsupported."""
        with pytest.raises(ValueError, match=r"specification 'odcs' version '9\.9\.9' is not supported"):
            Contract(
                contract_path=Path("contract.yaml"),
                contract_content={},
                contract_specification="odcs",
                contract_specification_version="9.9.9",
            )
