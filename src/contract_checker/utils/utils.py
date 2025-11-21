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


def parse_specification_from_contract(
    contract_content: dict, checks_dict: dict
) -> tuple[str, str]:
    """Check if the contract matches the expected version."""
    if not contract_content:
        raise ValueError("Contract content is not loaded.")

    if "data_contract_standard" in checks_dict:
        contract_specification = checks_dict["data_contract_standard"]
    else:
        raise ValueError("data_contract_standard not configured.")

    # Maybe we can simplify this with a mapping dict in utils later?
    if contract_specification == "dcs":
        version = contract_content["dataContractSpecification"]
    elif contract_specification == "odcs":
        version = contract_content["apiVersion"]
        return version, contract_specification
    else:
        raise ValueError("Specification field not found in data contract.")

    return version, contract_specification


def load_json_schema(schema_path: str) -> Optional[dict]:
    """Load a JSON schema from a file."""

    try:
        with open(schema_path, "r") as file:
            schema_dict = json.load(file)
        return schema_dict if isinstance(schema_dict, dict) else None
    except Exception as e:
        logging.warning(f"Failed to load JSON schema: {e}")
        return None
