"""Unit tests for individual check classes."""

from __future__ import annotations

from typing import Any

import pytest

from contract_checker.checks.base import Check
from contract_checker.checks.models import ValidationResult
from contract_checker.checks.registry import CheckRegistry
from contract_checker.checks.validator import DataContractValidator
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

    def test_pattern_check_list_value_all_match(self) -> None:
        """Test pattern check validates each item of a list attribute."""
        pattern = r"^[a-z]+$"
        results = self.check.execute("tags", [["abc", "def"]], pattern)

        assert len(results) == 2
        assert all(r.passed for r in results)
        assert "'abc'" in results[0].message
        assert "'def'" in results[1].message

    def test_pattern_check_list_value_partial_match(self) -> None:
        """Test pattern check fails only the list items that do not match."""
        pattern = r"^[a-z]+$"
        results = self.check.execute("tags", [["abc", "XYZ"]], pattern)

        assert len(results) == 2
        assert results[0].passed is True
        assert results[1].passed is False
        assert "'XYZ'" in results[1].message

    def test_pattern_check_list_value_not_matched_as_string(self) -> None:
        """Test a pattern matching the list's string form does not pass the check."""
        pattern = r"^\['abc'"
        results = self.check.execute("tags", [["abc", "XYZ"]], pattern)

        assert all(r.passed is False for r in results)

    def test_pattern_check_mixed_scalar_and_list_values(self) -> None:
        """Test pattern check handles scalars and lists found via wildcard paths."""
        pattern = r"^[a-z]+$"
        results = self.check.execute("models.*.tags", ["abc", ["def", "GHI"]], pattern)

        assert [r.passed for r in results] == [True, True, False]

    def test_pattern_check_list_with_none_item(self) -> None:
        """Test a null item inside a list fails the check."""
        pattern = r"^[a-z]+$"
        results = self.check.execute("tags", [["abc", None]], pattern)

        assert len(results) == 2
        assert results[0].passed is False
        assert "contains 1 null element(s)" in results[0].message
        assert results[1].passed is True

    def test_pattern_check_empty_list(self) -> None:
        """Test an empty list attribute produces no results."""
        results = self.check.execute("tags", [[]], r"^[a-z]+$")

        assert results == []


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

    def test_min_items_check_null_elements_not_counted(self) -> None:
        """Null elements fail and do not count toward the minimum."""
        results = self.check.execute("test.field", [[None, None, None]], 1)

        assert [r.passed for r in results] == [False, False]
        assert "contains 3 null element(s)" in results[0].message
        assert "fewer than 1 items" in results[1].message

    def test_min_items_check_non_list_value(self) -> None:
        """Test min items check with non-list value."""
        results = self.check.execute("test.field", ["not a list"], 3)

        assert len(results) == 1
        assert results[0].passed is False
        assert "is not a list" in results[0].message

    def test_min_items_check_mapping_counts_items(self) -> None:
        """Test min items check counts the entries of a mapping (e.g. DCS fields)."""
        fields = {"id": {"type": "int"}, "name": {"type": "text"}}

        assert self.check.execute("models.orders.fields", [fields], 2)[0].passed is True
        assert self.check.execute("models.orders.fields", [fields], 3)[0].passed is False

    def test_min_items_check_mapping_with_null_entry(self) -> None:
        """Test a null mapping entry is reported by key and not counted."""
        fields = {"id": {"type": "int"}, "name": None}
        results = self.check.execute("models.orders.fields", [fields], 2)

        assert len(results) == 2
        assert results[0].passed is False
        assert "contains 1 null element(s): name" in results[0].message
        assert results[1].passed is False

    def test_min_items_check_mixed_list_and_non_list(self) -> None:
        """Test min items check fails when any value is not a collection."""
        results = self.check.execute("test.field", [[1, 2, 3], 42], 1)

        assert len(results) == 1
        assert results[0].passed is False
        assert "is not a list" in results[0].message


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

    def test_max_items_check_null_elements_not_counted(self) -> None:
        """Null elements fail and do not count toward the maximum."""
        results = self.check.execute("test.field", [["a", None, None]], 2)

        assert [r.passed for r in results] == [False, True]
        assert "contains 2 null element(s)" in results[0].message

    def test_max_items_check_non_list_value(self) -> None:
        """Test max items check fails with non-list value, consistent with min_items."""
        results = self.check.execute("test.field", ["not a list"], 5)

        assert len(results) == 1
        assert results[0].passed is False
        assert "is not a list" in results[0].message

    def test_max_items_check_mapping_counts_items(self) -> None:
        """Test max items check counts the entries of a mapping (e.g. DCS fields)."""
        fields = {"id": {"type": "int"}, "name": {"type": "text"}}

        assert self.check.execute("models.orders.fields", [fields], 2)[0].passed is True
        assert self.check.execute("models.orders.fields", [fields], 1)[0].passed is False

    def test_max_items_check_mixed_list_and_non_list(self) -> None:
        """Test max items check fails when any value is not a collection."""
        results = self.check.execute("test.field", [[1], "not a list"], 5)

        assert len(results) == 1
        assert results[0].passed is False


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
        results = _validator()._run_check(check, "a.b", [None], CHECK_VALUES[check_type])

        assert len(results) == 1
        assert results[0].passed is False
        assert "is null" in results[0].message

    @pytest.mark.parametrize("check_type", sorted(set(CHECK_VALUES) - {"required"}))
    def test_null_attribute_uses_standard_message(self, check_type: str) -> None:
        check = CheckRegistry().get(check_type)
        results = _validator()._run_check(check, "a.b", [None], CHECK_VALUES[check_type])

        assert results[0].message == "Attribute 'a.b' is null"
        assert results[0].check_type == check_type

    def test_one_null_does_not_hide_other_values(self) -> None:
        """A null value fails on its own; the other values are still checked."""
        check = CheckRegistry().get("min_items")
        results = _validator()._run_check(check, "a.b", [["a"], None, []], 1)

        assert [r.passed for r in results] == [False, False]
        assert "is null" in results[0].message
        assert "fewer than 1 items" in results[1].message

    def test_required_false_ignores_null(self) -> None:
        """required: false stays a no-op, even for a null value."""
        check = CheckRegistry().get("required")
        assert _validator()._run_check(check, "a.b", [None], False) == []


