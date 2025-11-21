from pathlib import Path

from contract_checker.contract.contract_dcs import DataContractSpecification
from contract_checker.utils.utils import (
    is_dir_or_yaml,
    parse_yml_to_dict,
)


def get_specification_version(contract_content: dict, contract_standard: str) -> str:
    """Get the version of the provided contract based on its standard."""
    if contract_standard == "dcs":
        return str(contract_content["dataContractSpecification"])
    elif contract_standard == "odcs":
        return str(contract_content["apiVersion"])
    else:
        raise ValueError("Specification field not found in data contract.")


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


def load_contracts(contract_path: Path, contract_standard: str) -> list[dict]:
    """Load all data contracts within a user-provided path."""

    path_type = is_dir_or_yaml(contract_path)
    if path_type == "yaml_file":
        contract_paths = [contract_path]
    else:
        # TODO: check working with different folder structures
        contract_paths = list(contract_path.rglob("*.yaml"))
    contracts = []
    for contract_path in contract_paths:
        contract_content = parse_yml_to_dict(file_path=Path(contract_path))
        if contract_content:
            # identify type of contract and load accordingly
            if contract_standard == "dcs":
                contract = DataContractSpecification(
                    contract_path=contract_path,
                    contract_content=contract_content,
                    contract_specification=contract_standard,
                    version=get_specification_version(
                        contract_content, contract_standard
                    ),
                )
                contracts.append(contract)
            elif contract_standard == "odcs":
                pass
                # TODO: implement ODCS contract loading
    return contracts
