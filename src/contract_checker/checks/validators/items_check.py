"""List length validation checks."""

from typing import Any, Dict, List, Tuple, Union

from ..base import Check
from ..models import ValidationResult


def _not_a_collection_result(attribute_path: str, check_type: str) -> ValidationResult:
    """Build the failing result for an attribute that is not a collection.

    :param attribute_path: The dot-notation path to the attribute being checked.
    :param check_type: The identifier of the check reporting the failure.
    :return: A failed :class:`ValidationResult`.
    """
    return ValidationResult(
        "",
        attribute_path,
        check_type,
        False,
        f"Attribute '{attribute_path}' is not a list or mapping, cannot apply {check_type}",
    )


def _validate_count_config(check_type: str, check_value: Any) -> None:  # noqa: ANN401
    """Accept only a non-negative integer.

    :raises ValueError: If ``check_value`` is not an integer (booleans are
        rejected too, since ``true`` is not a count) or is negative.
    """
    if isinstance(check_value, bool) or not isinstance(check_value, int) or check_value < 0:
        raise ValueError(f"'{check_type}' expects a non-negative integer, got {check_value!r}")


def _count_items(
    check: Check, attribute_path: str, value: Union[List[Any], Dict[Any, Any]]
) -> Tuple[int, List[ValidationResult]]:
    """Count the non-null items in a list or mapping, reporting null elements.

    :param check: The check reporting any null elements.
    :param attribute_path: The dot-notation path to the attribute being checked.
    :param value: A list, or a mapping of named items (e.g. DCS ``fields``).
    :return: The number of non-null items, and a failing result if any items
        are null (empty otherwise).
    """
    if isinstance(value, dict):
        null_keys = [str(key) for key, item in value.items() if item is None]
        null_results = [check.null_elements_result(attribute_path, len(null_keys), null_keys)] if null_keys else []
        return len(value) - len(null_keys), null_results

    null_count = sum(1 for item in value if item is None)
    null_results = [check.null_elements_result(attribute_path, null_count)] if null_count else []
    return len(value) - null_count, null_results


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

    def validate_config(self, check_value: Any) -> None:  # noqa: ANN401
        """Accept only a non-negative integer. See :func:`_validate_count_config`."""
        _validate_count_config(self.check_type, check_value)

    def execute(self, attribute_path: str, values: List[Any], min_count: int) -> List[ValidationResult]:
        """Execute the minimum items validation.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param values: List of values found at the attribute path. Each value should
            be a list, or a mapping of named items (e.g. DCS ``fields``).
        :param min_count: The minimum number of items required in the list.
        :return: A list of :class:`ValidationResult` objects: one failing result
            per list or mapping with null elements, plus a single count result.
            Null elements are not counted. A value that is not a list or
            mapping fails. An absent attribute (empty ``values``)
            produces no results. Null values are reported by the validator.
        """
        if not values:
            return []

        if not all(isinstance(value, (list, dict)) for value in values):
            return [_not_a_collection_result(attribute_path, self.check_type)]

        results = []
        all_passed = True
        for value in values:
            count, null_results = _count_items(self, attribute_path, value)
            results.extend(null_results)
            if count < min_count:
                all_passed = False

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

    def validate_config(self, check_value: Any) -> None:  # noqa: ANN401
        """Accept only a non-negative integer. See :func:`_validate_count_config`."""
        _validate_count_config(self.check_type, check_value)

    def execute(self, attribute_path: str, values: List[Any], max_count: int) -> List[ValidationResult]:
        """Execute the maximum items validation.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param values: List of values found at the attribute path. Each value should
            be a list, or a mapping of named items (e.g. DCS ``fields``).
        :param max_count: The maximum number of items allowed in the list.
        :return: A list of :class:`ValidationResult` objects: one failing result
            per list or mapping with null elements, plus a single count result.
            Null elements are not counted. A value that is not a list or
            mapping fails. An absent attribute (empty ``values``)
            produces no results. Null values are reported by the validator.
        """
        if not values:
            return []

        if not all(isinstance(value, (list, dict)) for value in values):
            return [_not_a_collection_result(attribute_path, self.check_type)]

        results = []
        all_passed = True
        for value in values:
            count, null_results = _count_items(self, attribute_path, value)
            results.extend(null_results)
            if count > max_count:
                all_passed = False

        if all_passed:
            message = f"Attribute '{attribute_path}' has at most {max_count} items"
        else:
            message = f"Attribute '{attribute_path}' has more than {max_count} items"
        results.append(ValidationResult("", attribute_path, self.check_type, all_passed, message))

        return results
