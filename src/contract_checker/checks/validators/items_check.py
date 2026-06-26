"""List length validation checks."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class MinItemsCheck(Check):
    """Check if list has minimum number of items"""

    @property
    def check_type(self) -> str:
        return "min_items"

    def execute(self, attribute_path: str, values: List[Any], min_count: int) -> List[ValidationResult]:
        if not values:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    False,
                    f"Attribute '{attribute_path}' is missing, expected at least {min_count} items",
                )
            ]

        if any(v is None for v in values):
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    True,
                    f"Attribute '{attribute_path}' is null (min_items check skipped)",
                )
            ]

        # Check if any value is a list and validate its length
        all_passed = True
        for value in values:
            if isinstance(value, list):
                if len(value) < min_count:
                    all_passed = False
                    break
            else:
                # If it's not a list but we expect min_items, that's a failure
                all_passed = False
                break

        passed = all_passed and len(values) > 0

        if passed:
            message = f"Attribute '{attribute_path}' has at least {min_count} items"
        else:
            message = f"Attribute '{attribute_path}' has fewer than {min_count} items"

        return [ValidationResult("", attribute_path, self.check_type, passed, message)]


class MaxItemsCheck(Check):
    """Check if list does not exceed maximum number of items"""

    @property
    def check_type(self) -> str:
        return "max_items"

    def execute(self, attribute_path: str, values: List[Any], max_count: int) -> List[ValidationResult]:
        if not values:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    True,
                    f"Attribute '{attribute_path}' is missing (max_items check skipped)",
                )
            ]

        if any(v is None for v in values):
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    True,
                    f"Attribute '{attribute_path}' is null (max_items check skipped)",
                )
            ]

        all_passed = True
        for value in values:
            if isinstance(value, list):
                if len(value) > max_count:
                    all_passed = False
                    break

        passed = all_passed

        if passed:
            message = f"Attribute '{attribute_path}' has at most {max_count} items"
        else:
            message = f"Attribute '{attribute_path}' has more than {max_count} items"

        return [ValidationResult("", attribute_path, self.check_type, passed, message)]
