from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from contract_checker.utils.utils import parse_data_contract_from_str

class Check(BaseModel):
    path: Path
    include: Optional[dict]
    exclude: Optional[dict]
    severity: Optional[str]
    
    def parse_checks_yml(self, checks_yml_path: Path) -> Optional[dict]:
        """Parse checks from a YAML file."""
        checks_dict = parse_data_contract_from_str(checks_yml_path)
        if not checks_dict:
            raise ValueError(f"Failed to parse checks from {checks_yml_path}")
        return checks_dict if isinstance(checks_dict, dict) else None