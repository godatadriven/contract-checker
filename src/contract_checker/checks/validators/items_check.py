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

    def execute(
        self, attribute_path: str, values: List[Any], min_count: int
    ) -> List[ValidationResult]:
        """Execute the minimum items validation.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param values: List of values found at the attribute path. Each value should
            be a list to be validated.
        :param min_count: The minimum number of items required in the list.
        :return: A list containing a single :class:`ValidationResult` indicating
            whether all lists meet the minimum items requirement.
        """
        if not values:
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

    def execute(
        self, attribute_path: str, values: List[Any], max_count: int
    ) -> List[ValidationResult]:
        """Execute the maximum items validation.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param values: List of values found at the attribute path. Each value should
            be a list to be validated.
        :param max_count: The maximum number of items allowed in the list.
        :return: A list containing a single :class:`ValidationResult` indicating
            whether all lists are within the maximum items limit.
        """
        if not values:
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
