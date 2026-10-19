"""Accepted values validation check."""

from typing import Any, List, Sequence, Union

from ..base import Check
from ..models import ValidationResult

# The JSON Schema scalar types (string, number/integer, boolean). Nested lists,
# mappings and null are not values and are rejected by ``validate_config``.
# Dates need no type of their own: YAML loading keeps them as strings.
_SCALAR_TYPES = (str, int, float, bool)
_Scalar = Union[str, int, float, bool]

_JSON_TYPE_NAMES = {bool: "boolean", int: "integer", float: "number", str: "string"}


def _same_value(a: Any, b: Any) -> bool:  # noqa: ANN401
    """Compare two values the way JSON Schema types them.

    ``==`` already keeps strings apart from numbers (``"255" != 255``) and
    treats ``1`` and ``1.0`` as the same number. Booleans need their own check:
    ``bool`` is a subclass of ``int`` in Python, so ``True == 1``, but JSON
    Schema keeps ``boolean`` and ``integer`` apart.
    """
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and bool(a == b)
    return bool(a == b)


def _json_type_name(value: Any) -> str:  # noqa: ANN401
    """Name ``value``'s type the way JSON Schema and ``--lint`` do."""
    return _JSON_TYPE_NAMES.get(type(value), type(value).__name__)


class AcceptedValuesCheck(Check):
    """Check if attribute values are within a list of accepted values.

    Both string and list attributes are supported.

    - For string attributes, the value is checked directly against the accepted values.
    - For list attributes, each item in the list is checked against the accepted values,
    and a validation result is generated for each item.

    Values are compared with their type, the same way ``--lint`` checks them
    against the contract schema: a contract value ``255`` matches an accepted
    value of ``255`` (or ``255.0``) but not ``"255"``, and ``true`` matches
    ``true`` but not ``"true"`` or ``1``. Unquoted dates are strings on both
    sides, so ``2024-01-01`` matches ``2024-01-01`` and ``"2024-01-01"``.

    The identifier for this check type (``"accepted_values"``).

    Example configuration in ``data-contract-checks.yml``:

    ```yaml

        data_contract_checks:
          # Single value - ensure version is accepted
          - attribute: info.version
            checks:
              - accepted_values: 1.0.0

          # Multiple accepted values for tags (list attribute)
          - attribute: tags
            checks:
              - accepted_values:
                  - production
                  - staging
                  - development

          # Ensure server types are valid
          - attribute: servers.type
            checks:
              - accepted_values:
                  - s3
                  - gcs
                  - azure_blob
    ```
    """

    @property
    def check_type(self) -> str:
        """Return the check type identifier.

        :return: The string ``"accepted_values"``.
        """
        return "accepted_values"

    def validate_config(self, check_value: Any) -> None:  # noqa: ANN401
        """Accept a non-empty list of scalar values, or a single scalar value.

        Scalars are strings, numbers and booleans.

        :raises ValueError: If ``check_value`` is a mapping, null or an empty
            list, or a list containing a non-scalar entry (a nested list, a
            mapping or null).
        """
        if isinstance(check_value, _SCALAR_TYPES):
            return
        if not isinstance(check_value, list) or not check_value:
            raise ValueError(f"'accepted_values' expects a non-empty list of values, got {check_value!r}")
        for entry in check_value:
            if not isinstance(entry, _SCALAR_TYPES):
                raise ValueError(f"'accepted_values' entries must be strings, numbers or booleans, got {entry!r}")

    def execute(
        self,
        attribute_path: str,
        value_list: List[Any],
        accepted_values: Union[_Scalar, Sequence[_Scalar]],
    ) -> List[ValidationResult]:
        """Execute the accepted values validation.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param value_list: List of values found at the attribute path. Each value
            can be a string or a list of strings.
        :param accepted_values: The values that are considered valid: a list of
            scalars, or a single scalar as shorthand for a one-item list.
        :return: A list of :class:`ValidationResult` objects. When the attribute
            contains a list, a result is generated for each item in that list.
            Null elements in a list fail. An absent attribute (empty
            ``value_list``) produces no results. Null values are reported by
            the validator.
        """
        # validate_config allows a single scalar as shorthand for a one-item
        # list. Wrapping it keeps the test a membership test, not a substring
        # test ('act' must not pass against accepted_values: active).
        if isinstance(accepted_values, _SCALAR_TYPES):
            accepted_values = [accepted_values]

        results = []
        for value in value_list:
            if isinstance(value, str):
                items = [value]
            elif isinstance(value, list):
                # Filter out null elements and report them explicitly
                items = [v for v in value if v is not None]
                null_count = len(value) - len(items)
                if null_count:
                    results.append(self.null_elements_result(attribute_path, null_count))
            else:
                items = [value]

            for item in items:
                passed = any(_same_value(item, accepted) for accepted in accepted_values)

                if passed:
                    message = f"Attribute '{attribute_path}' value '{item}' is in the list of accepted values"
                else:
                    message = (
                        f"Attribute '{attribute_path}' value '{item}' "
                        f"is not in the list of accepted values: '{accepted_values}'"
                    ) + self._type_mismatch_hint(item, accepted_values)

                results.append(ValidationResult("", attribute_path, self.check_type, passed, message))

        return results

    @staticmethod
    def _type_mismatch_hint(item: Any, accepted_values: Sequence[_Scalar]) -> str:  # noqa: ANN401
        """Explain a failure where the value is listed, but with another type.

        A contract ``255`` against ``accepted_values: ["255"]``, or ``true``
        against ``["true"]``, reads as the same value but is not: point at the
        quotes in the checks config rather than leave the failure unexplained.
        """
        for accepted in accepted_values:
            if str(accepted).lower() == str(item).lower():
                return (
                    f" (type mismatch: the contract has {_json_type_name(item)} {item!r}, the checks config has "
                    f"{_json_type_name(accepted)} {accepted!r}; add or remove the quotes in the checks config)"
                )
        return ""
