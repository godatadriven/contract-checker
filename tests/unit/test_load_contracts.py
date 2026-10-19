"""Unit tests for load_contracts: per-file failures are reported, not skipped or fatal."""

from __future__ import annotations

from pathlib import Path

import pytest

from contract_checker.utils.contract_utils import LoadedContracts, load_contracts

GOOD_DCS = "dataContractSpecification: 1.1.0\ninfo:\n  title: Orders\n"


def _write(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body)
    return path


class TestConfigurationErrorsRaise:
    """Problems that make the whole run meaningless raise before any file is read."""

    def test_missing_specification_raises_with_config_hint(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="data_contract_specification must be one of: dcs, odcs"):
            load_contracts(tmp_path, contract_specification=None)

    def test_unknown_specification_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="got 'nope'"):
            load_contracts(tmp_path, contract_specification="nope")

    def test_custom_without_schema_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="no custom schema was provided"):
            load_contracts(tmp_path, contract_specification="custom")

    def test_missing_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_contracts(tmp_path / "nope", contract_specification="dcs")


class TestDiscovery:
    """Only regular *.yaml / *.yml files are candidates; nothing found is an empty result, not an error."""

    def test_empty_directory_loads_nothing(self, tmp_path: Path) -> None:
        loaded = load_contracts(tmp_path, contract_specification="dcs")
        assert loaded.contracts == []
        assert loaded.failed_reports == []

    def test_filters_excluding_everything_load_nothing(self, tmp_path: Path) -> None:
        _write(tmp_path, "a.yaml", GOOD_DCS)
        _write(tmp_path, "b.yml", GOOD_DCS)
        loaded = load_contracts(tmp_path, contract_specification="dcs", include_paths=["nothing/**"])
        assert loaded.contracts == []
        assert loaded.failed_reports == []

    def test_directory_named_like_a_contract_is_ignored(self, tmp_path: Path) -> None:
        _write(tmp_path, "orders.yaml", GOOD_DCS)
        (tmp_path / "archive.yaml").mkdir()
        loaded = load_contracts(tmp_path, contract_specification="dcs")
        assert [c.contract_path.name for c in loaded.contracts] == ["orders.yaml"]
        assert loaded.failed_reports == []


class TestPerFileFailuresAreReported:
    """A single bad file becomes a failed report; the other files still load."""

    def test_good_file_loads(self, tmp_path: Path) -> None:
        _write(tmp_path, "orders.yaml", GOOD_DCS)
        loaded = load_contracts(tmp_path, contract_specification="dcs")
        assert isinstance(loaded, LoadedContracts)
        assert [c.contract_specification_version for c in loaded.contracts] == ["1.1.0"]
        assert loaded.failed_reports == []

    @pytest.mark.parametrize(
        ("body", "expected_message"),
        [
            ("info: [not, closed\n", "is not valid YAML"),
            ("", "is empty"),
            ("- just\n- a list\n", "must contain a mapping at the top level, got list"),
            ("info:\n  title: Orders\n", "missing the 'dataContractSpecification' key"),
            ("dataContractSpecification: 9.9.9\ninfo:\n  title: Orders\n", "version '9.9.9' is not supported"),
        ],
        ids=["broken-yaml", "empty", "list-root", "missing-version-key", "unsupported-version"],
    )
    def test_bad_file_becomes_failed_report(self, tmp_path: Path, body: str, expected_message: str) -> None:
        bad = _write(tmp_path, "bad.yaml", body)
        loaded = load_contracts(tmp_path, contract_specification="dcs")

        assert loaded.contracts == []
        assert len(loaded.failed_reports) == 1
        report = loaded.failed_reports[0]
        assert report.contract_file == str(bad)
        assert report.success is False
        assert (report.total_checks, report.passed_checks, report.failed_checks) == (1, 0, 1)
        assert report.results[0].check_type == "load"
        assert report.results[0].attribute == "file"
        assert expected_message in report.results[0].message

    def test_dcs_version_with_v_prefix_is_unsupported(self, tmp_path: Path) -> None:
        _write(tmp_path, "a.yaml", "dataContractSpecification: v1.1.0\ninfo:\n  title: Orders\n")
        loaded = load_contracts(tmp_path, contract_specification="dcs")
        assert loaded.contracts == []
        assert len(loaded.failed_reports) == 1
        assert "version 'v1.1.0' is not supported" in loaded.failed_reports[0].results[0].message

    def test_unsupported_version_message_has_no_pydantic_noise(self, tmp_path: Path) -> None:
        _write(tmp_path, "bad.yaml", "dataContractSpecification: 9.9.9\n")
        message = load_contracts(tmp_path, contract_specification="dcs").failed_reports[0].results[0].message
        assert message == "Contract specification 'dcs' version '9.9.9' is not supported."

    def test_bad_file_does_not_stop_the_others(self, tmp_path: Path) -> None:
        _write(tmp_path, "a_good.yaml", GOOD_DCS)
        _write(tmp_path, "b_bad.yaml", "info: [broken\n")
        _write(tmp_path, "c_good.yaml", GOOD_DCS)
        loaded = load_contracts(tmp_path, contract_specification="dcs")

        assert [c.contract_path.name for c in loaded.contracts] == ["a_good.yaml", "c_good.yaml"]
        assert [Path(r.contract_file).name for r in loaded.failed_reports] == ["b_bad.yaml"]

    def test_odcs_missing_api_version_names_the_key(self, tmp_path: Path) -> None:
        _write(tmp_path, "bad.yaml", "kind: DataContract\n")
        loaded = load_contracts(tmp_path, contract_specification="odcs")
        assert "missing the 'apiVersion' key" in loaded.failed_reports[0].results[0].message


class TestCustomSchema:
    """With a custom schema the specification is 'custom' and the version is never checked."""

    def test_custom_schema_ignores_specification_and_version(self, tmp_path: Path) -> None:
        _write(tmp_path, "any.yaml", "info:\n  title: anything\n")
        schema = _write(tmp_path, "schema.json", "{}")
        loaded = load_contracts(tmp_path / "any.yaml", contract_specification=None, custom_schema_path=schema)
        assert loaded.failed_reports == []
        contract = loaded.contracts[0]
        assert (contract.contract_specification, contract.contract_specification_version) == ("custom", "custom")
