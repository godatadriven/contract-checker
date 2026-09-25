"""Exactly-one item check for nested collections."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class ExactlyOneCheck(Check):
    """Check that exactly one item in a collection satisfies a key-value condition.

    Use this check when a constraint must hold for **exactly one** item in a
    collection — not zero, not two, not more. The motivating case is primary
    key enforcement: a model must have exactly one field with
    ``primaryKey: true``; two is a modelling bug.

    Point the ``attribute`` path at the **collection**, not a leaf field, and
    provide a single ``attr: val`` pair under ``exactly_one`` as a YAML block
    mapping to match a nested attribute.

    Example — every model must have exactly one primary key field:

    ```yaml
    data_contract_checks:
      - attribute: models.*.fields
        checks:
          - exactly_one:
              primaryKey: true
    ```

    Example — every model must have exactly one event-time timestamp field:

    ```yaml
    data_contract_checks:
      - attribute: models.*.fields
        checks:
          - exactly_one:
              type: timestamp
    ```

    **Per-expansion semantics.** When the attribute path contains a wildcard
    (e.g. ``models.*.fields``), the check runs once per expanded concrete path
    — once per model in the examples above. Each expansion must independently
    satisfy the condition; results are *not* aggregated across matches. Use a
    non-wildcarded path if you want a single pooled verdict instead.

    **Check-value shape contract.** ``check_value`` must be a single-key
    mapping. Multi-key mappings, empty mappings, and non-mapping values are
    rejected with a failing result.

    | ``check_value``                           | Result                         |
    |-------------------------------------------|--------------------------------|
    | ``{primaryKey: true}``                    | OK — checked                   |
    | ``{primaryKey: true, unique: true}``      | FAIL — multi-key rejected      |
    | ``{}``                                    | FAIL — empty mapping rejected  |
    | ``true`` / ``"unique"`` / ``[...]`` / ``null`` | FAIL — non-mapping rejected |
    """

    @property
    def check_type(self) -> str:
        return "exactly_one"

    def execute(
        self,
        attribute_path: str,
        values: List[Any],
        check_value: Any,  # noqa: ANN401
    ) -> List[ValidationResult]:
        """Execute the exactly-one validation.

        :param attribute_path: The dot-notation path to the collection being checked.
        :param values: List of values found at the attribute path. Typically a list
            containing one dict (a mapping of named items, e.g. fields in a model).
        :param check_value: A single-key mapping ``{attr: val}`` — exactly one
            child object in the collection must have ``attr == val``. Any other
            shape (multi-key mapping, empty mapping, non-mapping) is rejected.
        :return: A list of :class:`ValidationResult` objects: a failing result
            for a null collection or for null items inside it, plus a single
            verdict for the non-null collections. An absent attribute (empty
            ``values``) produces no results.
        """
        if not values:
            return []

        if not isinstance(check_value, dict):
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    False,
                    f"Attribute '{attribute_path}' has invalid exactly_one check_value: "
                    f"expected a single-key mapping, got {type(check_value).__name__}",
                )
            ]

        if len(check_value) != 1:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    False,
                    f"Attribute '{attribute_path}' has invalid exactly_one check_value: "
                    f"expected a single-key mapping, got {len(check_value)} keys",
                )
            ]

        required_attr, required_val = next(iter(check_value.items()))
        results = []
        checked = False
        count = 0
        for value in values:
            if value is None:
                results.append(self.null_result(attribute_path))
                continue

            checked = True
            if isinstance(value, dict):
                null_keys = [str(key) for key, item in value.items() if item is None]
                if null_keys:
                    results.append(self.null_elements_result(attribute_path, len(null_keys), null_keys))
                for item in value.values():
                    if isinstance(item, dict) and item.get(required_attr) == required_val:
                        count += 1

        if not checked:
            return results

        passed = count == 1
        if passed:
            message = f"Attribute '{attribute_path}' contains exactly one item with '{required_attr}: {required_val}'"
        else:
            message = (
                f"Attribute '{attribute_path}' has {count} items with "
                f"'{required_attr}: {required_val}', expected exactly 1"
            )

        results.append(ValidationResult("", attribute_path, self.check_type, passed, message))
        return results
