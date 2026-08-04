import json
import logging
from pathlib import Path
from typing import Optional, Union

import jsonschema
import yaml


class CustomSchemaError(Exception):
    """Raised when a JSON Schema is missing, unparseable, or itself invalid."""


def load_and_validate_json_schema(schema_path: Union[str, Path]) -> dict:
    """Load a custom JSON Schema and verify it is itself a valid JSON Schema.

    Unlike :func:`load_json_schema`, this does not swallow errors: it raises
    :class:`CustomSchemaError` with a clear, user-facing message for each failure
    mode so the CLI can fail fast before validating any contracts.

    :param schema_path: Path to the custom JSON Schema file.
    :returns: The parsed schema as a dict.
    :raises CustomSchemaError: If the file is missing, not valid JSON, or not a
        valid JSON Schema (checked against its meta-schema).
    """
    try:
        with open(schema_path, "r") as file:
            schema = json.load(file)
    except FileNotFoundError as e:
        raise CustomSchemaError(f"Custom schema file not found: {schema_path}") from e
    except json.JSONDecodeError as e:
        raise CustomSchemaError(f"Custom schema is not valid JSON ({schema_path}): {e}") from e

    if not isinstance(schema, dict):
        raise CustomSchemaError(f"Custom schema must be a JSON object ({schema_path}).")

    # Validate the schema itself against its meta-schema. The draft is auto-detected
    # from the schema's "$schema" key (falling back to the latest supported draft).
    validator_class = jsonschema.validators.validator_for(schema)
    try:
        validator_class.check_schema(schema)
    except jsonschema.exceptions.SchemaError as e:
        raise CustomSchemaError(f"Custom schema is not a valid JSON Schema ({schema_path}): {e.message}") from e

    return schema


def parse_yml_to_dict(file_path: Path) -> Optional[dict]:
    """Parse a data contract from a YAML string."""
    try:
        with open(file_path, "r") as file:
            yaml_dict = yaml.safe_load(file)
        return yaml_dict if isinstance(yaml_dict, dict) else None
    except Exception as e:
        logging.warning(f"Failed to parse YAML: {e}")
        return None


def load_json_schema(schema_path: str) -> Optional[dict]:
    """Load a JSON schema from a file."""

    try:
        with open(schema_path, "r") as file:
            schema_dict = json.load(file)
        return schema_dict if isinstance(schema_dict, dict) else None
    except Exception as e:
        logging.warning(f"Failed to load JSON schema: {e}")
        return None


def is_dir_or_yaml(path: Path) -> str:
    """Check if the provided path is a directory or a YAML file."""
    if path.is_dir():
        return "directory"
    elif path.is_file() and path.suffix in [".yaml", ".yml"]:
        return "yaml_file"
    else:
        raise ValueError('Provided path is neither a directory nor a file with ".yaml" extension.')
