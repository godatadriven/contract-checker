from pathlib import Path
from typing import ClassVar, Optional

from pydantic import BaseModel


class Contract(BaseModel):
    contract_path: Path
    contract_content: Optional[dict]
    contract_specification_version: str
    contract_specification: str
    SPECIFICATION_FIELD: ClassVar[str]
    schema_file_directory: ClassVar[Path]
    supported_versions: ClassVar[list[str]]
