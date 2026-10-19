"""Unit tests for contract specification/version parsing helpers."""

from __future__ import annotations

import pytest

from contract_checker.utils.contract_utils import (
    get_specification_version,
    parse_specification_from_contract,
)


class TestGetSpecificationVersion:
    """Test version extraction and normalisation per standard."""

    def test_dcs_returns_bare_semver(self) -> None:
        content = {"dataContractSpecification": "1.2.1"}
        assert get_specification_version(content, "dcs") == "1.2.1"

    def test_odcs_strips_v_prefix(self) -> None:
        """ODCS `apiVersion: vX.Y.Z` must map to the bare-semver schema folder."""
        content = {"apiVersion": "v3.0.2"}
        assert get_specification_version(content, "odcs") == "3.0.2"

    def test_odcs_without_prefix_is_unchanged(self) -> None:
        content = {"apiVersion": "3.1.0"}
        assert get_specification_version(content, "odcs") == "3.1.0"

    def test_custom_returns_custom(self) -> None:
        assert get_specification_version({}, "custom") == "custom"

    def test_unknown_standard_raises(self) -> None:
        with pytest.raises(ValueError):
            get_specification_version({"apiVersion": "v3.0.2"}, "unknown")


class TestParseSpecificationFromContract:
    """Test parse_specification_from_contract normalises the ODCS version too."""

    def test_odcs_strips_v_prefix(self) -> None:
        version, spec = parse_specification_from_contract({"apiVersion": "v3.0.2"}, {"data_contract_standard": "odcs"})
        assert (version, spec) == ("3.0.2", "odcs")

    def test_dcs_passthrough(self) -> None:
        version, spec = parse_specification_from_contract(
            {"dataContractSpecification": "1.2.1"}, {"data_contract_standard": "dcs"}
        )
        assert (version, spec) == ("1.2.1", "dcs")

    def test_unknown_standard_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported data_contract_specification 'nope'"):
            parse_specification_from_contract({"apiVersion": "v3.0.2"}, {"data_contract_standard": "nope"})
