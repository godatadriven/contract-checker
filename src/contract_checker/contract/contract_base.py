from pathlib import Path
from typing import ClassVar, Optional

from pydantic import BaseModel, model_validator
from typing_extensions import Self

# The vendored standard schemas (DCS / ODCS) live alongside the package, not in
# the current working directory. Resolve them relative to this module so lookups
# work both from the repo root and from a pip-installed package. This module is
# deliberately free of other ``contract_checker`` imports to keep it a safe leaf.
STANDARD_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contract_schemas"


def get_standard_schema_path(specification: str, version: str) -> Path:
    """Return the path to the vendored JSON Schema for a standard and version.

    :param specification: The contract standard (e.g. ``dcs`` or ``odcs``).
    :param version: The standard version (e.g. ``1.2.1``).
    :returns: Path to the ``schema.json`` for that standard/version.
    """
    return STANDARD_SCHEMA_DIR / specification / version / "schema.json"


class Contract(BaseModel):
    contract_path: Path
    contract_content: Optional[dict]
    contract_specification: str
    contract_specification_version: str
    custom_schema_path: Optional[Path] = None
    schema_file_directory: ClassVar[Path] = STANDARD_SCHEMA_DIR

    @model_validator(mode="after")
    def validate_version(self) -> Self:
        """Validate if the version of the provided contract is supported."""

        # Skip validation for custom schemas
        if self.custom_schema_path is not None:
            return self

        schema_file = get_standard_schema_path(self.contract_specification, self.contract_specification_version)

        if not schema_file.is_file():
            raise ValueError(
                f"Contract specification '{self.contract_specification}' "
                f"version '{self.contract_specification_version}' is not supported."
            )
        return self
