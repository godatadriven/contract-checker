"""Unit tests for individual check classes."""

from __future__ import annotations

from typing import Any

import pytest

from contract_checker.checks.registry import CheckRegistry
from contract_checker.checks.validators import (
    AcceptedValuesCheck,
    AtLeastOneCheck,
    ExactlyOneCheck,
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
        """Required check fails when the field is completely absent from the contract.

        An empty values list means the attribute path wasn't found in the
        parsed data. The check should report a single failure with a
        "missing" message (distinct from null).
        """
        results = self.check.execute("test.field", [], True)

        assert len(results) == 1
        assert results[0].passed is False
        assert "is missing" in results[0].message

    def test_required_check_with_none_values(self) -> None:
        """Test required check fails when values contain None."""
        results = self.check.execute("test.field", [None, "value"], True)

        assert len(results) == 1
        assert results[0].passed is False
        assert "is null" in results[0].message

    def test_required_check_disabled(self) -> None:
        """required: false checks nothing, so it produces no results."""
        assert self.check.execute("test.field", [], False) == []
        assert self.check.execute("test.field", [None], False) == []
        assert self.check.execute("test.field", ["value"], False) == []

    def test_required_with_single_none_value(self) -> None:
        """A single None value should fail required with a 'null' message."""
        results = self.check.execute("test.field", [None], True)

        assert len(results) == 1
        assert results[0].passed is False
        assert "is null" in results[0].message

    def test_required_with_empty_string(self) -> None:
        """An empty string is still a present value."""
        results = self.check.execute("test.field", [""], True)

        assert len(results) == 1
        assert results[0].passed is True

    def test_required_with_zero(self) -> None:
        """Zero is a valid present value."""
        results = self.check.execute("test.field", [0], True)

        assert len(results) == 1
        assert results[0].passed is True

    def test_required_with_false(self) -> None:
        """Boolean False is a valid present value."""
        results = self.check.execute("test.field", [False], True)

        assert len(results) == 1
        assert results[0].passed is True

    def test_attribute_path_in_message(self) -> None:
        """The attribute path should appear in the result message."""
        results = self.check.execute("models.orders.fields.order_id.unique", ["val"], True)

        assert "models.orders.fields.order_id.unique" in results[0].message


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
        """A present-but-null value fails the pattern check."""
        pattern = r"^[A-Z]+$"
        results = self.check.execute("test.field", [None], pattern)

        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].message == "Attribute 'test.field' is null"

    def test_empty_values_no_results(self) -> None:
        """Empty values list produces no results."""
        results = self.check.execute("test.field", [], r"^.*$")

        assert len(results) == 0

    def test_non_string_value_coerced(self) -> None:
        """Non-string values are coerced via str() before matching."""
        results = self.check.execute("test.field", [123], r"^\d+$")

        assert len(results) == 1
        assert results[0].passed is True

    def test_semantic_version_pattern(self) -> None:
        """Test with a real-world semver pattern."""
        pattern = r"^\d+\.\d+\.\d+$"
        results = self.check.execute("info.version", ["1.0.0"], pattern)

        assert results[0].passed is True

    def test_semantic_version_pattern_fails(self) -> None:
        """Semver pattern rejects non-conforming values."""
        pattern = r"^\d+\.\d+\.\d+$"
        results = self.check.execute("info.version", ["v1.0"], pattern)

        assert results[0].passed is False

    def test_unanchored_pattern_accepts_partial_match(self) -> None:
        """Documents current behavior: unanchored patterns allow partial matches.

        PatternCheck uses re.match, which anchors at the start only. A pattern
        like r'\\d+' matches '123abc' because the prefix satisfies the regex.
        Callers must fully anchor their patterns (use ^...$) to enforce whole-
        string matching. If this surprises users in practice, switch the
        implementation to re.fullmatch.
        """
        results = self.check.execute("test.field", ["123abc"], r"\d+")

        assert len(results) == 1
        assert results[0].passed is True


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
        """An absent attribute is skipped: presence is required's job."""
        assert self.check.execute("test.field", [], 3) == []

    def test_min_items_check_null_value(self) -> None:
        """A present-but-null list fails."""
        results = self.check.execute("test.field", [None], 1)

        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].message == "Attribute 'test.field' is null"

    def test_min_items_check_null_elements_not_counted(self) -> None:
        """Null elements fail and do not count toward the minimum."""
        results = self.check.execute("test.field", [[None, None, None]], 1)

        assert [r.passed for r in results] == [False, False]
        assert "contains 3 null element(s)" in results[0].message
        assert "fewer than 1 items" in results[1].message

    def test_min_items_check_one_null_does_not_hide_other_lists(self) -> None:
        """A null value fails on its own; the other lists are still counted."""
        results = self.check.execute("test.field", [["a"], None, []], 1)

        assert [r.passed for r in results] == [False, False]
        assert "is null" in results[0].message
        assert "fewer than 1 items" in results[1].message

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
        """An absent attribute is skipped: presence is required's job."""
        assert self.check.execute("test.field", [], 5) == []

    def test_max_items_check_null_value(self) -> None:
        """A present-but-null list fails."""
        results = self.check.execute("test.field", [None], 5)

        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].message == "Attribute 'test.field' is null"

    def test_max_items_check_null_elements_not_counted(self) -> None:
        """Null elements fail and do not count toward the maximum."""
        results = self.check.execute("test.field", [["a", None, None]], 2)

        assert [r.passed for r in results] == [False, True]
        assert "contains 2 null element(s)" in results[0].message


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

    def test_accepted_values_check_none_fails(self) -> None:
        """A present-but-null value fails the accepted values check."""
        results = self.check.execute("test.field", [None], ["active", "inactive"])

        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].message == "Attribute 'test.field' is null"

    def test_accepted_values_check_missing_no_results(self) -> None:
        """An absent attribute is skipped: presence is required's job."""
        assert self.check.execute("test.field", [], ["active"]) == []


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
        """An absent collection is skipped: presence is required's job."""
        assert self.check.execute("models.orders.fields", [], {"unique": True}) == []

    def test_null_collection_fails(self) -> None:
        """A present-but-null collection fails with the null message, not '0 items'."""
        results = self.check.execute("models.orders.fields", [None], {"unique": True})

        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].message == "Attribute 'models.orders.fields' is null"

    def test_null_item_in_collection_fails(self) -> None:
        """A null item fails and is named; the verdict still uses the other items."""
        fields = {"id": None, "name": {"unique": True}}
        results = self.check.execute("models.orders.fields", [fields], {"unique": True})

        assert [r.passed for r in results] == [False, True]
        assert results[0].message == "Attribute 'models.orders.fields' contains 1 null element(s): id"

    def test_multi_key_check_value_rejected(self) -> None:
        """Multi-key check_value must fail with a clear message, not silently ignore extras."""
        fields = {"order_id": {"unique": True, "type": "text"}}
        results = self.check.execute("models.orders.fields", [fields], {"unique": True, "primaryKey": True})

        assert len(results) == 1
        assert results[0].passed is False
        assert "single-key" in results[0].message

    def test_empty_dict_check_value_rejected(self) -> None:
        """Empty dict check_value must fail, not raise StopIteration."""
        fields = {"order_id": {"unique": True}}
        results = self.check.execute("models.orders.fields", [fields], {})

        assert len(results) == 1
        assert results[0].passed is False
        assert "single-key" in results[0].message

    def test_non_dict_check_value_rejected(self) -> None:
        """Scalar / list / None check_value must fail with a clear message."""
        for bad_value in [True, "unique", ["unique"], None]:
            results = self.check.execute("models.orders.fields", [{"x": {}}], bad_value)

            assert len(results) == 1
            assert results[0].passed is False
            assert "single-key" in results[0].message

    def test_non_dict_items_in_collection(self) -> None:
        """Collection entries that are not dicts must not crash; they don't match."""
        fields = {"order_id": "not_a_dict", "name": {"unique": True}}
        results = self.check.execute("models.orders.fields", [fields], {"unique": True})

        assert len(results) == 1
        assert results[0].passed is True

        fields_none_match = {"order_id": "str", "name": 42}
        results = self.check.execute("models.orders.fields", [fields_none_match], {"unique": True})

        assert len(results) == 1
        assert results[0].passed is False

    def test_per_expansion_independence(self) -> None:
        """Each wildcard-expanded path gets its own verdict; results are not pooled.

        Simulates how the runner invokes the check once per expanded model.
        One passing and one failing collection must produce independent verdicts.
        """
        model_a_fields = {"id": {"unique": True}}
        model_b_fields = {"id": {"unique": False}}

        pass_results = self.check.execute("models.a.fields", [model_a_fields], {"unique": True})
        fail_results = self.check.execute("models.b.fields", [model_b_fields], {"unique": True})

        assert pass_results[0].passed is True
        assert fail_results[0].passed is False


