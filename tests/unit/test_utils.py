"""Unit tests for utility helpers: custom JSON Schema loading and lint resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pytest

from contract_checker.utils.utils import (
    CustomSchemaError,
    load_and_validate_json_schema,
    load_yaml_mapping,
    parse_yml_to_dict,
    resolve_lint,
)

CUSTOM_FIXTURES = Path(__file__).parent.parent / "fixtures" / "custom"


class TestResolveLint:
    """Tests for resolve_lint: CLI flag > config 'lint' key > default."""

    @pytest.mark.parametrize(
        ("cli_lint", "checks_dict", "expected"),
        [
            # Default: off.
            (None, None, False),
            (None, {}, False),
            # The config key wins over the default...
            (None, {"lint": True}, True),
            (None, {"lint": False}, False),
            # ...and the CLI flag wins over the config key.
            (True, {"lint": False}, True),
            (False, {"lint": True}, False),
        ],
    )
    def test_precedence(self, cli_lint: Optional[bool], checks_dict: Optional[dict], expected: bool) -> None:
        """Each source is only consulted when the higher-priority one is unset."""
        assert resolve_lint(cli_lint, checks_dict) is expected

    @pytest.mark.parametrize("value", ["false", "true", "yes", 0, 1])
    def test_non_boolean_config_value_raises(self, value: object) -> None:
        """A non-boolean 'lint' (e.g. quoted "false", which bool() treats as true) is rejected."""
        with pytest.raises(ValueError, match="must be true or false"):
            resolve_lint(None, {"lint": value})

    def test_cli_flag_skips_config_type_check(self) -> None:
        """An explicit CLI flag wins, so a malformed config value is never consulted."""
        assert resolve_lint(True, {"lint": "false"}) is True


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


_DATES_YAML = (
    "date: 2024-01-01\n"
    "timestamp: 2024-01-01T00:00:00Z\n"
    'quoted: "2024-01-01T00:00:00Z"\n'
    "integer: 255\n"
    "number: 1.5\n"
    "boolean: true\n"
    "empty: null\n"
)
_DATES_EXPECTED = {
    "date": "2024-01-01",
    "timestamp": "2024-01-01T00:00:00Z",
    "quoted": "2024-01-01T00:00:00Z",
    "integer": 255,
    "number": 1.5,
    "boolean": True,
    "empty": None,
}


class TestYamlLoadingKeepsDatesAsStrings:
    """Contracts and checks configs keep unquoted dates as the text that was written.

    JSON (and so DCS/ODCS) has no date type, so a date is a string, as in
    datacontract-cli. Every other YAML type is parsed as usual.
    """

    def test_load_yaml_mapping(self, tmp_path: Path) -> None:
        path = tmp_path / "contract.yaml"
        path.write_text(_DATES_YAML)
        assert load_yaml_mapping(path) == _DATES_EXPECTED

    def test_parse_yml_to_dict(self, tmp_path: Path) -> None:
        path = tmp_path / "contract.yaml"
        path.write_text(_DATES_YAML)
        assert parse_yml_to_dict(path) == _DATES_EXPECTED
