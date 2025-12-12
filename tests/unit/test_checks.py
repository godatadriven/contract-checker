"""Unit tests for individual check classes."""

from __future__ import annotations

from typing import Any

from contract_checker.checks.base_check import (
    MaxItemsCheck,
    MinItemsCheck,
    PatternCheck,
    RequiredCheck,
    SchemaExistenceCheck,
    ValidationResult,
)


class TestRequiredCheck:
    """Test RequiredCheck functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.check = RequiredCheck()

    def test_required_check_with_values(self) -> None:
        """Test required check passes when values are present."""
        results = self.check.execute("test.field", ["value1", "value2"], True)

        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].check_type == "required"
        assert "is present" in results[0].message

    def test_required_check_with_empty_values(self) -> None:
        """Test required check fails when no values present."""
        results = self.check.execute("test.field", [], True)

        assert len(results) == 1
        assert results[0].passed is False
        assert "missing or null" in results[0].message

    def test_required_check_with_none_values(self) -> None:
        """Test required check fails when values contain None."""
        results = self.check.execute("test.field", [None, "value"], True)

        assert len(results) == 1
        assert results[0].passed is False

    def test_required_check_disabled(self) -> None:
        """Test required check passes when disabled."""
        results = self.check.execute("test.field", [], False)

        assert len(results) == 1
        assert results[0].passed is True
        assert "optional" in results[0].message


class TestPatternCheck:
    """Test PatternCheck functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.check = PatternCheck()

    def test_pattern_check_matches(self) -> None:
        """Test pattern check passes with matching values."""
        pattern = r"^[A-Z]{3}[0-9]{8}$"
        results = self.check.execute("test.field", ["ACC12345678"], pattern)

        assert len(results) == 1
        assert results[0].passed is True
        assert "matches pattern" in results[0].message

    def test_pattern_check_fails(self) -> None:
        """Test pattern check fails with non-matching values."""
        pattern = r"^[A-Z]{3}[0-9]{8}$"
        results = self.check.execute("test.field", ["invalid"], pattern)

        assert len(results) == 1
        assert results[0].passed is False
        assert "does not match" in results[0].message

    def test_pattern_check_multiple_values(self) -> None:
        """Test pattern check with multiple values."""
        pattern = r"^[A-Z]{3}[0-9]{8}$"
        values = ["ACC12345678", "invalid", "DEF98765432"]
        results = self.check.execute("test.field", values, pattern)

        assert len(results) == 3
        assert results[0].passed is True
        assert results[1].passed is False
        assert results[2].passed is True

    def test_pattern_check_with_none(self) -> None:
        """Test pattern check with None value."""
        pattern = r"^[A-Z]+$"
        results = self.check.execute("test.field", [None], pattern)

        assert len(results) == 1
        assert results[0].passed is False
        assert "is null" in results[0].message


class TestMinItemsCheck:
    """Test MinItemsCheck functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.check = MinItemsCheck()

    def test_min_items_check_passes(self) -> None:
        """Test min items check passes with sufficient items."""
        results = self.check.execute("test.field", [[1, 2, 3, 4]], 3)

        assert len(results) == 1
        assert results[0].passed is True
        assert "at least 3 items" in results[0].message

    def test_min_items_check_fails(self) -> None:
        """Test min items check fails with insufficient items."""
        results = self.check.execute("test.field", [[1, 2]], 3)

        assert len(results) == 1
        assert results[0].passed is False
        assert "fewer than 3 items" in results[0].message

    def test_min_items_check_exact_count(self) -> None:
        """Test min items check with exact minimum count."""
        results = self.check.execute("test.field", [[1, 2, 3]], 3)

        assert len(results) == 1
        assert results[0].passed is True

    def test_min_items_check_missing_attribute(self) -> None:
        """Test min items check with missing attribute."""
        results = self.check.execute("test.field", [], 3)

        assert len(results) == 1
        assert results[0].passed is False
        assert "is missing" in results[0].message

    def test_min_items_check_non_list_value(self) -> None:
        """Test min items check with non-list value."""
        results = self.check.execute("test.field", ["not a list"], 3)

        assert len(results) == 1
        assert results[0].passed is False


class TestMaxItemsCheck:
    """Test MaxItemsCheck functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.check = MaxItemsCheck()

    def test_max_items_check_passes(self) -> None:
        """Test max items check passes with items under limit."""
        results = self.check.execute("test.field", [[1, 2, 3]], 5)

        assert len(results) == 1
        assert results[0].passed is True
        assert "at most 5 items" in results[0].message

    def test_max_items_check_fails(self) -> None:
        """Test max items check fails with items over limit."""
        results = self.check.execute("test.field", [[1, 2, 3, 4, 5, 6]], 5)

        assert len(results) == 1
        assert results[0].passed is False
        assert "more than 5 items" in results[0].message

    def test_max_items_check_exact_count(self) -> None:
        """Test max items check with exact maximum count."""
        results = self.check.execute("test.field", [[1, 2, 3, 4, 5]], 5)

        assert len(results) == 1
        assert results[0].passed is True

    def test_max_items_check_missing_attribute(self) -> None:
        """Test max items check with missing attribute."""
        results = self.check.execute("test.field", [], 5)

        assert len(results) == 1
        assert results[0].passed is True
        assert "skipped" in results[0].message


class TestSchemaExistenceCheck:
    """Test SchemaExistenceCheck functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "models": {
                    "type": "object",
                    "properties": {
                        "covid_cases": {
                            "type": "object",
                            "properties": {
                                "fields": {
                                    "type": "object",
                                    "properties": {
                                        "fips": {"type": "string"},
                                        "admin2": {"type": "string"},
                                    },
                                }
                            },
                        }
                    },
                },
                "quality": {
                    "type": "object",
                    "properties": {"type": {"type": "string"}},
                },
            },
        }
        self.check = SchemaExistenceCheck(self.schema)

    def test_schema_check_exists_simple_path(self) -> None:
        """Test schema check with existing simple path."""
        results = self.check.execute("quality.type", [], True)

        assert len(results) == 1
        assert results[0].passed is True
        assert "exists in the schema" in results[0].message

    def test_schema_check_exists_nested_path(self) -> None:
        """Test schema check with existing nested path."""
        results = self.check.execute("models.covid_cases.fields.fips", [], True)

        assert len(results) == 1
        assert results[0].passed is True

    def test_schema_check_does_not_exist(self) -> None:
        """Test schema check with non-existing path."""
        results = self.check.execute("models.nonexistent.field", [], True)

        assert len(results) == 1
        assert results[0].passed is False
        assert "does not exist" in results[0].message

    def test_schema_check_disabled(self) -> None:
        """Test schema check when disabled."""
        results = self.check.execute("any.path", [], False)

        assert len(results) == 1
        assert results[0].passed is True
        assert "disabled" in results[0].message

    def test_schema_check_with_array_wildcard(self) -> None:
        """Test schema check with array wildcard."""
        schema_with_array: dict[str, Any] = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                }
            },
        }
        check = SchemaExistenceCheck(schema_with_array)
        results = check.execute("items.*.name", [], True)

        assert len(results) == 1
        assert results[0].passed is True


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_creation(self) -> None:
        """Test creating a ValidationResult."""
        result = ValidationResult(
            contract_file="test.yaml",
            attribute="test.field",
            check_type="required",
            passed=True,
            message="Test passed",
        )

        assert result.contract_file == "test.yaml"
        assert result.attribute == "test.field"
        assert result.check_type == "required"
        assert result.passed is True
        assert result.message == "Test passed"
