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

    def test_none_value_preserved(self) -> None:
        """Explicitly None leaf is preserved as [None] (not collapsed to []).

        This lets required_check distinguish missing (=[]) from null (=[None]).
        """
        data = {"info": {"title": None}}
        assert self.v._get_attribute_values(data, "info.title") == [None]

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


# ===================================================================
# _expand_and_collect: ODCS-style lists of named objects
# ===================================================================


class TestExpandWildcardPathsListStyle:
    """Wildcard expansion over ODCS-style lists (repeatable objects as lists)."""

    def setup_method(self) -> None:
        self.v = _validator()
        self.data = {
            "schema": [
                {
                    "name": "tbl",
                    "physicalType": "table",
                    "properties": [
                        {"name": "rcvr_cntry_code", "logicalType": "string", "primaryKey": True},
                        {"name": "amount", "logicalType": "number"},
                    ],
                },
            ]
        }

    def test_single_wildcard_over_list(self) -> None:
        """schema.* expands to each list item, labeled by its name."""
        result = self.v._expand_wildcard_paths(self.data, "schema.*.name")
        assert result == {"schema.tbl.name": ["tbl"]}

    def test_double_wildcard_over_lists(self) -> None:
        """Wildcards expand through nested lists of named objects."""
        result = self.v._expand_wildcard_paths(self.data, "schema.*.properties.*.logicalType")
        assert result == {
            "schema.tbl.properties.rcvr_cntry_code.logicalType": ["string"],
            "schema.tbl.properties.amount.logicalType": ["number"],
        }

    def test_name_leaf_over_list(self) -> None:
        """The explicit `name` value of each list item is returned."""
        result = self.v._expand_wildcard_paths(self.data, "schema.*.properties.*.name")
        assert result == {
            "schema.tbl.properties.rcvr_cntry_code.name": ["rcvr_cntry_code"],
            "schema.tbl.properties.amount.name": ["amount"],
        }

    def test_leaf_missing_on_some_items(self) -> None:
        """Items lacking the leaf map to empty lists (per-item, not merged)."""
        result = self.v._expand_wildcard_paths(self.data, "schema.*.properties.*.primaryKey")
        assert result["schema.tbl.properties.rcvr_cntry_code.primaryKey"] == [True]
        assert result["schema.tbl.properties.amount.primaryKey"] == []

    def test_nested_repeatable_objects(self) -> None:
        """ODCS nests repeatable objects as `properties` inside `properties`."""
        data = {
            "schema": [
                {
                    "name": "t",
                    "properties": [
                        {
                            "name": "cost_breakdown",
                            "logicalType": "object",
                            "properties": [
                                {"name": "slot_cost", "logicalType": "number"},
                                {"name": "storage_cost", "logicalType": "number"},
                            ],
                        }
                    ],
                }
            ]
        }
        result = self.v._expand_wildcard_paths(data, "schema.*.properties.*.properties.*.name")
        assert result == {
            "schema.t.properties.cost_breakdown.properties.slot_cost.name": ["slot_cost"],
            "schema.t.properties.cost_breakdown.properties.storage_cost.name": ["storage_cost"],
        }

    def test_unnamed_items_labeled_by_index(self) -> None:
        """List items without a `name` are labeled by their index."""
        data = {"servers": [{"type": "s3"}, {"type": "gcs"}]}
        result = self.v._expand_wildcard_paths(data, "servers.*.type")
        assert result == {"servers.0.type": ["s3"], "servers.1.type": ["gcs"]}

    def test_wildcard_over_list_of_scalars(self) -> None:
        """A wildcard over scalar items yields the items themselves."""
        data = {"tags": ["a", "b"]}
        result = self.v._expand_wildcard_paths(data, "tags.*")
        assert result == {"tags.0": ["a"], "tags.1": ["b"]}

    def test_wildcard_over_list_of_scalars_with_leaf(self) -> None:
        """A leaf segment on scalar items resolves to empty, not a crash."""
        data = {"tags": ["a", "b"]}
        result = self.v._expand_wildcard_paths(data, "tags.*.name")
        assert result == {"tags.0.name": [], "tags.1.name": []}

    def test_list_transparent_without_wildcard(self) -> None:
        """Non-wildcard segments still iterate list items transparently."""
        result = self.v._expand_wildcard_paths(self.data, "schema.properties.name")
        assert result == {"schema.properties.name": ["rcvr_cntry_code", "amount"]}

    def test_empty_list(self) -> None:
        """Wildcard on an empty list returns an empty result."""
        result = self.v._expand_wildcard_paths({"schema": []}, "schema.*.name")
        assert result == {}

    def test_duplicate_names_are_not_merged(self) -> None:
        """Items sharing a name get `name[index]` labels and are checked separately."""
        data = {
            "schema": [
                {
                    "name": "orders",
                    "properties": [{"name": "id", "logicalType": "string"}, {"name": "amount"}, {"name": "id"}],
                }
            ]
        }
        result = self.v._expand_wildcard_paths(data, "schema.*.properties.*.logicalType")
        assert result == {
            "schema.orders.properties.id[0].logicalType": ["string"],
            "schema.orders.properties.amount.logicalType": [],
            "schema.orders.properties.id[2].logicalType": [],
        }

    def test_duplicate_parent_names_keep_collections_apart(self) -> None:
        """Two schema objects with the same name each yield their own collection."""
        data = {"schema": [{"name": "t", "properties": [{"name": "a"}]}, {"name": "t", "properties": [{"name": "b"}]}]}
        result = self.v._expand_wildcard_paths(data, "schema.*.properties")
        assert result == {
            "schema.t[0].properties": [[{"name": "a"}]],
            "schema.t[1].properties": [[{"name": "b"}]],
        }

    def test_name_equal_to_other_items_index(self) -> None:
        """A name that equals an unnamed item's index does not merge the two."""
        data = {"schema": [{"x": 1}, {"name": "0", "x": 2}]}
        result = self.v._expand_wildcard_paths(data, "schema.*.x")
        assert result == {"schema.0[0].x": [1], "schema.0[1].x": [2]}


