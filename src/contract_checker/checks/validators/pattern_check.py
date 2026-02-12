"""Pattern matching validation check."""

import re
from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class PatternCheck(Check):
    """Check if attribute values match a regular expression pattern.

    This validator ensures that attribute values conform to a specified regex pattern.
    It is useful for enforcing naming conventions, format requirements, or other
    string-based constraints on data contract attributes.

    The pattern matching uses Python's :func:`re.match`, which matches from the
    beginning of the string. Use ``.*`` prefix if you need to match anywhere in
    the string.

    :cvar check_type: The identifier for this check type (``"pattern"``).

    Example configuration in ``data-contract-checks.yml``:

    .. code-block:: yaml

        data_contract_checks:
          # Ensure title starts with "Orders"
          - attribute: info.title
            checks:
              - pattern: ^Orders

          # Ensure version follows semantic versioning
          - attribute: info.version
            checks:
              - pattern: ^\\d+\\.\\d+\\.\\d+$

          # Ensure field names are snake_case
          - attribute: models.*.fields.*.name
            checks:
              - pattern: ^[a-z][a-z0-9_]*$
    """

    @property
    def check_type(self) -> str:
        """Return the check type identifier.

        :return: The string ``"pattern"``.
        """
        return "pattern"

    def execute(
        self, attribute_path: str, values: List[Any], pattern: str
    ) -> List[ValidationResult]:
        """Execute the pattern matching validation.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param values: List of values found at the attribute path. Each value is
            converted to a string before pattern matching.
        :param pattern: The regular expression pattern to match against.
        :return: A list of :class:`ValidationResult` objects, one for each value
            in the input list. Null values will result in a failed check.
        """
        results = []

        for idx, value in enumerate(values):
            if value is None:
                results.append(
                    ValidationResult(
                        "",
                        attribute_path,
                        self.check_type,
                        False,
                        f"Attribute '{attribute_path}' is null, cannot match "
                        f"pattern '{pattern}'",
                    )
                )
                continue

            value_str = str(value)
            passed = re.match(pattern, value_str) is not None

            if passed:
                message = f"Attribute '{attribute_path}' value '{value_str}' matches "
                f"pattern '{pattern}'"
            else:
                message = (
                    f"Attribute '{attribute_path}' value '{value_str}' does not match "
                    f"pattern '{pattern}'"
                )

            results.append(
                ValidationResult("", attribute_path, self.check_type, passed, message)
            )

        return results
