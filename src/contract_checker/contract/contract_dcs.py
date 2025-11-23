from pathlib import Path
from typing import ClassVar

from pydantic import model_validator
from typing_extensions import Self

from contract_checker.contract.contract_base import Contract
from contract_checker.utils.utils import load_json_schema


def _get_supported_dcs_versions(schema_file_path: Path) -> list[str]:
    """Get all supported versions of the DataContractSpecification."""

    supported_contract_specification_versions = []
    schema_files = list(schema_file_path.rglob("**.json"))
    for schema_file in schema_files:
        schema_file_content = load_json_schema(schema_file)
        contract_specification_version = (
            schema_file_content.get("properties", {})
            .get("dataContractSpecification", {})
            .get("enum", [None])
        )
        supported_contract_specification_versions.extend(contract_specification_version)
    return supported_contract_specification_versions


class DataContractSpecification(Contract):
    SPECIFICATION_FIELD: ClassVar[str] = "dataContractSpecification"
    schema_file_directory: ClassVar[Path] = Path(
        "src/contract_checker/contract_schemas/dcs/"
    )
    supported_versions: ClassVar[list[str]] = _get_supported_dcs_versions(
        schema_file_directory
    )

    @model_validator(mode="after")
    def validate_version(self) -> Self:
        """Validate if the version of the provided contract is supported."""

        if self.contract_specification_version not in self.supported_versions:
            raise ValueError(
                f"Unsupported OpenDataContractSpecification version."
                f"Unsupported version: {self.contract_specification_version}."
                f"Supported versions are: {self.supported_versions}"
            )
        return self
