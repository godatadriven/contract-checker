"""Shared pytest fixtures for the contract-checker test suite."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_root_path() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def custom_fixtures_path(fixtures_root_path: Path) -> Path:
    return fixtures_root_path / "custom"


@pytest.fixture
def dcs_fixtures_path(fixtures_root_path: Path) -> Path:
    return fixtures_root_path / "dcs"


@pytest.fixture
def odcs_fixtures_path(fixtures_root_path: Path) -> Path:
    return fixtures_root_path / "odcs"


@pytest.fixture
def custom_schema_path(custom_fixtures_path: Path) -> Path:
    return custom_fixtures_path / "ecommerce-product-schema.json"


@pytest.fixture
def custom_checks_config_path() -> Path:
    return Path(__file__).parent.parent / "custom-checks-config.yml"
