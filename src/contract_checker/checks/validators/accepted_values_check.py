"""Accepted values validation check."""

from typing import Any, List, Sequence, Union

from ..base import Check
from ..models import ValidationResult

# Config values are compared by their string form, so a YAML ``1`` and a YAML
# ``"1"`` are the same accepted value. Nested lists, mappings and null are not
# values and are rejected by ``validate_config``.
_SCALAR_TYPES = (str, int, float, bool)
_Scalar = Union[str, int, float, bool]


class AcceptedValuesCheck(Check):
    """Check if attribute values are within a list of accepted values.

    Both string and list attributes are supported.

    - For string attributes, the value is checked directly against the accepted values.
    - For list attributes, each item in the list is checked against the accepted values,
    and a validation result is generated for each item.

    Values are compared by their string form: a contract value ``1`` matches an
    accepted value of ``1`` or ``"1"``, and ``true`` matches ``true`` or ``"true"``
    (YAML booleans render as ``True``/``False``). ``1.0`` and ``1`` are different
    values.

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
        # list. Normalise both sides to their string form so ``in`` is a
        # membership test, not a substring test ('act' must not pass against
        # accepted_values: active), and a YAML ``1`` matches a contract ``1``
        # (the contract side was always stringified; the config side was not).
        if isinstance(accepted_values, _SCALAR_TYPES):
            accepted_values = [accepted_values]
        accepted_strs = [str(v) for v in accepted_values]

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
                item_str = str(item)
                passed = item_str in accepted_strs

                if passed:
                    message = f"Attribute '{attribute_path}' value '{item_str}' is in the list of accepted values"
                else:
                    message = (
                        f"Attribute '{attribute_path}' value '{item_str}' "
                        f"is not in the list of accepted values: '{accepted_values}'"
                    )

                results.append(ValidationResult("", attribute_path, self.check_type, passed, message))

        return results
