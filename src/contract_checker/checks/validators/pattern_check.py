"""Pattern matching validation check."""

import re
from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class PatternCheck(Check):
    """Check if attribute values match a regular expression pattern.

    The identifier for this check type is (``"pattern"``).

    Example configuration in ``data-contract-checks.yml``:

    ``` yaml

        data_contract_checks:
          # Ensure title starts with "Contract"
          - attribute: info.title
            checks:
              - pattern: ^Contract

          # Ensure version follows semantic versioning
          - attribute: info.version
            checks:
              - pattern: ^\\d+\\.\\d+\\.\\d+$

          # Ensure field names are snake_case
          - attribute: models.*.fields.*.name
            checks:
              - pattern: ^[a-z][a-z0-9_]*$
    ```

    To enforce full-string matching implicitly, switch this to ``re.fullmatch``.
    """

    @property
    def check_type(self) -> str:
        """Return the check type identifier.

        :return: The string ``"pattern"``.
        """
        return "pattern"

    def execute(self, attribute_path: str, values: List[Any], pattern: str) -> List[ValidationResult]:
        """Execute the pattern matching validation.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param values: List of values found at the attribute path. Each value is
            converted to a string before pattern matching.
        :param pattern: The regular expression pattern to match against.
        :return: A list of :class:`ValidationResult` objects, one for each value
            in the input list. A null value fails; an absent attribute
            (empty ``values``) produces no results, since presence is
            enforced by the ``required`` check.
        """
        results = []

        for value in values:
            if value is None:
                results.append(self.null_result(attribute_path))
                continue

            value_str = str(value)
            passed = re.match(pattern, value_str) is not None

            if passed:
                message = f"Attribute '{attribute_path}' value '{value_str}' matches pattern '{pattern}'"
            else:
                message = f"Attribute '{attribute_path}' value '{value_str}' does not match pattern '{pattern}'"

            results.append(ValidationResult("", attribute_path, self.check_type, passed, message))

        return results
