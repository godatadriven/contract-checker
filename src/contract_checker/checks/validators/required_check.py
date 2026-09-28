"""Required field validation check."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class RequiredCheck(Check):
    """Check if a required field exists and is not null.

    The identifier for this check type is (``"required"``).

    Example configuration in ``data-contract-checks.yml``:

    ``` yaml

        data_contract_checks:
          - attribute: info.title
            checks:
              - required: true

          - attribute: models.*.fields.*.description
            checks:
              - required: true
    ```
    """

    @property
    def check_type(self) -> str:
        """Return the check type identifier.

        :return: The string ``"required"``.
        """
        return "required"

    # required reports null values itself ("Required attribute ... is null"),
    # and required: false must stay a no-op even when the value is null.
    handles_nulls = True

    def execute(self, attribute_path: str, values: List[Any], check_value: bool) -> List[ValidationResult]:
        """Execute the required field validation.

        :param attribute_path: The dot-notation path to the attribute being checked
            (e.g., ``"info.title"`` or ``"models.*.fields.*.name"``).
        :param values: List of values found at the attribute path.
        :param check_value: If ``True``, the attribute must exist and be non-null.
            If ``False`` (or null), the check does nothing and returns no results.
        :return: A list containing a single :class:`ValidationResult` indicating
            whether the check passed or failed, or an empty list when
            ``check_value`` is falsy.
        """
        if not check_value:
            # required: false documents that a field is optional; it checks
            # nothing, so it must not add a (misleading) passing result.
            return []

        if not values:
            passed = False
            message = f"Required attribute '{attribute_path}' is missing"
        elif any(v is None for v in values):
            passed = False
            message = f"Required attribute '{attribute_path}' is null"
        else:
            passed = True
            message = f"Attribute '{attribute_path}' is present"

        return [ValidationResult("", attribute_path, self.check_type, passed, message)]
