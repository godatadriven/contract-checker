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

    def execute(
        self, attribute_path: str, values: List[Any], check_value: bool
    ) -> List[ValidationResult]:
        """Execute the required field validation.

        :param attribute_path: The dot-notation path to the attribute being checked
            (e.g., ``"info.title"`` or ``"models.*.fields.*.name"``).
        :param values: List of values found at the attribute path.
        :param check_value: If ``True``, the attribute must exist and be non-null.
            If ``False``, the check is skipped (attribute is optional).
        :return: A list containing a single :class:`ValidationResult` indicating
            whether the check passed or failed.
        """
        if check_value:
            passed = len(values) > 0 and all(v is not None for v in values)
            message = (
                f"Attribute '{attribute_path}' is present"
                if passed
                else f"Required attribute '{attribute_path}' is missing or null"
            )
        else:
            passed = True
            message = f"Attribute '{attribute_path}' is optional"

        return [ValidationResult("", attribute_path, self.check_type, passed, message)]