class TestExactlyOneCheck:
    """Test ExactlyOneCheck functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.check = ExactlyOneCheck()

    def test_exactly_one_match_passes(self) -> None:
        """Passes when exactly one item in the collection matches."""
        fields = {
            "order_id": {"primaryKey": True, "type": "text"},
            "name": {"type": "text"},
            "created_at": {"type": "timestamp"},
        }
        results = self.check.execute("models.orders.fields", [fields], {"primaryKey": True})

        assert len(results) == 1
        assert results[0].passed is True
        assert "exactly one" in results[0].message

    def test_zero_matches_fails(self) -> None:
        """Fails with count 0 when no items match."""
        fields = {"order_id": {"type": "text"}, "name": {"type": "text"}}
        results = self.check.execute("models.orders.fields", [fields], {"primaryKey": True})

        assert len(results) == 1
        assert results[0].passed is False
        assert "0 items" in results[0].message
        assert "expected exactly 1" in results[0].message

    def test_two_matches_fails(self) -> None:
        """Fails with count 2 when two items match."""
        fields = {
            "order_id": {"primaryKey": True, "type": "text"},
            "customer_id": {"primaryKey": True, "type": "text"},
            "name": {"type": "text"},
        }
        results = self.check.execute("models.orders.fields", [fields], {"primaryKey": True})

        assert len(results) == 1
        assert results[0].passed is False
        assert "2 items" in results[0].message
        assert "expected exactly 1" in results[0].message

    def test_empty_collection_fails(self) -> None:
        """Fails when the collection is empty (0 matches)."""
        results = self.check.execute("models.orders.fields", [{}], {"primaryKey": True})

        assert len(results) == 1
        assert results[0].passed is False
        assert "0 items" in results[0].message

    def test_missing_attribute_skipped(self) -> None:
        """An absent collection is skipped: presence is required's job."""
        assert self.check.execute("models.orders.fields", [], {"primaryKey": True}) == []

    def test_null_collection_fails(self) -> None:
        """A present-but-null collection fails with the null message, not '0 items'."""
        results = self.check.execute("models.orders.fields", [None], {"primaryKey": True})

        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].message == "Attribute 'models.orders.fields' is null"

    def test_null_item_in_collection_fails(self) -> None:
        """A null item fails and is named; the verdict still uses the other items."""
        fields = {"id": None, "name": {"primaryKey": True}}
        results = self.check.execute("models.orders.fields", [fields], {"primaryKey": True})

        assert [r.passed for r in results] == [False, True]
        assert results[0].message == "Attribute 'models.orders.fields' contains 1 null element(s): id"

    def test_multi_key_check_value_rejected(self) -> None:
        """Multi-key mapping as check_value is rejected with a failing result."""
        fields = {"order_id": {"primaryKey": True, "unique": True}}
        results = self.check.execute("models.orders.fields", [fields], {"primaryKey": True, "unique": True})

        assert len(results) == 1
        assert results[0].passed is False
        assert "single-key mapping" in results[0].message
        assert "2 keys" in results[0].message

    def test_empty_dict_check_value_rejected(self) -> None:
        """Empty mapping as check_value is rejected with a failing result."""
        fields = {"order_id": {"primaryKey": True}}
        results = self.check.execute("models.orders.fields", [fields], {})

        assert len(results) == 1
        assert results[0].passed is False
        assert "single-key mapping" in results[0].message
        assert "0 keys" in results[0].message

    def test_non_mapping_check_value_rejected(self) -> None:
        """Non-mapping check_value values are rejected with a failing result."""
        fields = {"order_id": {"primaryKey": True}}

        for bad in [True, "primaryKey", ["primaryKey"], None, 1]:
            results = self.check.execute("models.orders.fields", [fields], bad)

            assert len(results) == 1
            assert results[0].passed is False, f"expected failure for check_value={bad!r}"
            assert "single-key mapping" in results[0].message

    def test_non_dict_items_in_collection_skipped(self) -> None:
        """Non-dict items inside the collection are not counted."""
        fields = {
            "order_id": {"primaryKey": True, "type": "text"},
            "stray_scalar": "not a mapping",
            "stray_list": [1, 2, 3],
        }
        results = self.check.execute("models.orders.fields", [fields], {"primaryKey": True})

        assert len(results) == 1
        assert results[0].passed is True
        assert "exactly one" in results[0].message


