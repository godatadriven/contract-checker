import json
import logging
from pathlib import Path
from typing import Optional

import yaml


def parse_yml_to_dict(file_path: Path) -> Optional[dict]:
    """Parse a data contract from a YAML string."""
    try:
        with open(file_path, "r") as file:
            yaml_dict = yaml.safe_load(file)
        return yaml_dict if isinstance(yaml_dict, dict) else None
    except Exception as e:
        logging.warning(f"Failed to parse YAML: {e}")
        return None


def parse_specification(contract_content: dict) -> tuple[str, str]:
    """Check if the contract matches the expected version."""
    if not contract_content:
        raise ValueError("Contract content is not loaded.")

    if "dataContractSpecification" in contract_content:
        version = contract_content["dataContractSpecification"]
        contract_specification = "dataContractSpecification"
        return version, contract_specification
    elif "kind" in contract_content and "apiVersion" in contract_content:
        version = contract_content["apiVersion"]
        contract_specification = contract_content["kind"]
        return version, contract_specification
    else:
        raise ValueError("Specification field not found in contract content.")


def load_json_schema(schema_path: str) -> Optional[dict]:
    """Load a JSON schema from a file."""

    try:
        with open(schema_path, "r") as file:
            schema_dict = json.load(file)
        return schema_dict if isinstance(schema_dict, dict) else None
    except Exception as e:
        logging.warning(f"Failed to load JSON schema: {e}")
        return None
