"""Unit tests for glob-based contract path filtering."""

from pathlib import Path

import pytest

from contract_checker.utils.contract_utils import parse_data_contracts_path_config
from contract_checker.utils.path_filter import filter_contract_paths, glob_to_regex

BASE = Path("/repo/contracts")

PATHS = [
    BASE / "domain/orders.yaml",
    BASE / "domain/customers/profile.yaml",
    BASE / "source/crm.yml",
    BASE / "marts/finance/revenue.yaml",
    BASE / "marts/kpis.yaml",
    BASE / "staging/domain/temp.yaml",
]


def rel(paths: list[Path]) -> set[str]:
    return {p.relative_to(BASE).as_posix() for p in paths}


class TestGlobToRegex:
    def test_literal_pattern_matches_only_itself(self) -> None:
        r = glob_to_regex("domain/contract_a.yml")
        assert r.match("domain/contract_a.yml")
        assert not r.match("domain/contract_aXyml")  # '.' must not be a wildcard
        assert not r.match("domain/contract_a.yml.bak")  # anchored at the end

    def test_single_star_does_not_cross_segments(self) -> None:
        r = glob_to_regex("domain/*.yaml")
        assert r.match("domain/orders.yaml")
        assert not r.match("domain/customers/profile.yaml")

    def test_double_star_crosses_segments(self) -> None:
        r = glob_to_regex("marts/**")
        assert r.match("marts/kpis.yaml")
        assert r.match("marts/finance/revenue.yaml")
        assert not r.match("staging/marts/x.yaml")  # anchored at the start

    def test_leading_double_star_matches_any_depth_including_root(self) -> None:
        r = glob_to_regex("**/domain/**")
        assert r.match("staging/domain/temp.yaml")
        assert r.match("domain/orders.yaml")

    def test_mid_double_star_allows_zero_directories(self) -> None:
        r = glob_to_regex("domain/**/draft.yaml")
        assert r.match("domain/draft.yaml")
        assert r.match("domain/a/b/draft.yaml")

    def test_leading_slash_is_stripped(self) -> None:
        assert glob_to_regex("/marts/**").match("marts/kpis.yaml")

    def test_bare_directory_pattern_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="did you mean 'domain/\\*\\*'"):
            glob_to_regex("domain/")


class TestFilterContractPaths:
    def test_no_filters_includes_everything(self) -> None:
        assert filter_contract_paths(PATHS, BASE, [], []) == PATHS

    def test_include_only(self) -> None:
        out = filter_contract_paths(PATHS, BASE, ["domain/**", "source/**"], [])
        assert rel(out) == {"domain/orders.yaml", "domain/customers/profile.yaml", "source/crm.yml"}

    def test_exclude_only(self) -> None:
        out = filter_contract_paths(PATHS, BASE, [], ["marts/**"])
        assert "marts/kpis.yaml" not in rel(out)
        assert "domain/orders.yaml" in rel(out)

    def test_exclude_wins_over_include(self) -> None:
        out = filter_contract_paths(PATHS, BASE, ["domain/**"], ["domain/**"])
        assert out == []

    def test_exact_file_pin(self) -> None:
        out = filter_contract_paths(PATHS, BASE, ["domain/orders.yaml"], [])
        assert rel(out) == {"domain/orders.yaml"}


class TestParseDataContractsPathConfig:
    def test_missing_block(self) -> None:
        assert parse_data_contracts_path_config({}) == (None, [], [])

    def test_string_form(self) -> None:
        path, inc, exc = parse_data_contracts_path_config({"data_contracts_path": "./contracts/"})
        assert path == Path("./contracts/")
        assert inc == [] and exc == []

    def test_mapping_form(self) -> None:
        cfg = {"data_contracts_path": {"path": "./c/", "include_paths": ["domain/**"], "exclude_paths": ["marts/**"]}}
        path, inc, exc = parse_data_contracts_path_config(cfg)
        assert path == Path("./c/")
        assert inc == ["domain/**"] and exc == ["marts/**"]

    def test_custom_filters_ignored(self) -> None:
        cfg = {"data_contracts_path": {"path": "./c/", "include_custom": [{"field": "x", "value": 1}]}}
        path, inc, exc = parse_data_contracts_path_config(cfg)
        assert (path, inc, exc) == (Path("./c/"), [], [])
