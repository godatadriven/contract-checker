"""List length validation checks."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class MinItemsCheck(Check):
    """Check if a list attribute has at least a minimum number of items.

    The identifier for this check type (``"min_items"``).

    Example configuration in ``data-contract-checks.yml``:

    ``` yaml

        data_contract_checks:
          # Ensure each model has at least one field
          - attribute: models.*.fields
            checks:
              - min_items: 1

          # Ensure at least 3 examples are provided
          - attribute: models.*.fields.*.examples
            checks:
              - min_items: 3
    ```
    """

    @property
    def check_type(self) -> str:
        """Return the check type identifier.

        :return: The string ``"min_items"``.
        """
        return "min_items"

    def execute(self, attribute_path: str, values: List[Any], min_count: int) -> List[ValidationResult]:
        """Execute the minimum items validation.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param values: List of values found at the attribute path. Each value should
            be a list to be validated.
        :param min_count: The minimum number of items required in the list.
        :return: A list of :class:`ValidationResult` objects: one failing result
            per null value or list with null elements, plus a single count
            result covering the non-null values. Null elements are not counted.
            An absent attribute (empty ``values``) produces no results.
        """
        if not values:
            return []

        results = []
        counted = False
        all_passed = True
        for value in values:
            if value is None:
                results.append(self.null_result(attribute_path))
                continue

            counted = True
            if isinstance(value, list):
                items = [v for v in value if v is not None]
                null_count = len(value) - len(items)
                if null_count:
                    results.append(self.null_elements_result(attribute_path, null_count))
                if len(items) < min_count:
                    all_passed = False
            else:
                # If it's not a list but we expect min_items, that's a failure
                all_passed = False

        if counted:
            if all_passed:
                message = f"Attribute '{attribute_path}' has at least {min_count} items"
            else:
                message = f"Attribute '{attribute_path}' has fewer than {min_count} items"
            results.append(ValidationResult("", attribute_path, self.check_type, all_passed, message))

        return results


class MaxItemsCheck(Check):
    """Check if a list attribute does not exceed a maximum number of items.

    The identifier for this check type (``"max_items"``).

    Example configuration in ``data-contract-checks.yml``:

    .. code-block:: yaml

        data_contract_checks:
          # Limit tags to maximum 5 items
          - attribute: tags
            checks:
              - max_items: 5

          # Limit examples to reasonable number
          - attribute: models.*.fields.*.examples
            checks:
              - max_items: 10
    """

    @property
    def check_type(self) -> str:
        """Return the check type identifier.

        :return: The string ``"max_items"``.
        """
        return "max_items"

    def execute(self, attribute_path: str, values: List[Any], max_count: int) -> List[ValidationResult]:
        """Execute the maximum items validation.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param values: List of values found at the attribute path. Each value should
            be a list to be validated.
        :param max_count: The maximum number of items allowed in the list.
        :return: A list of :class:`ValidationResult` objects: one failing result
            per null value or list with null elements, plus a single count
            result covering the non-null values. Null elements are not counted.
            An absent attribute (empty ``values``) produces no results.
        """
        if not values:
            return []

        results = []
        counted = False
        all_passed = True
        for value in values:
            if value is None:
                results.append(self.null_result(attribute_path))
                continue

            counted = True
            if isinstance(value, list):
                items = [v for v in value if v is not None]
                null_count = len(value) - len(items)
                if null_count:
                    results.append(self.null_elements_result(attribute_path, null_count))
                if len(items) > max_count:
                    all_passed = False

        if counted:
            if all_passed:
                message = f"Attribute '{attribute_path}' has at most {max_count} items"
            else:
                message = f"Attribute '{attribute_path}' has more than {max_count} items"
            results.append(ValidationResult("", attribute_path, self.check_type, all_passed, message))

        return results
