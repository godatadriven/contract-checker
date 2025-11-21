import glob
from pathlib import Path
from typing import ClassVar, Optional

from pydantic import model_validator
from typing_extensions import Self

from contract_checker.contract.base import ContractParser
from contract_checker.contract.contract_base import Contract
from contract_checker.utils.utils import load_json_schema, parse_yml_to_dict


def _get_supported_dcs_versions(schema_file_path: Path) -> list[str]:
    """Get all supported versions of the DataContractSpecification."""

    supported_versions = []
    schema_files = list(schema_file_path.rglob("*.json"))
    for schema_file in schema_files:
        schema_file_content = load_json_schema(schema_file)
        version = (
            schema_file_content.get("properties", {})
            .get("dataContractSpecification", {})
            .get("enum", [None])
        )
        supported_versions.extend(version)
    return supported_versions


def get_specification_version(contract_content: dict, contract_standard: str) -> str:
    """Get the version of the provided contract based on its standard."""
    if contract_standard == "dcs":
        return contract_content["dataContractSpecification"]
    elif contract_standard == "odcs":
        return contract_content["apiVersion"]
    else:
        raise ValueError("Specification field not found in data contract.")


def load_contracts(contract_directory_path: Path, contract_standard: str) -> list[dict]:
    """Load all data contracts within a user-provided directory path."""
    print(str(contract_directory_path / "*.yaml"))
    contract_paths = list(
        glob.glob(str(contract_directory_path / "**/*.yaml"), recursive=True)
    )
    contracts = []
    for contract_path in contract_paths:
        contract_content = parse_yml_to_dict(file_path=Path(contract_path))
        if contract_content:
            contract = Contract(
                contract_path=contract_path,
                contract_content=contract_content,
                contract_specification=contract_standard,
                version=get_specification_version(contract_content, contract_standard),
            )
            contracts.append(contract)
    return contracts


class DataContractParser(ContractParser):
    contract_path: Path
    contract_content: Optional[dict]
    version: str
    contract_specification: str
    SPECIFICATION_FIELD: ClassVar[str] = "dataContractSpecification"
    schema_file_path: ClassVar[Path] = Path(
        "src/contract_checker/contract_schemas/dcs/"
    )
    supported_versions: ClassVar[list[str]] = _get_supported_dcs_versions(
        schema_file_path
    )

    @model_validator(mode="after")
    def validate_version(self) -> Self:
        """Validate if the version of the provided contract is supported."""

        if self.version not in self.supported_versions:
            raise ValueError(
                f"Unsupported DataContractSpecification version: {self.version}."
                f"Supported versions are: {self.supported_versions}"
            )
        return self
