"""Pattern matching validation check."""

import re
from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class PatternCheck(Check):
    """Check if value matches a regex pattern"""

    @property
    def check_type(self) -> str:
        return "pattern"

    def execute(
        self, attribute_path: str, path_value_pairs: List[tuple[str, Any]], pattern: str
    ) -> List[ValidationResult]:
        results = []

        for actual_path, value in path_value_pairs:
            if value is None:
                results.append(
                    ValidationResult(
                        "",
                        actual_path or attribute_path,
                        self.check_type,
                        False,
                        f"Attribute '{actual_path or attribute_path}' is missing, cannot match "
                        f"pattern '{pattern}'",
                    )
                )
                continue

            value_str = str(value)
            passed = re.match(pattern, value_str) is not None

            if passed:
                message = f"Attribute '{actual_path or attribute_path}' value '{value_str}' matches "
                f"pattern '{pattern}'"
            else:
                message = (
                    f"Attribute '{actual_path or attribute_path}' value '{value_str}' does not match "
                    f"pattern '{pattern}'"
                )

            results.append(
                ValidationResult(
                    "", actual_path or attribute_path, self.check_type, passed, message
                )
            )

        return results
