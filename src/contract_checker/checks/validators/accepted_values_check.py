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

    def execute(self, attribute_path: str, value_list: List[Any], accepted_values: List[str]) -> List[ValidationResult]:
        results = []
        for value in value_list:
            if value is None:
                continue

            if isinstance(value, str):
                items = [value]
            elif isinstance(value, list):
                items = value
            else:
                items = [value]

            for item in items:
                item_str = str(item)
                passed = item_str in accepted_values

                if passed:
                    message = f"Attribute '{attribute_path}' value '{item_str}' is in the list of accepted values"
                else:
                    message = (
                        f"Attribute '{attribute_path}' value '{item_str}' "
                        f"is not in the list of accepted values: '{accepted_values}'"
                    )

                results.append(ValidationResult("", attribute_path, self.check_type, passed, message))

        return results
