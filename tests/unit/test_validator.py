"""Unit tests for DataContractValidator path traversal methods.

These test the internal methods in isolation without running the full
check pipeline. Integration tests for the full run_checks flow live
in tests/integration/.
"""

from __future__ import annotations

from contract_checker.checks.validator import DataContractValidator


# Helper to create a minimal validator (we only need the methods, not the config)
def _validator() -> DataContractValidator:
    return DataContractValidator({"data_contract_checks": []})


# ===================================================================
# _get_attribute_values / _traverse_path (non-wildcard paths)
# ===================================================================


class TestGetAttributeValues:
    """Test _get_attribute_values for non-wildcard dot-separated paths."""

    def setup_method(self) -> None:
        self.v = _validator()

    def test_simple_top_level_key(self) -> None:
        """Single-segment path returns the top-level value."""
        data = {"title": "Orders"}
        assert self.v._get_attribute_values(data, "title") == ["Orders"]

    def test_nested_path(self) -> None:
        """Multi-segment path traverses nested dicts."""
        data = {"info": {"title": "Orders", "version": "1.0.0"}}
        assert self.v._get_attribute_values(data, "info.title") == ["Orders"]
        assert self.v._get_attribute_values(data, "info.version") == ["1.0.0"]

    def test_deeply_nested_path(self) -> None:
        """Three-level deep path."""
        data = {"a": {"b": {"c": 42}}}
        assert self.v._get_attribute_values(data, "a.b.c") == [42]

    def test_missing_key_returns_empty(self) -> None:
        """A path that doesn't exist returns an empty list."""
        data = {"info": {"title": "Orders"}}
        assert self.v._get_attribute_values(data, "info.missing") == []

    def test_missing_intermediate_key_returns_empty(self) -> None:
        """If an intermediate key is missing, returns empty."""
        data = {"info": {"title": "Orders"}}
        assert self.v._get_attribute_values(data, "info.nonexistent.deep") == []

    def test_none_value_returns_empty(self) -> None:
        """Explicitly None leaf returns empty (filtered by _traverse_path)."""
        data = {"info": {"title": None}}
        assert self.v._get_attribute_values(data, "info.title") == []

    def test_boolean_value(self) -> None:
        """Boolean values are returned as-is."""
        data = {"field": {"unique": True}}
        assert self.v._get_attribute_values(data, "field.unique") == [True]

    def test_false_value(self) -> None:
        """Boolean False is a valid value (not filtered out)."""
        data = {"field": {"unique": False}}
        assert self.v._get_attribute_values(data, "field.unique") == [False]

    def test_integer_value(self) -> None:
        """Integer values are returned as-is."""
        data = {"field": {"count": 0}}
        assert self.v._get_attribute_values(data, "field.count") == [0]

    def test_list_value_at_leaf(self) -> None:
        """A list at the leaf is returned as a single-element list (the list itself)."""
        data = {"tags": ["a", "b", "c"]}
        assert self.v._get_attribute_values(data, "tags") == [["a", "b", "c"]]

    def test_list_traversal(self) -> None:
        """When a list is encountered mid-path, all items are traversed."""
        data = {"servers": [{"type": "s3"}, {"type": "gcs"}]}
        assert self.v._get_attribute_values(data, "servers.type") == ["s3", "gcs"]

    def test_empty_dict(self) -> None:
        """Traversing an empty dict returns empty."""
        assert self.v._get_attribute_values({}, "anything") == []

    def test_scalar_at_intermediate_returns_empty(self) -> None:
        """If a scalar is hit before the path is fully consumed, returns empty."""
        data = {"info": "just a string"}
        assert self.v._get_attribute_values(data, "info.title") == []


# ===================================================================
# _expand_wildcard_paths / _expand_and_collect
# ===================================================================


class TestExpandWildcardPaths:
    """Test _expand_wildcard_paths for paths containing '*'."""

    def setup_method(self) -> None:
        self.v = _validator()
        self.data = {
            "models": {
                "orders": {
                    "fields": {
                        "order_id": {"type": "text", "unique": True},
                        "amount": {"type": "long"},
                    }
                },
                "items": {
                    "fields": {
                        "item_id": {"type": "text", "unique": True},
                    }
                },
            }
        }

    def test_single_wildcard(self) -> None:
        """models.* expands to each model name."""
        result = self.v._expand_wildcard_paths(self.data, "models.*")
        assert set(result.keys()) == {"models.orders", "models.items"}

    def test_double_wildcard(self) -> None:
        """models.*.fields.* expands to each field across all models."""
        result = self.v._expand_wildcard_paths(self.data, "models.*.fields.*")
        assert set(result.keys()) == {
            "models.orders.fields.order_id",
            "models.orders.fields.amount",
            "models.items.fields.item_id",
        }

    def test_wildcard_with_leaf_present(self) -> None:
        """Leaf attribute present on some fields, missing on others."""
        result = self.v._expand_wildcard_paths(self.data, "models.*.fields.*.unique")

        assert result["models.orders.fields.order_id.unique"] == [True]
        assert result["models.items.fields.item_id.unique"] == [True]
        assert result["models.orders.fields.amount.unique"] == []

    def test_wildcard_with_leaf_missing_everywhere(self) -> None:
        """When no field has the leaf, all paths map to empty."""
        result = self.v._expand_wildcard_paths(self.data, "models.*.fields.*.description")

        assert all(v == [] for v in result.values())
        assert len(result) == 3  # one per field

    def test_no_wildcard_path(self) -> None:
        """A path without '*' should still resolve correctly."""
        result = self.v._expand_wildcard_paths(self.data, "models.orders.fields.order_id.type")
        assert result == {"models.orders.fields.order_id.type": ["text"]}

    def test_wildcard_on_empty_dict(self) -> None:
        """Wildcard on an empty dict returns empty result."""
        result = self.v._expand_wildcard_paths({"models": {}}, "models.*")
        assert result == {}

    def test_wildcard_missing_intermediate(self) -> None:
        """Missing intermediate key after a wildcard returns empty values."""
        result = self.v._expand_wildcard_paths(self.data, "models.*.nonexistent.*.leaf")

        for path, vals in result.items():
            assert vals == []

    def test_wildcard_with_none_data(self) -> None:
        """None data at any point returns empty values."""
        data = {"models": {"m1": None}}
        result = self.v._expand_wildcard_paths(data, "models.*.fields")

        assert result["models.m1.fields"] == []

    def test_wildcard_with_list_data(self) -> None:
        """List encountered mid-traversal is iterated, items merged by path."""
        data = {
            "servers": {
                "prod": {"roles": [{"name": "admin"}, {"name": "reader"}]},
            }
        }
        result = self.v._expand_wildcard_paths(data, "servers.*.roles.name")

        assert result["servers.prod.roles.name"] == ["admin", "reader"]

    def test_three_level_wildcard(self) -> None:
        """Three wildcards expanding at different levels."""
        data = {
            "a": {
                "x": {"b": {"p": {"val": 1}}},
                "y": {"b": {"q": {"val": 2}, "r": {"val": 3}}},
            }
        }
        result = self.v._expand_wildcard_paths(data, "a.*.b.*.val")

        assert result == {
            "a.x.b.p.val": [1],
            "a.y.b.q.val": [2],
            "a.y.b.r.val": [3],
        }
