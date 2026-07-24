import logging
from pathlib import Path
from typing import Optional

from contract_checker.contract.contract_base import Contract
from contract_checker.utils.path_filter import filter_contract_paths
from contract_checker.utils.utils import (
    is_dir_or_yaml,
    parse_yml_to_dict,
)


def parse_data_contracts_path_config(
    checks_dict: dict,
) -> tuple[Optional[Path], list[str], list[str]]:
    """Parse the optional 'data_contracts_path' block from the checks config.

    Accepts either a plain string path:

        data_contracts_path: ./contracts/

    or a mapping with optional glob filters:

        data_contracts_path:
          path: ./contracts/
          include_paths:
            - domain/**
          exclude_paths:
            - marts/**

    Args:
        checks_dict: Parsed checks configuration.

    Returns:
        Tuple of (path or None, include_paths, exclude_paths).

    Raises:
        ValueError: If 'data_contracts_path' is neither a string nor a mapping.
    """
    raw = (checks_dict or {}).get("data_contracts_path")
    if raw is None:
        return None, [], []
    if isinstance(raw, str):
        return Path(raw), [], []
    if not isinstance(raw, dict):
        raise ValueError("'data_contracts_path' must be a string or a mapping.")

    for ignored_key in ("include_custom", "exclude_custom"):
        if ignored_key in raw:
            logging.debug(f"'{ignored_key}' in data_contracts_path is not yet supported and will be ignored.")

    path = Path(raw["path"]) if raw.get("path") else None
    return path, raw.get("include_paths") or [], raw.get("exclude_paths") or []


def get_specification_version(contract_content: dict, contract_standard: str) -> str:
    """Get the version of the provided contract based on its standard."""
    if contract_standard == "custom":
        return "custom"
    elif contract_standard == "dcs":
        return str(contract_content["dataContractSpecification"])
    elif contract_standard == "odcs":
        return str(contract_content["apiVersion"])
    else:
        raise ValueError("Specification field not found in data contract.")


def parse_specification_from_contract(contract_content: dict, checks_dict: dict) -> tuple[str, str]:
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


def load_contracts(
    contract_path: Path,
    contract_specification: str,
    custom_schema_path: Optional[Path] = None,
    include_paths: Optional[list[str]] = None,
    exclude_paths: Optional[list[str]] = None,
) -> list[dict]:
    """Load all data contracts within a user-provided path."""

    # Check if the contract_path exists before proceeding
    if not contract_path.exists():
        raise FileNotFoundError(f"Provided contract path does not exist: {contract_path}")

    path_type = is_dir_or_yaml(contract_path)
    if path_type == "yaml_file":
        contract_paths = [contract_path]
    else:
        contract_paths = sorted([*contract_path.rglob("*.yaml"), *contract_path.rglob("*.yml")])
        discovered_count = len(contract_paths)
        contract_paths = filter_contract_paths(contract_paths, contract_path, include_paths or [], exclude_paths or [])
        logging.debug(
            f"Discovered {discovered_count} contract file(s), {len(contract_paths)} remaining after filtering."
        )
        if discovered_count > 0 and not contract_paths:
            logging.warning(
                "include_paths/exclude_paths filtered out ALL discovered contracts, nothing will be validated. "
                "Check your patterns in 'data_contracts_path'."
            )
    contracts = []
    for contract_path in contract_paths:
        contract_content = parse_yml_to_dict(file_path=Path(contract_path))
        if contract_content:
            # Determine if using custom schema
            if custom_schema_path:
                specification = "custom"
                version = "custom"
            else:
                specification = contract_specification
                version = get_specification_version(contract_content, contract_specification)

            # identify type of contract and load accordingly
            contract = Contract(
                contract_path=contract_path,
                contract_content=contract_content,
                contract_specification=specification,
                contract_specification_version=version,
                custom_schema_path=custom_schema_path,
            )
            contracts.append(contract)

    return contracts
