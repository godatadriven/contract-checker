"""Accepted values validation check."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class AcceptedValuesCheck(Check):
    """Check if a value is in a list of accepted values.
    This check can be applied to both a string attribute as well as a list attribute."""

    @property
    def check_type(self) -> str:
        return "accepted_values"

    def execute(
        self,
        attribute_path: str,
        path_value_pairs: List[tuple[str, Any]],
        accepted_values: List[str],
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
                        f"Attribute '{actual_path or attribute_path}' is missing, "
                        f"expected one of: '{accepted_values}'",
                    )
                )
                continue

            if isinstance(value, str):
                check_values = [value]
            elif isinstance(value, list):
                check_values = value
            else:
                check_values = [value]

            for val in check_values:
                value_str = str(val)
                passed = value_str in accepted_values

                if passed:
                    message = (
                        f"Attribute '{actual_path or attribute_path}' value '{value_str}' "
                        "is in the list of accepted values"
                    )
                else:
                    message = (
                        f"Attribute '{actual_path or attribute_path}' value '{value_str}' "
                        f"is not in the list of accepted values: '{accepted_values}'"
                    )

                results.append(
                    ValidationResult(
                        "",
                        actual_path or attribute_path,
                        self.check_type,
                        passed,
                        message,
                    )
                )

        return results