class _LengthCheck(Check):
    """Custom check that, like many user checks, assumes values are not None."""

    @property
    def check_type(self) -> str:
        return "max_length"

    def execute(self, attribute_path: str, values: list[Any], check_value: int) -> list[ValidationResult]:
        return [ValidationResult("", attribute_path, self.check_type, len(v) <= check_value, "checked") for v in values]


class _FakeContract:
    """Lightweight stand-in for Contract to avoid on-disk schema validation."""

    def __init__(self, content: dict) -> None:
        self.contract_path = "test-contract.yaml"
        self.contract_content = content
        self.custom_schema_path = None


class TestCustomCheckNeverSeesNull:
    """Custom checks registered through CheckRegistry never receive a top-level None."""

    def _validate(self, content: dict, attribute: str) -> list[ValidationResult]:
        registry = CheckRegistry()
        registry.register(_LengthCheck())
        config = {"data_contract_checks": [{"attribute": attribute, "checks": [{"max_length": 5}]}]}
        validator = DataContractValidator(config, registry)
        contract: Any = _FakeContract(content)
        results: list[ValidationResult] = validator.validate([contract])[0].results
        return results

    def test_null_attribute(self) -> None:
        results = self._validate({"info": {"title": None}}, "info.title")

        assert [(r.check_type, r.passed, r.message) for r in results] == [
            ("max_length", False, "Attribute 'info.title' is null")
        ]

    def test_null_attribute_in_wildcard_path(self) -> None:
        content = {"models": {"a": {"name": None}, "b": {"name": "ok"}}}
        results = self._validate(content, "models.*.name")

        by_path = {r.attribute: (r.passed, r.message) for r in results}
        assert by_path == {
            "models.a.name": (False, "Attribute 'models.a.name' is null"),
            "models.b.name": (True, "checked"),
        }


def _validator() -> DataContractValidator:
    return DataContractValidator({"data_contract_checks": []})
