import os
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
    schema_file_directory: ClassVar[Path] = Path(__file__).parent / "contract_schemas"

    @model_validator(mode="after")
    def validate_version(self) -> Self:
        """Validate if the version of the provided contract is supported."""

        # Skip validation for custom schemas
        if self.custom_schema_path is not None:
            return self

        if (
            os.path.exists(
                os.path.join(
                    self.schema_file_directory,
                    self.contract_specification,
                    self.contract_specification_version,
                    "schema.json",
                )
            )
            is False
        ):
            raise ValueError(
                f"Contract version {self.contract_specification} is not supported."
            )
        return self