# ===================================================================
# _expand_and_collect: key-as-name for DCS-style dicts
# ===================================================================


class TestExpandWildcardKeyAsName:
    """DCS-style dicts carry the entry name as the key; `name` resolves to it."""

    def setup_method(self) -> None:
        self.v = _validator()

    def test_field_names_from_keys(self) -> None:
        data = {
            "models": {
                "orders": {
                    "fields": {
                        "order_id": {"type": "text"},
                        "amount": {"type": "long"},
                    }
                }
            }
        }
        result = self.v._expand_wildcard_paths(data, "models.*.fields.*.name")
        assert result == {
            "models.orders.fields.order_id.name": ["order_id"],
            "models.orders.fields.amount.name": ["amount"],
        }

    def test_model_names_from_keys(self) -> None:
        data = {"models": {"orders": {"type": "table"}, "items": {"type": "table"}}}
        result = self.v._expand_wildcard_paths(data, "models.*.name")
        assert result == {
            "models.orders.name": ["orders"],
            "models.items.name": ["items"],
        }

    def test_explicit_name_value_wins_over_key(self) -> None:
        """DCS `definitions` entries can carry a real `name` value."""
        data = {"definitions": {"order_id": {"name": "order_identifier", "type": "text"}}}
        result = self.v._expand_wildcard_paths(data, "definitions.*.name")
        assert result == {"definitions.order_id.name": ["order_identifier"]}

    def test_nested_records(self) -> None:
        """Key-as-name applies at any depth (nested DCS records)."""
        data = {
            "models": {
                "orders": {
                    "fields": {
                        "cost_breakdown": {
                            "type": "record",
                            "fields": {
                                "slot_cost": {"type": "number"},
                                "storage_cost": {"type": "number"},
                            },
                        }
                    }
                }
            }
        }
        result = self.v._expand_wildcard_paths(data, "models.*.fields.*.fields.*.name")
        assert result == {
            "models.orders.fields.cost_breakdown.fields.slot_cost.name": ["slot_cost"],
            "models.orders.fields.cost_breakdown.fields.storage_cost.name": ["storage_cost"],
        }

    def test_other_missing_leaf_stays_empty(self) -> None:
        """Only `name` resolves to the key; other missing leaves stay empty."""
        data = {"models": {"orders": {"fields": {"order_id": {"type": "text"}}}}}
        result = self.v._expand_wildcard_paths(data, "models.*.fields.*.description")
        assert result == {"models.orders.fields.order_id.description": []}
