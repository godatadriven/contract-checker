from pathlib import Path
from typing import ClassVar, Optional

from pydantic import BaseModel, model_validator
from typing_extensions import Self


class Contract(BaseModel):
    contract_path: Path
    contract_content: Optional[dict]
    contract_specification: str
    contract_specification_version: str
    custom_schema_path: Optional[Path] = None
    schema_file_directory: ClassVar[Path] = Path(__file__).resolve().parent.parent / "contract_schemas"

    @model_validator(mode="after")
    def validate_version(self) -> Self:
        """Validate if the version of the provided contract is supported."""

        # Skip validation for custom schemas
        if self.custom_schema_path is not None:
            return self

        schema_file = (
            self.schema_file_directory
            / self.contract_specification
            / self.contract_specification_version
            / "schema.json"
        )

        if not schema_file.is_file():
            raise ValueError(
                f"Contract specification '{self.contract_specification}' "
                f"version '{self.contract_specification_version}' is not supported."
            )
        return self
