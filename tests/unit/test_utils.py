"""Unit tests for utility helpers, focused on custom JSON Schema loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from contract_checker.utils.utils import CustomSchemaError, load_and_validate_json_schema

CUSTOM_FIXTURES = Path(__file__).parent.parent / "fixtures" / "custom"


class TestLoadAndValidateJsonSchema:
    """Tests for load_and_validate_json_schema."""

    def test_valid_schema_returns_dict(self) -> None:
        """A well-formed JSON Schema is returned as a dict."""
        schema = load_and_validate_json_schema(CUSTOM_FIXTURES / "ecommerce-product-schema.json")
        assert isinstance(schema, dict)
        assert schema["type"] == "object"

    def test_missing_file_raises(self) -> None:
        """A non-existent path raises a clear CustomSchemaError."""
        with pytest.raises(CustomSchemaError, match="not found"):
            load_and_validate_json_schema(CUSTOM_FIXTURES / "does-not-exist.json")

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        """A file that is not valid JSON raises a clear CustomSchemaError."""
        bad = tmp_path / "bad.json"
        bad.write_text("{ this is not json ")
        with pytest.raises(CustomSchemaError, match="not valid JSON"):
            load_and_validate_json_schema(bad)

    def test_non_object_schema_raises(self, tmp_path: Path) -> None:
        """A JSON document that is not an object is rejected."""
        not_object = tmp_path / "list.json"
        not_object.write_text("[1, 2, 3]")
        with pytest.raises(CustomSchemaError, match="must be a JSON object"):
            load_and_validate_json_schema(not_object)

    def test_schema_invalid_against_metaschema_raises(self) -> None:
        """A document that is valid JSON but not a valid JSON Schema is rejected."""
        with pytest.raises(CustomSchemaError, match="not a valid JSON Schema"):
            load_and_validate_json_schema(CUSTOM_FIXTURES / "invalid-json-schema.json")
