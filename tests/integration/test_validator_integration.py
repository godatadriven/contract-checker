"""Integration tests for DataContractValidator.

These tests exercise the full validation pipeline: config parsing →
path resolution → check execution → report assembly. They cover both
wildcard and non-wildcard attribute paths, multiple rules, multiple
contracts, error handling, and summary generation.
"""

from __future__ import annotations

import pytest

from contract_checker.checks.validator import DataContractValidator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_validator(rules: list[dict]) -> DataContractValidator:
    """Create a validator from a list of attribute/check rules."""
    return DataContractValidator({"data_contract_checks": rules})


class _FakeContract:
    """Lightweight stand-in for Contract to avoid on-disk schema validation."""

    def __init__(self, content: dict, path: str = "test-contract.yaml") -> None:
        self.contract_path = path
        self.contract_content = content
        self.custom_schema_path = None


# Shared fixture data
SAMPLE_DATA = {
    "info": {
        "title": "Orders Latest",
        "version": "2.0.0",
        "status": "active",
    },
    "tags": ["checkout", "orders", "s3"],
    "servers": {
        "production": {"type": "s3", "environment": "prod"},
    },
    "models": {
        "orders": {
            "fields": {
                "order_id": {
                    "type": "text",
                    "unique": True,
                    "examples": ["ex1", "ex2", "ex3"],
                    "tags": ["id", "primary"],
                },
                "order_timestamp": {
                    "type": "timestamp",
                    "examples": ["2024-01-01T00:00:00Z"],
                },
                "order_total": {
                    "type": "long",
                    "unique": False,
                },
            }
        },
        "line_items": {
            "fields": {
                "line_item_id": {
                    "type": "text",
                    "unique": True,
                    "examples": ["li1"],
                },
                "sku": {
                    "type": "text",
                },
            }
        },
    },
}


# ===================================================================
# 1. Non-wildcard: single rule, single contract
# ===================================================================


