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
    schema_file_directory: ClassVar[Path]

    @model_validator(mode="after")
    def validate_version(self) -> Self:
        """Validate if the version of the provided contract is supported."""

        if (
            os.path.exists(
                os.path.join(
                    "src/contract_checker/contract_schemas",
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
