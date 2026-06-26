"""Pattern matching validation check."""

import re
from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class PatternCheck(Check):
    """Check if value matches a regex pattern.

    Uses ``re.match``, which anchors at the start of the string but not the
    end. Callers must fully anchor their patterns (``^...$``) if they want
    whole-string matching — e.g. ``r"\\d+"`` will accept ``"123abc"`` as a
    match. To enforce full-string matching implicitly, switch this to
    ``re.fullmatch``.
    """

    @property
    def check_type(self) -> str:
        return "pattern"

    def execute(self, attribute_path: str, values: List[Any], pattern: str) -> List[ValidationResult]:
        results = []

        for idx, value in enumerate(values):
            if value is None:
                results.append(
                    ValidationResult(
                        "",
                        attribute_path,
                        self.check_type,
                        False,
                        f"Attribute '{attribute_path}' is null, cannot match pattern {pattern}",
                    )
                )
                continue

            value_str = str(value)
            passed = re.match(pattern, value_str) is not None

            if passed:
                message = f"Attribute '{attribute_path}' value '{value_str}' matches pattern '{pattern}'"
            else:
                message = f"Attribute '{attribute_path}' value '{value_str}' does not match pattern '{pattern}'"

            results.append(ValidationResult("", attribute_path, self.check_type, passed, message))

        return results
