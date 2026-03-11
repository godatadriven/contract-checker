"""List length validation checks."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class MinItemsCheck(Check):
    """Check if list has minimum number of items"""

    @property
    def check_type(self) -> str:
        return "min_items"

    def execute(
        self,
        attribute_path: str,
        path_value_pairs: List[tuple[str, Any]],
        min_count: int,
    ) -> List[ValidationResult]:
        if not path_value_pairs:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    False,
                    f"Attribute '{attribute_path}' is missing, expected at least "
                    f"{min_count} items",
                )
            ]

        # Check each value individually and report failures with specific paths
        results = []
        for actual_path, value in path_value_pairs:
            if value is None:
                results.append(
                    ValidationResult(
                        "",
                        actual_path,
                        self.check_type,
                        False,
                        f"Attribute '{actual_path}' is missing, expected at least "
                        f"{min_count} items",
                    )
                )
            elif isinstance(value, list):
                if len(value) < min_count:
                    results.append(
                        ValidationResult(
                            "",
                            actual_path or attribute_path,
                            self.check_type,
                            False,
                            f"Attribute '{actual_path or attribute_path}' has {len(value)} items, "
                            f"expected at least {min_count} items",
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            "",
                            actual_path or attribute_path,
                            self.check_type,
                            True,
                            f"Attribute '{actual_path or attribute_path}' has at least {min_count} items",
                        )
                    )
            else:
                # If it's not a list but we expect min_items, that's a failure
                results.append(
                    ValidationResult(
                        "",
                        actual_path or attribute_path,
                        self.check_type,
                        False,
                        f"Attribute '{actual_path or attribute_path}' is not a list, "
                        f"expected at least {min_count} items",
                    )
                )

        return results


class MaxItemsCheck(Check):
    """Check if list does not exceed maximum number of items"""

    @property
    def check_type(self) -> str:
        return "max_items"

    def execute(
        self,
        attribute_path: str,
        path_value_pairs: List[tuple[str, Any]],
        max_count: int,
    ) -> List[ValidationResult]:
        if not path_value_pairs:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    True,
                    f"Attribute '{attribute_path}' is missing "
                    f"(max_items check skipped)",
                )
            ]

        # Check each value individually and report failures with specific paths
        results = []
        for actual_path, value in path_value_pairs:
            if value is None:
                # Attribute is missing — max_items is vacuously satisfied
                results.append(
                    ValidationResult(
                        "",
                        actual_path,
                        self.check_type,
                        True,
                        f"Attribute '{actual_path}' is missing (max_items check skipped)",
                    )
                )
            elif isinstance(value, list):
                if len(value) > max_count:
                    results.append(
                        ValidationResult(
                            "",
                            actual_path or attribute_path,
                            self.check_type,
                            False,
                            f"Attribute '{actual_path or attribute_path}' has {len(value)} items, "
                            f"expected at most {max_count} items",
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            "",
                            actual_path or attribute_path,
                            self.check_type,
                            True,
                            f"Attribute '{actual_path or attribute_path}' has at most {max_count} items",
                        )
                    )
            else:
                # Non-list values pass the max_items check
                results.append(
                    ValidationResult(
                        "",
                        actual_path or attribute_path,
                        self.check_type,
                        True,
                        f"Attribute '{actual_path or attribute_path}' is not a list "
                        f"(max_items check skipped)",
                    )
                )

        return results
