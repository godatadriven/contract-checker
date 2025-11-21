from pathlib import Path
from typing import ClassVar, Optional

from pydantic import model_validator
from typing_extensions import Self

from contract_checker.contract.contract_base import Contract


def _get_supported_odcs_versions(schema_file_path: Path) -> list[str]:
    """Get all supported versions of the OpenDataContractSpecification."""

    # TODO: change to read from schema files after decision on versioning
    supported_versions = []
    folders = [item.name for item in schema_file_path.iterdir() if item.is_dir()]
    supported_versions.extend(folders)
    return supported_versions


class OpenDataContractSpecification(Contract):
    contract_path: Path
    contract_content: Optional[dict]
    version: str
    contract_specification: str
    SPECIFICATION_FIELD: ClassVar[str] = "apiVersion"
    schema_file_path: ClassVar[Path] = Path(
        "src/contract_checker/contract_schemas/odcs/"
    )
    supported_versions: ClassVar[list[str]] = _get_supported_odcs_versions(
        schema_file_path
    )

    @model_validator(mode="after")
    def validate_version(self) -> Self:
        """Validate if the version of the provided contract is supported."""

        if self.version not in self.supported_versions:
            raise ValueError(
                f"Unsupported OpenDataContractSpecification version: {self.version}. "
                f"Supported versions are: {self.supported_versions}"
            )
        return self