class TestNonWildcardSingleRule:
    """run_checks with a single non-wildcard attribute rule."""

    def test_required_present(self) -> None:
        v = _make_validator([{"attribute": "info.title", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.passed_checks == 1
        assert report.failed_checks == 0
        assert report.results[0].attribute == "info.title"
        assert report.results[0].check_type == "required"

    def test_required_missing(self) -> None:
        v = _make_validator([{"attribute": "info.owner", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.passed_checks == 0
        assert report.failed_checks == 1

    def test_pattern_pass(self) -> None:
        v = _make_validator([{"attribute": "info.title", "checks": [{"pattern": "^Orders"}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.passed_checks == 1

    def test_pattern_fail(self) -> None:
        v = _make_validator([{"attribute": "info.title", "checks": [{"pattern": "^Users"}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.failed_checks == 1

    def test_accepted_values_pass(self) -> None:
        v = _make_validator([{"attribute": "info.version", "checks": [{"accepted_values": ["1.0.0", "2.0.0"]}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.passed_checks == 1

    def test_accepted_values_fail(self) -> None:
        v = _make_validator([{"attribute": "info.version", "checks": [{"accepted_values": ["1.0.0"]}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.failed_checks == 1

    def test_accepted_values_list_attribute(self) -> None:
        """Tags is a list; each item is checked individually."""
        v = _make_validator([{"attribute": "tags", "checks": [{"accepted_values": ["checkout", "orders", "s3"]}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.failed_checks == 0
        # 3 tags → 3 individual results
        assert report.passed_checks == 3

    def test_min_items_pass(self) -> None:
        v = _make_validator([{"attribute": "tags", "checks": [{"min_items": 2}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.passed_checks == 1

    def test_min_items_fail(self) -> None:
        v = _make_validator([{"attribute": "tags", "checks": [{"min_items": 10}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.failed_checks == 1

    def test_max_items_pass(self) -> None:
        v = _make_validator([{"attribute": "tags", "checks": [{"max_items": 5}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.passed_checks == 1

    def test_max_items_fail(self) -> None:
        v = _make_validator([{"attribute": "tags", "checks": [{"max_items": 1}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.failed_checks == 1


# ===================================================================
# 2. Non-wildcard: multiple rules on same contract
# ===================================================================


class TestMultipleRules:
    """run_checks with multiple rules validates all of them."""

    def test_multiple_rules_all_pass(self) -> None:
        v = _make_validator(
            [
                {"attribute": "info.title", "checks": [{"required": True}]},
                {"attribute": "info.version", "checks": [{"required": True}, {"pattern": r"^\d+\.\d+\.\d+$"}]},
                {"attribute": "tags", "checks": [{"min_items": 1}]},
            ]
        )
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.failed_checks == 0
        # 1 (required title) + 2 (required + pattern version) + 1 (min_items tags) = 4
        assert report.total_checks == 4

    def test_multiple_rules_mixed_results(self) -> None:
        v = _make_validator(
            [
                {"attribute": "info.title", "checks": [{"required": True}]},  # pass
                {"attribute": "info.owner", "checks": [{"required": True}]},  # fail
                {"attribute": "info.version", "checks": [{"pattern": "^1\\.0\\.0$"}]},  # fail (2.0.0)
            ]
        )
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.passed_checks == 1
        assert report.failed_checks == 2

    def test_multiple_checks_on_same_attribute(self) -> None:
        """Two checks on the same attribute produce two results."""
        v = _make_validator(
            [
                {
                    "attribute": "info.version",
                    "checks": [
                        {"required": True},
                        {"pattern": r"^\d+\.\d+\.\d+$"},
                    ],
                },
            ]
        )
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.total_checks == 2
        assert report.passed_checks == 2


# ===================================================================
# 3. Non-wildcard: report properties
# ===================================================================


class TestReportProperties:
    """Verify ContractValidationReport fields are set correctly."""

    def test_contract_file_set_on_results(self) -> None:
        """Every result should have the contract path set."""
        v = _make_validator([{"attribute": "info.title", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA, path="my/contract.yaml"))

        assert report.contract_file == "my/contract.yaml"
        for r in report.results:
            assert r.contract_file == "my/contract.yaml"

    def test_report_success_property(self) -> None:
        v = _make_validator([{"attribute": "info.title", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.success is True

    def test_report_not_success_property(self) -> None:
        v = _make_validator([{"attribute": "info.missing", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.success is False

    def test_empty_checks_config(self) -> None:
        """No rules configured produces an empty passing report."""
        v = _make_validator([])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.total_checks == 0
        assert report.success is True


# ===================================================================
# 4. Wildcard: per-field check execution
# ===================================================================


class TestWildcardRequiredCheck:
    """Wildcard + required check integration."""

    def test_required_fails_for_missing_fields(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.unique", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["models.orders.fields.order_id.unique"] is True
        assert results_by_path["models.orders.fields.order_total.unique"] is True
        assert results_by_path["models.line_items.fields.line_item_id.unique"] is True
        assert results_by_path["models.orders.fields.order_timestamp.unique"] is False
        assert results_by_path["models.line_items.fields.sku.unique"] is False

        assert report.passed_checks == 3
        assert report.failed_checks == 2

    def test_required_false_always_passes(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.unique", "checks": [{"required": False}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.failed_checks == 0
        assert report.passed_checks == 5

    def test_required_all_present(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.type", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert report.failed_checks == 0
        assert report.passed_checks == 5


class TestWildcardPatternCheck:
    """Wildcard + pattern check integration."""

    def test_pattern_per_field(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.type", "checks": [{"pattern": "^t"}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["models.orders.fields.order_id.type"] is True
        assert results_by_path["models.orders.fields.order_timestamp.type"] is True
        assert results_by_path["models.orders.fields.order_total.type"] is False
        assert results_by_path["models.line_items.fields.line_item_id.type"] is True
        assert results_by_path["models.line_items.fields.sku.type"] is True

    def test_pattern_on_missing_leaf_no_result(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.unique", "checks": [{"pattern": "^true$"}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert len(report.results) == 3


class TestWildcardAcceptedValuesCheck:
    """Wildcard + accepted_values check integration."""

    def test_accepted_values_per_field(self) -> None:
        v = _make_validator(
            [{"attribute": "models.*.fields.*.type", "checks": [{"accepted_values": ["text", "timestamp"]}]}]
        )
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["models.orders.fields.order_total.type"] is False
        assert report.passed_checks == 4
        assert report.failed_checks == 1


class TestWildcardMinMaxItemsCheck:
    """Wildcard + min_items/max_items check integration."""

    def test_min_items_per_field(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.examples", "checks": [{"min_items": 2}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["models.orders.fields.order_id.examples"] is True
        assert results_by_path["models.orders.fields.order_timestamp.examples"] is False

    def test_max_items_per_field(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.examples", "checks": [{"max_items": 2}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["models.orders.fields.order_id.examples"] is False
        assert results_by_path["models.orders.fields.order_timestamp.examples"] is True

    def test_missing_examples_min_items_fails(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.examples", "checks": [{"min_items": 1}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["models.orders.fields.order_total.examples"] is False
        assert results_by_path["models.line_items.fields.sku.examples"] is False

    def test_missing_examples_max_items_skipped(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.examples", "checks": [{"max_items": 5}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["models.orders.fields.order_total.examples"] is True
        assert results_by_path["models.line_items.fields.sku.examples"] is True


# ===================================================================
# 5. Wildcard edge cases
# ===================================================================


class TestWildcardEdgeCases:
    """Edge cases for wildcard path handling through the full pipeline."""

    def test_single_wildcard_at_top_level(self) -> None:
        data = {"a": {"val": 1}, "b": {"val": 2}, "c": {"val": 3}}
        v = _make_validator([{"attribute": "*.val", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(data))

        assert report.passed_checks == 3

    def test_wildcard_single_key(self) -> None:
        data = {"models": {"only": {"fields": {"f": {"type": "text"}}}}}
        v = _make_validator([{"attribute": "models.*.fields.*.type", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(data))

        assert len(report.results) == 1
        assert report.results[0].attribute == "models.only.fields.f.type"

    def test_all_leaves_missing(self) -> None:
        data = {"models": {"m1": {"fields": {"f1": {None}, "f2": {None}}}}}
        v = _make_validator([{"attribute": "models.*.fields.*.unique", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(data))

        assert report.passed_checks == 0
        assert report.failed_checks == 2

    def test_multiple_checks_per_wildcard(self) -> None:
        v = _make_validator(
            [{"attribute": "models.*.fields.*.examples", "checks": [{"required": True}, {"min_items": 2}]}]
        )
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        assert len(report.results) == 10  # 5 fields x 2 checks

    def test_concrete_paths_no_wildcards_in_output(self) -> None:
        v = _make_validator([{"attribute": "models.*.fields.*.unique", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        for result in report.results:
            assert "*" not in result.attribute
            assert "*" not in result.message

    def test_deeply_nested_wildcards(self) -> None:
        data = {"a": {"x": {"b": {"p": {"c": 1}, "q": {"c": 2}}}, "y": {"b": {"r": {"c": 3}}}}}
        v = _make_validator([{"attribute": "a.*.b.*.c", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(data))

        assert report.passed_checks == 3

    def test_none_at_leaf_fails_required(self) -> None:
        data = {"models": {"m1": {"fields": {"f1": {"unique": None}, "f2": {"unique": True}}}}}
        v = _make_validator([{"attribute": "models.*.fields.*.unique", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(data))

        results_by_path = {r.attribute: r.passed for r in report.results}
        assert results_by_path["models.m1.fields.f1.unique"] is False
        assert results_by_path["models.m1.fields.f2.unique"] is True


# ===================================================================
# 6. Mixed wildcard and non-wildcard rules
# ===================================================================


class TestMixedRules:
    """Config with both wildcard and non-wildcard rules."""

    def test_mixed_rules_in_single_config(self) -> None:
        v = _make_validator(
            [
                {"attribute": "info.title", "checks": [{"required": True}]},
                {"attribute": "info.version", "checks": [{"pattern": r"^\d+\.\d+\.\d+$"}]},
                {"attribute": "models.*.fields.*.type", "checks": [{"required": True}]},
                {"attribute": "models.*.fields.*.unique", "checks": [{"required": True}]},
            ]
        )
        report = v.run_checks(_FakeContract(SAMPLE_DATA))

        # info.title required → 1 pass
        # info.version pattern → 1 pass
        # 5 fields x type required → 5 passes
        # 5 fields x unique required → 3 pass, 2 fail
        assert report.total_checks == 12
        assert report.passed_checks == 10
        assert report.failed_checks == 2


# ===================================================================
# 7. validate() with multiple contracts
# ===================================================================


class TestValidateMultipleContracts:
    """Test the validate() method processing multiple contracts."""

    def test_multiple_contracts_individual_reports(self) -> None:
        contract_a = _FakeContract(SAMPLE_DATA, path="a.yaml")
        contract_b = _FakeContract(
            {"info": {"title": "Other", "version": "1.0.0"}},
            path="b.yaml",
        )

        v = _make_validator(
            [
                {"attribute": "info.title", "checks": [{"required": True}]},
            ]
        )
        reports = v.validate([contract_a, contract_b])

        assert len(reports) == 2
        assert reports[0].contract_file == "a.yaml"
        assert reports[1].contract_file == "b.yaml"
        assert all(r.success for r in reports)

    def test_one_contract_fails_other_passes(self) -> None:
        good = _FakeContract({"info": {"title": "Good"}}, path="good.yaml")
        bad = _FakeContract({"info": {}}, path="bad.yaml")

        v = _make_validator(
            [
                {"attribute": "info.title", "checks": [{"required": True}]},
            ]
        )
        reports = v.validate([good, bad])

        assert reports[0].success is True
        assert reports[1].success is False

    def test_validate_handles_processing_error(self) -> None:
        """A contract that causes an exception should produce a failed report."""

        class _BrokenContract:
            contract_path = "broken.yaml"
            custom_schema_path = None

            @property
            def contract_content(self) -> None:
                raise RuntimeError("Simulated file read error")

        v = _make_validator(
            [
                {"attribute": "info.title", "checks": [{"required": True}]},
            ]
        )
        reports = v.validate([_BrokenContract()])

        assert len(reports) == 1
        assert reports[0].success is False
        assert "Error processing file" in reports[0].results[0].message


# ===================================================================
# 8. get_summary()
# ===================================================================


class TestGetSummary:
    """Test the get_summary() method for aggregated statistics."""

    def test_summary_structure(self) -> None:
        good = _FakeContract({"info": {"title": "Good"}}, path="good.yaml")
        bad = _FakeContract({"info": {}}, path="bad.yaml")

        v = _make_validator(
            [
                {"attribute": "info.title", "checks": [{"required": True}]},
            ]
        )
        reports = v.validate([good, bad])
        summary = v.get_summary(reports)

        assert summary["total_contracts"] == 2
        assert summary["passed_contracts"] == 1
        assert summary["failed_contracts"] == 1
        assert summary["total_checks"] == 2
        assert summary["passed_checks"] == 1
        assert summary["failed_checks"] == 1
        assert len(summary["contracts"]) == 2

    def test_summary_all_pass(self) -> None:
        c = _FakeContract({"info": {"title": "OK"}}, path="ok.yaml")

        v = _make_validator([{"attribute": "info.title", "checks": [{"required": True}]}])
        reports = v.validate([c])
        summary = v.get_summary(reports)

        assert summary["failed_contracts"] == 0
        assert summary["failed_checks"] == 0

    def test_summary_empty_contracts_list(self) -> None:
        v = _make_validator([])
        summary = v.get_summary([])

        assert summary["total_contracts"] == 0
        assert summary["total_checks"] == 0


# ===================================================================
# 9. Unknown check type
# ===================================================================


class TestUnknownCheckType:
    """Requesting an unregistered check type raises an error."""

    def test_unknown_check_type_raises(self) -> None:
        v = _make_validator([{"attribute": "info.title", "checks": [{"nonexistent_check": True}]}])

        with pytest.raises(ValueError, match="Unknown check type"):
            v.run_checks(_FakeContract(SAMPLE_DATA))


# ===================================================================
# 10. ODCS-style contracts (repeatable objects as lists)
# ===================================================================


ODCS_SAMPLE_DATA = {
    "apiVersion": "v3.0.2",
    "kind": "DataContract",
    "name": "my_table",
    "status": "active",
    "schema": [
        {
            "name": "tbl",
            "physicalType": "table",
            "properties": [
                {
                    "name": "rcvr_cntry_code",
                    "logicalType": "string",
                    "primaryKey": True,
                },
                {
                    "name": "amount",
                    "logicalType": "number",
                },
            ],
        }
    ],
}


class TestOdcsListStyleContracts:
    """Full pipeline against ODCS-shaped contracts, where repeatable
    objects are lists of named objects instead of dicts keyed by name."""

    def test_required_name_per_property(self) -> None:
        v = _make_validator([{"attribute": "schema.*.properties.*.name", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(ODCS_SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["schema.tbl.properties.rcvr_cntry_code.name"] is True
        assert results_by_path["schema.tbl.properties.amount.name"] is True
        assert report.failed_checks == 0

    def test_required_missing_leaf_fails_per_property(self) -> None:
        v = _make_validator([{"attribute": "schema.*.properties.*.primaryKey", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(ODCS_SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["schema.tbl.properties.rcvr_cntry_code.primaryKey"] is True
        assert results_by_path["schema.tbl.properties.amount.primaryKey"] is False

    def test_accepted_values_per_property(self) -> None:
        v = _make_validator(
            [{"attribute": "schema.*.properties.*.logicalType", "checks": [{"accepted_values": ["string"]}]}]
        )
        report = v.run_checks(_FakeContract(ODCS_SAMPLE_DATA))

        results_by_path = {r.attribute: r.passed for r in report.results}

        assert results_by_path["schema.tbl.properties.rcvr_cntry_code.logicalType"] is True
        assert results_by_path["schema.tbl.properties.amount.logicalType"] is False

    def test_same_path_shape_works_for_both_standards(self) -> None:
        """The same wildcard path yields field names for list-style (ODCS)
        and dict-style (DCS) contracts alike."""
        odcs_style = {"models": [{"name": "orders", "fields": [{"name": "order_id"}]}]}
        dcs_style = {"models": {"orders": {"fields": {"order_id": {"type": "text"}}}}}

        v = _make_validator([{"attribute": "models.*.fields.*.name", "checks": [{"required": True}]}])

        for content in (odcs_style, dcs_style):
            report = v.run_checks(_FakeContract(content))
            assert report.failed_checks == 0
            assert report.results[0].attribute == "models.orders.fields.order_id.name"

    def test_concrete_paths_no_wildcards_in_output(self) -> None:
        v = _make_validator([{"attribute": "schema.*.properties.*.name", "checks": [{"required": True}]}])
        report = v.run_checks(_FakeContract(ODCS_SAMPLE_DATA))

        assert report.results, "expected per-property results"
        for result in report.results:
            assert "*" not in result.attribute
