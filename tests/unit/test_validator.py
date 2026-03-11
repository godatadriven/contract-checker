"""Tests for wildcard path matching in DataContractValidator._traverse_path()."""

import os
import tempfile
from typing import Any, Dict, List

import pytest
import yaml

from contract_checker.checks.validator import DataContractValidator
from contract_checker.contract.contract_base import Contract

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_validator(checks: List[Dict[str, Any]]) -> DataContractValidator:
    """Create a DataContractValidator from an in-memory checks list."""
    config = {"data_contract_checks": checks}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(config, tmp)
        tmp_path = tmp.name
    try:
        return DataContractValidator(checks_file=tmp_path)
    finally:
        os.unlink(tmp_path)


def _make_contract(content: Dict[str, Any]) -> Contract:
    """Create a minimal Contract object with the given content (skip validation)."""
    return Contract.model_construct(
        contract_path="test-contract.yaml",
        contract_content=content,
        contract_specification="dcs",
        contract_specification_version="1.2.0",
        custom_schema_path=None,
    )


# ---------------------------------------------------------------------------
# Unit tests for _traverse_path
# ---------------------------------------------------------------------------


class TestTraversePath:
    """Direct unit tests for DataContractValidator._traverse_path()."""

    @pytest.fixture()
    def validator(self) -> DataContractValidator:
        return _make_validator([])

    # -- Single-level wildcard -------------------------------------------------

    def test_single_level_wildcard(self, validator: DataContractValidator) -> None:
        """models.* should return all top-level values."""
        data = {
            "models": {
                "orders": {"description": "Orders table"},
                "customers": {"description": "Customers table"},
            }
        }
        result = validator._get_attribute_values(data, "models.*")
        assert len(result) == 2
        # Result is now list of (path, value) tuples
        paths = [path for path, _ in result]
        values = [value for _, value in result]
        assert "models.orders" in paths
        assert "models.customers" in paths
        assert {"description": "Orders table"} in values
        assert {"description": "Customers table"} in values

    def test_single_level_wildcard_with_child_key(
        self, validator: DataContractValidator
    ) -> None:
        """models.*.description should return the description of every model."""
        data = {
            "models": {
                "orders": {"description": "Orders table"},
                "customers": {"description": "Customers table"},
            }
        }
        result = validator._get_attribute_values(data, "models.*.description")
        # Result is now list of (path, value) tuples
        values = [value for _, value in result]
        assert sorted(values) == ["Customers table", "Orders table"]

    # -- Multi-level wildcard --------------------------------------------------

    def test_multi_level_wildcard(self, validator: DataContractValidator) -> None:
        """models.*.fields.*.examples should collect examples from all fields."""
        data = {
            "models": {
                "orders": {
                    "fields": {
                        "order_id": {"examples": ["abc"]},
                        "total": {"examples": [100, 200]},
                    }
                },
                "customers": {
                    "fields": {
                        "name": {"examples": ["Alice"]},
                    }
                },
            }
        }
        result = validator._get_attribute_values(data, "models.*.fields.*.examples")
        assert len(result) == 3
        # Result is now list of (path, value) tuples
        values = [value for _, value in result]
        assert ["abc"] in values
        assert [100, 200] in values
        assert ["Alice"] in values

    # -- Empty / no-match cases ------------------------------------------------

    def test_wildcard_on_empty_dict(self, validator: DataContractValidator) -> None:
        """Wildcard over an empty dict should return an empty list."""
        data = {"models": {}}
        result = validator._get_attribute_values(data, "models.*.description")
        assert result == []

    def test_wildcard_missing_child_key(self, validator: DataContractValidator) -> None:
        """If some children lack the target key, missing ones are returned with None."""
        data = {
            "models": {
                "orders": {"description": "has desc"},
                "customers": {},  # no description
            }
        }
        result = validator._get_attribute_values(data, "models.*.description")
        paths = [path for path, _ in result]
        values = [value for _, value in result]
        assert "models.orders.description" in paths
        assert "models.customers.description" in paths
        assert "has desc" in values
        assert None in values

    def test_wildcard_all_children_missing(
        self, validator: DataContractValidator
    ) -> None:
        """If no children have the target key, all are returned with None value."""
        data = {
            "models": {
                "orders": {"type": "table"},
                "customers": {"type": "view"},
            }
        }
        result = validator._get_attribute_values(data, "models.*.description")
        assert len(result) == 2
        assert all(value is None for _, value in result)
        paths = [path for path, _ in result]
        assert "models.orders.description" in paths
        assert "models.customers.description" in paths

    # -- Mixed presence --------------------------------------------------------

    def test_mixed_presence(self, validator: DataContractValidator) -> None:
        """Wildcard returns resolved paths: present fields with values, missing leaf with None."""
        data = {
            "models": {
                "a": {"fields": {"f1": {"examples": [1]}}},
                "b": {"fields": {"f2": {}}},  # no examples
                "c": {},  # no fields at all (intermediate key missing — not returned)
            }
        }
        result = validator._get_attribute_values(data, "models.*.fields.*.examples")
        paths = [path for path, _ in result]
        values = [value for _, value in result]
        # f1 has examples, f2 is missing examples (None), c has no fields (skipped)
        assert "models.a.fields.f1.examples" in paths
        assert "models.b.fields.f2.examples" in paths
        assert [1] in values
        assert None in values
        assert len(result) == 2

    # -- Non-wildcard paths still work (regression) ----------------------------

    def test_non_wildcard_path(self, validator: DataContractValidator) -> None:
        """Literal paths should continue to work as before."""
        data = {"info": {"title": "My Contract", "version": "1.0"}}
        result = validator._get_attribute_values(data, "info.title")
        # Result is now list of (path, value) tuples
        values = [value for _, value in result]
        assert values == ["My Contract"]

    def test_non_wildcard_missing(self, validator: DataContractValidator) -> None:
        """Literal path where last key doesn't exist returns (path, None)."""
        data = {"info": {"title": "My Contract"}}
        result = validator._get_attribute_values(data, "info.owner")
        assert result == [("info.owner", None)]

    # -- List traversal still works (regression) -------------------------------

    def test_list_traversal(self, validator: DataContractValidator) -> None:
        """Existing list-traversal behaviour should be preserved."""
        data = {"items": [{"name": "a"}, {"name": "b"}]}
        result = validator._get_attribute_values(data, "items.name")
        # Result is now list of (path, value) tuples
        values = [value for _, value in result]
        assert sorted(values) == ["a", "b"]