# A valid check_value for every registered check. Adding a check to the
# registry without adding it here fails test_every_check_is_covered, so every
# new check is held to the missing-vs-null rule below.
CHECK_VALUES: dict[str, Any] = {
    "required": True,
    "pattern": r"^x$",
    "accepted_values": ["x"],
    "min_items": 1,
    "max_items": 5,
    "at_least_one": {"key": True},
    "exactly_one": {"key": True},
}


class TestMissingVsNullRule:
    """Every check: absent is skipped (except required), present-but-null fails."""

    def test_every_check_is_covered(self) -> None:
        assert set(CheckRegistry().list_available()) == set(CHECK_VALUES)

    @pytest.mark.parametrize("check_type", sorted(set(CHECK_VALUES) - {"required"}))
    def test_absent_attribute_produces_no_results(self, check_type: str) -> None:
        check = CheckRegistry().get(check_type)
        assert check.execute("a.b", [], CHECK_VALUES[check_type]) == []

    def test_absent_attribute_fails_required(self) -> None:
        results = CheckRegistry().get("required").execute("a.b", [], True)
        assert [r.passed for r in results] == [False]
        assert "is missing" in results[0].message

    @pytest.mark.parametrize("check_type", sorted(CHECK_VALUES))
    def test_null_attribute_fails(self, check_type: str) -> None:
        check = CheckRegistry().get(check_type)
        results = check.execute("a.b", [None], CHECK_VALUES[check_type])

        assert len(results) == 1
        assert results[0].passed is False
        assert "is null" in results[0].message
