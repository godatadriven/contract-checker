"""At-least-one item check for nested collections."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class AtLeastOneCheck(Check):
    """Check that at least one item in a collection satisfies a key-value condition.

    Use this check when a constraint must hold for *some* (not all) items.
    Point the ``attribute`` path at the **collection**, not a leaf field, and
    provide a single ``attr: val`` pair under ``at_least_one`` as a YAML block
    mapping to match a nested attribute.

    Example — at least one field per model must have ``unique: true``:

    ```yaml
    data_contract_checks:
      - attribute: models.*.fields
        checks:
          - at_least_one:
              unique: true
    ```

    Example — at least one field must be a primary key:

    ```yaml
    data_contract_checks:
      - attribute: models.*.fields
        checks:
          - at_least_one:
              primaryKey: true
    ```

    **Per-expansion semantics.** When the attribute path contains a wildcard
    (e.g. ``models.*.fields``), the check runs once per expanded concrete path
    — once per model in the examples above. Each expansion must independently
    satisfy the condition; results are *not* aggregated across matches. Use a
    non-wildcarded path if you want a single pooled verdict instead.
    """

    @property
    def check_type(self) -> str:
        return "at_least_one"

    def execute(
        self,
        attribute_path: str,
        values: List[Any],
        check_value: Any,  # noqa: ANN401
    ) -> List[ValidationResult]:
        """Execute the at-least-one validation.

        :param attribute_path: The dot-notation path to the collection being checked.
        :param values: List of values found at the attribute path. Typically a list
            containing one dict (a mapping of named items, e.g. fields in a model).
        :param check_value: Either a mapping with a single ``attr: val`` entry
            — meaning at least one child object must have ``attr == val`` — or a
            scalar, meaning at least one element in ``values`` must equal the
            scalar.
        :return: A list containing a single :class:`ValidationResult`.
        """
        if not values:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    False,
                    f"Attribute '{attribute_path}' is missing; cannot verify at_least_one condition",
                )
            ]

        if isinstance(check_value, dict):
            required_attr, required_val = next(iter(check_value.items()))
            found = False
            for value in values:
                if isinstance(value, dict):
                    for item in value.values():
                        if isinstance(item, dict) and item.get(required_attr) == required_val:
                            found = True
                            break
                if found:
                    break

            if found:
                message = (
                    f"Attribute '{attribute_path}' contains at least one item with '{required_attr}: {required_val}'"
                )
            else:
                message = f"Attribute '{attribute_path}' has no items with '{required_attr}: {required_val}'"
        else:
            found = any(v == check_value for v in values if v is not None)
            if found:
                message = f"Attribute '{attribute_path}' contains at least one value equal to '{check_value}'"
            else:
                message = f"Attribute '{attribute_path}' has no values equal to '{check_value}'"

        return [ValidationResult("", attribute_path, self.check_type, found, message)]
