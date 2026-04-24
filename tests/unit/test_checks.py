"""Unit tests for individual check classes."""

from __future__ import annotations

from contract_checker.checks.validators import (
    AcceptedValuesCheck,
    AtLeastOneCheck,
    MaxItemsCheck,
    MinItemsCheck,
    PatternCheck,
    RequiredCheck,
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
        results = self.check.execute("test.field", ["ACC12345688"], pattern)

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


class TestAcceptedValuesCheck:
    """Test AcceptedValuesCheck functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.check = AcceptedValuesCheck()

    def test_accepted_values_check_string_passes(self) -> None:
        """Test accepted values check passes when string is in accepted list."""
        results = self.check.execute("test.field", ["active"], ["active", "inactive"])

        assert len(results) == 1
        assert results[0].passed is True
        assert "is in the list of accepted values" in results[0].message

    def test_accepted_values_check_string_fails(self) -> None:
        """Test accepted values check fails when string is not in accepted list."""
        results = self.check.execute("test.field", ["unknown"], ["active", "inactive"])

        assert len(results) == 1
        assert results[0].passed is False
        assert "is not in the list of accepted values" in results[0].message

    def test_accepted_values_check_list_all_pass(self) -> None:
        """Test accepted values check passes when all list items are accepted."""
        results = self.check.execute("test.field", [["active", "inactive"]], ["active", "inactive", "pending"])

        assert len(results) == 2
        assert all(r.passed is True for r in results)

    def test_accepted_values_check_list_partial_fail(self) -> None:
        """Test accepted values check returns mixed results when some list items are not accepted."""
        results = self.check.execute("test.field", [["active", "unknown"]], ["active", "inactive"])

        assert len(results) == 2
        assert results[0].passed is True
        assert results[1].passed is False

    def test_accepted_values_check_none_skipped(self) -> None:
        """Test accepted values check skips None values."""
        results = self.check.execute("test.field", [None], ["active", "inactive"])

        assert len(results) == 0


class TestAtLeastOneCheck:
    """Test AtLeastOneCheck functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.check = AtLeastOneCheck()

    def test_dict_check_passes(self) -> None:
        """Test dict check passes when at least one item has the required attribute."""
        fields = {"order_id": {"unique": True, "type": "text"}, "name": {"type": "text"}}
        results = self.check.execute("models.orders.fields", [fields], {"unique": True})

        assert len(results) == 1
        assert results[0].passed is True
        assert "at least one item" in results[0].message

    def test_dict_check_fails(self) -> None:
        """Test dict check fails when no item has the required attribute."""
        fields = {"order_id": {"type": "text"}, "name": {"type": "text"}}
        results = self.check.execute("models.orders.fields", [fields], {"unique": True})

        assert len(results) == 1
        assert results[0].passed is False
        assert "no items" in results[0].message

    def test_dict_check_empty_collection(self) -> None:
        """Test dict check fails when the collection is empty."""
        results = self.check.execute("models.orders.fields", [{}], {"unique": True})

        assert len(results) == 1
        assert results[0].passed is False

    def test_missing_attribute(self) -> None:
        """Test check fails when the attribute is missing entirely."""
        results = self.check.execute("models.orders.fields", [], {"unique": True})

        assert len(results) == 1
        assert results[0].passed is False
        assert "missing" in results[0].message

    def test_scalar_check_passes(self) -> None:
        """Test scalar check passes when at least one value matches."""
        results = self.check.execute("test.field", [False, True], True)

        assert len(results) == 1
        assert results[0].passed is True

    def test_scalar_check_fails(self) -> None:
        """Test scalar check fails when no value matches."""
        results = self.check.execute("test.field", [False, False], True)

        assert len(results) == 1
        assert results[0].passed is False
