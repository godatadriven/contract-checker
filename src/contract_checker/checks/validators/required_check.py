"""Required field validation check."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class RequiredCheck(Check):
    """Check if a required field exists and is not null"""

    @property
    def check_type(self) -> str:
        return "required"

    def execute(self, attribute_path: str, values: List[Any], check_value: bool) -> List[ValidationResult]:
        if check_value:
            if not values:
                passed = False
                message = f"Required attribute '{attribute_path}' is missing"
            elif any(v is None for v in values):
                passed = False
                message = f"Required attribute '{attribute_path}' is null"
            else:
                passed = True
                message = f"Attribute '{attribute_path}' is present"
        else:
            passed = True
            message = f"Attribute '{attribute_path}' is optional"

        return [ValidationResult("", attribute_path, self.check_type, passed, message)]
