"""Unit tests for CheckRegistry."""

from __future__ import annotations

from typing import Any

import pytest

from contract_checker.checks.base import Check
from contract_checker.checks.models import ValidationResult
from contract_checker.checks.registry import CheckRegistry
from contract_checker.checks.validators import RequiredCheck


class _DummyCheck(Check):
    """Minimal Check subclass for testing custom registration."""

    @property
    def check_type(self) -> str:
        return "dummy"

    def execute(self, attribute_path: str, value_list: list[Any], check_value: Any) -> list[ValidationResult]:  # noqa: ANN401
        return []


class TestCheckRegistry:
    """Test CheckRegistry functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.registry = CheckRegistry()

    def test_default_registry_has_all_checks(self) -> None:
        """Test that the registry contains all 5 default check types on init."""
        available = self.registry.list_available()
        expected = {"required", "pattern", "accepted_values", "min_items", "max_items"}
        assert set(available) == expected

    def test_get_known_check_type(self) -> None:
        """Test that get() returns the correct check instance for a known type."""
        check = self.registry.get("required")
        assert isinstance(check, RequiredCheck)

    def test_get_unknown_check_type_raises(self) -> None:
        """Test that get() raises ValueError for an unknown check type."""
        with pytest.raises(ValueError, match="nonexistent"):
            self.registry.get("nonexistent")

    def test_register_custom_check(self) -> None:
        """Test that a custom Check subclass can be registered and retrieved."""
        dummy = _DummyCheck()
        self.registry.register(dummy)
        result = self.registry.get("dummy")
        assert isinstance(result, _DummyCheck)
