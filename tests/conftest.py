"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest

if TYPE_CHECKING:
    pass


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def fixtures_root_path() -> Path:
    """Return the root fixtures directory."""
    fixtures_path = Path(__file__).parent / "fixtures"
    print(f"THE PATH IS {fixtures_path}")
    return fixtures_path


@pytest.fixture
def dcs_fixtures_path(fixtures_root_path: Path) -> Path:
    """Return the DCS fixtures directory."""
    return fixtures_root_path / "dcs"


@pytest.fixture
def odcs_fixtures_path(fixtures_root_path: Path) -> Path:
    """Return the ODCS fixtures directory."""
    return fixtures_root_path / "odcs"
