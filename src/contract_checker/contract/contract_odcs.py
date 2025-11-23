from pathlib import Path
from typing import ClassVar

from pydantic import model_validator
from typing_extensions import Self

from contract_checker.contract.contract_base import Contract
from contract_checker.utils.utils import load_json_schema


def _get_supported_odcs_versions(schema_file_directory: Path) -> list[str]:
    """Get all supported versions of the OpenDataContractSpecification."""

    supported_contract_specification_versions = []
    schema_file_paths = list(schema_file_directory.rglob("**/*.json"))
    for schema_file_path in schema_file_paths:
        schema_file_content = load_json_schema(schema_file_path)
        contract_specification_version = []
        contract_specification_version = (
            schema_file_content.get("properties", {})
            .get("apiVersion", {})
            .get("enum", [None])
        )

        # Pre 3.x versions of ODCS do not have a version enum.
        if not any(contract_specification_version):
            contract_specification_version = [schema_file_path.parent.name]

        supported_contract_specification_versions.extend(contract_specification_version)

    return supported_contract_specification_versions


class OpenDataContractSpecification(Contract):
    SPECIFICATION_FIELD: ClassVar[str] = "apiVersion"
    schema_file_directory: ClassVar[Path] = Path(
        "src/contract_checker/contract_schemas/odcs/"
    )
    supported_versions: ClassVar[list[str]] = _get_supported_odcs_versions(
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