# ---------------------------------------------------------------------------
# Integration tests: checks with wildcard paths
# ---------------------------------------------------------------------------


class TestWildcardIntegration:
    """End-to-end tests running actual checks through wildcard paths."""

    def test_min_items_with_wildcard(self) -> None:
        """min_items check should work on a wildcard attribute path."""
        checks = [
            {
                "attribute": "models.*.fields.*.examples",
                "checks": [{"min_items": 1}],
            }
        ]
        validator = _make_validator(checks)

        content = {
            "models": {
                "orders": {
                    "fields": {
                        "order_id": {"examples": ["abc"]},
                        "total": {"examples": [100, 200]},
                    }
                }
            }
        }
        contract = _make_contract(content)
        report = validator.run_checks(contract)

        assert report.failed_checks == 0
        assert report.passed_checks > 0

    def test_min_items_with_wildcard_fails(self) -> None:
        """min_items check should fail when a wildcard-matched value is empty."""
        checks = [
            {
                "attribute": "models.*.fields.*.examples",
                "checks": [{"min_items": 1}],
            }
        ]
        validator = _make_validator(checks)

        content = {
            "models": {
                "orders": {
                    "fields": {
                        "order_id": {"examples": []},  # empty list
                    }
                }
            }
        }
        contract = _make_contract(content)
        report = validator.run_checks(contract)

        assert report.failed_checks > 0

    def test_min_items_missing_key_shows_resolved_path(self) -> None:
        """When a field is missing 'examples' entirely, the error shows the resolved path."""
        checks = [
            {
                "attribute": "models.*.fields.*.examples",
                "checks": [{"min_items": 1}],
            }
        ]
        validator = _make_validator(checks)

        content = {
            "models": {
                "orders": {
                    "fields": {
                        "order_id": {},  # no 'examples' key at all
                    }
                }
            }
        }
        contract = _make_contract(content)
        report = validator.run_checks(contract)

        assert report.failed_checks > 0
        failed = [r for r in report.results if not r.passed]
        assert len(failed) == 1
        # The error must reference the concrete field path, not the wildcard pattern
        assert "models.orders.fields.order_id.examples" in failed[0].attribute
        assert "*" not in failed[0].attribute

    def test_required_with_wildcard(self) -> None:
        """required check should work on a wildcard attribute path."""
        checks = [
            {
                "attribute": "models.*.description",
                "checks": [{"required": True}],
            }
        ]
        validator = _make_validator(checks)

        content = {
            "models": {
                "orders": {"description": "Orders table"},
                "customers": {"description": "Customers table"},
            }
        }
        contract = _make_contract(content)
        report = validator.run_checks(contract)

        assert report.failed_checks == 0
        assert report.passed_checks > 0

    def test_required_with_wildcard_fails(self) -> None:
        """required check should fail with the resolved path, not the wildcard pattern."""
        checks = [
            {
                "attribute": "models.*.nonexistent",
                "checks": [{"required": True}],
            }
        ]
        validator = _make_validator(checks)

        content = {
            "models": {
                "orders": {"description": "Orders table"},
            }
        }
        contract = _make_contract(content)
        report = validator.run_checks(contract)

        assert report.failed_checks > 0
        failed = [r for r in report.results if not r.passed]
        assert len(failed) == 1
        assert "models.orders.nonexistent" in failed[0].attribute
        assert "*" not in failed[0].attribute

    # -- Integration with real fixture -----------------------------------------

    def test_wildcard_on_orders_latest_fixture(self) -> None:
        """Wildcard path should match fields in the real orders-latest fixture."""
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "fixtures",
            "dcs",
            "1.2.0",
            "orders-latest.yaml",
        )
        with open(fixture_path) as f:
            content = yaml.safe_load(f)

        validator = _make_validator([])

        # models.*.description should find descriptions for orders and line_items
        descriptions = validator._get_attribute_values(content, "models.*.description")
        assert len(descriptions) == 2
        # Result is now list of (path, value) tuples
        description_values = [value for _, value in descriptions]
        assert any("order" in d.lower() for d in description_values)
        assert any("article" in d.lower() for d in description_values)

        # models.*.fields.*.examples should find examples across both models
        examples = validator._get_attribute_values(
            content, "models.*.fields.*.examples"
        )
        assert len(examples) >= 2  # at least order_timestamp and order_total
