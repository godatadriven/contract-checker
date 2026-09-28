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
        :param check_value: A mapping with exactly one ``attr: val`` entry — at
            least one child object in the collection must have ``attr == val``.
            Multi-key mappings, empty mappings, and non-mapping values are
            rejected with a failing result.
        :return: A list of :class:`ValidationResult` objects: a failing result
            for null items inside the collection, plus a single verdict. An
            absent attribute (empty ``values``) produces no results. Null
            collections are reported by the validator.
        """
        if not values:
            return []

        if not isinstance(check_value, dict) or len(check_value) != 1:
            return [
                ValidationResult(
                    "",
                    attribute_path,
                    self.check_type,
                    False,
                    f"Attribute '{attribute_path}' at_least_one check requires a "
                    f"single-key mapping (e.g. {{unique: true}}); got: {check_value!r}",
                )
            ]

        required_attr, required_val = next(iter(check_value.items()))
        results = []
        found = False
        for value in values:
            if isinstance(value, dict):
                null_keys = [str(key) for key, item in value.items() if item is None]
                if null_keys:
                    results.append(self.null_elements_result(attribute_path, len(null_keys), null_keys))
                for item in value.values():
                    if isinstance(item, dict) and item.get(required_attr) == required_val:
                        found = True

        if found:
            message = f"Attribute '{attribute_path}' contains at least one item with '{required_attr}: {required_val}'"
        else:
            message = f"Attribute '{attribute_path}' has no items with '{required_attr}: {required_val}'"

        results.append(ValidationResult("", attribute_path, self.check_type, found, message))
        return results
