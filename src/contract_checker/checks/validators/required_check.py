"""Required field validation check."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class RequiredCheck(Check):
    """Check if a required field exists and is not null"""

    @property
    def check_type(self) -> str:
        return "required"

    def execute(
        self,
        attribute_path: str,
        path_value_pairs: List[tuple[str, Any]],
        check_value: bool,
    ) -> List[ValidationResult]:
        if not check_value:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    True,
                    f"Attribute '{attribute_path}' is optional",
                )
            ]

        if not path_value_pairs:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    False,
                    f"Required attribute '{attribute_path}' is missing",
                )
            ]

        results = []
        for actual_path, value in path_value_pairs:
            if value is None:
                results.append(
                    ValidationResult(
                        "",
                        actual_path,
                        self.check_type,
                        False,
                        f"Required attribute '{actual_path}' is missing",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        "",
                        actual_path,
                        self.check_type,
                        True,
                        f"Attribute '{actual_path}' is present",
                    )
                )
        return results
