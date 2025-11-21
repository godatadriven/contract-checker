from pathlib import Path

from contract_checker.contract.contract_dcs import DataContract
from contract_checker.utils.utils import (
    get_specification_version,
    is_dir_or_yaml,
    parse_yml_to_dict,
)


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
                contract = DataContract(
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
