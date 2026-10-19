import json
import logging
from pathlib import Path
from typing import Optional, Union

import jsonschema
import yaml


class CustomSchemaError(Exception):
    """Raised when a JSON Schema is missing, unparseable, or itself invalid."""


class YamlMappingError(ValueError):
    """Raised when a YAML file cannot be read as a single top-level mapping."""


def load_yaml_mapping(file_path: Path) -> dict:
    """Load a YAML file whose root must be a mapping.

    This does not swallow errors: every failure mode raises
    :class:`YamlMappingError` with a message that names the file, so a broken
    file is reported rather than silently skipped.

    :param file_path: Path to the YAML file.
    :returns: The parsed mapping.
    :raises YamlMappingError: If the file cannot be read, is not valid YAML,
        is empty, or its root is not a mapping.
    """
    try:
        with open(file_path, "r") as file:
            content = yaml.safe_load(file)
    except OSError as e:
        raise YamlMappingError(f"Cannot read {file_path}: {e.strerror}") from e
    except yaml.YAMLError as e:
        raise YamlMappingError(f"{file_path} is not valid YAML: {e}") from e

    if content is None:
        raise YamlMappingError(f"{file_path} is empty.")
    if not isinstance(content, dict):
        raise YamlMappingError(f"{file_path} must contain a mapping at the top level, got {type(content).__name__}.")
    return content


def load_and_validate_json_schema(schema_path: Union[str, Path]) -> dict:
    """Load a JSON Schema (custom or built-in) and verify it is itself a valid JSON Schema.

    Unlike :func:`load_json_schema`, this does not swallow errors: it raises
    :class:`CustomSchemaError` with a clear, user-facing message for each failure
    mode so the CLI can fail fast before validating any contracts.

    :param schema_path: Path to the JSON Schema file.
    :returns: The parsed schema as a dict.
    :raises CustomSchemaError: If the file is missing, not valid JSON, or not a
        valid JSON Schema (checked against its meta-schema).
    """
    try:
        with open(schema_path, "r") as file:
            schema = json.load(file)
    except FileNotFoundError as e:
        raise CustomSchemaError(f"Schema file not found: {schema_path}") from e
    except json.JSONDecodeError as e:
        raise CustomSchemaError(f"Schema is not valid JSON ({schema_path}): {e}") from e

    if not isinstance(schema, dict):
        raise CustomSchemaError(f"Schema must be a JSON object ({schema_path}).")

    # Validate the schema itself against its meta-schema. The draft is auto-detected
    # from the schema's "$schema" key (falling back to the latest supported draft).
    validator_class = jsonschema.validators.validator_for(schema)
    try:
        validator_class.check_schema(schema)
    except jsonschema.exceptions.SchemaError as e:
        raise CustomSchemaError(f"Schema is not a valid JSON Schema ({schema_path}): {e.message}") from e

    return schema


def resolve_lint(cli_lint: Optional[bool], checks_dict: Optional[dict]) -> bool:
    """Decide whether schema validation ("lint") runs. The single place lint is resolved.

    Precedence: the ``--lint/--no-lint`` CLI flag, then the ``lint`` key in the
    checks config, then the default (off), also when a custom schema is supplied.

    :param cli_lint: The CLI flag value, or ``None`` when the flag was not passed.
    :param checks_dict: The parsed checks config (may be ``None``).
    :returns: ``True`` when contracts should be validated against their JSON Schema.
    :raises ValueError: If the config ``lint`` key is present but not a boolean
        (e.g. the quoted string ``"false"``, which ``bool()`` would treat as true).
    """
    if cli_lint is not None:
        return cli_lint

    config_lint = (checks_dict or {}).get("lint")
    if config_lint is not None:
        if not isinstance(config_lint, bool):
            raise ValueError(f"'lint' in the checks config must be true or false, got {config_lint!r}.")
        return config_lint

    return False


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
