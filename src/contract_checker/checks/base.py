"""Abstract base classes for validation checks."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from .models import ValidationResult


class Check(ABC):
    """Abstract base class for all validation check types.

    This class defines the interface that all validation checks must implement.
    Custom checks can be created by subclassing this class and implementing
    the required abstract methods.

    **Missing vs null.** Every check follows the same rule:

    - An attribute that is *absent* (``values == []``) is skipped by every
      check except ``required``: return no results. Presence is enforced
      only by ``required``, so a field can be present in some contracts and
      absent in others.
    - An attribute that is *present but null* (``None`` in ``values``) fails
      every check. Use :meth:`null_result` so the message is consistent.
    - ``None`` elements inside a list or mapping value also fail. Use
      :meth:`null_elements_result`.

    To create a custom check:

    1. Subclass :class:`Check`
    2. Implement the :meth:`execute` method with your validation logic
    3. Implement the :attr:`check_type` property to return a unique identifier
    4. Register the check with the :class:`CheckRegistry`

    Example custom check implementation::

        from contract_checker.checks.base import Check
        from contract_checker.checks.models import ValidationResult

        class MyCustomCheck(Check):
            @property
            def check_type(self) -> str:
                return "my_custom_check"

            def execute(self, attribute_path, values, check_value):
                # Your validation logic here
                passed = all(v is not None for v in values)
                message = "Passed" if passed else "Failed"
                return [
                    ValidationResult(
                        "", attribute_path, self.check_type, passed, message
                    )
                ]
    """

    @abstractmethod
    def execute(
        self,
        field_path: str,
        values: List[Any],
        check_value: Any,  # noqa: ANN401
    ) -> List[ValidationResult]:
        """Execute the validation check.

        :param field_path: The dot-notation path to the attribute being checked
            (e.g., ``"info.title"`` or ``"models.*.fields"``).
        :param values: List of values found at the attribute path in the data contract.
        :param check_value: The configuration value for this check, as specified
            in the checks configuration file.
        :return: List of :class:`ValidationResult` objects representing the
            outcome of the validation. The ``contract_file`` field will be
            populated by the validator after execution.
        """
        pass

    @property
    @abstractmethod
    def check_type(self) -> str:
        """Return the unique identifier for this check type.

        :return: A string identifier used to reference this check in configuration
            files (e.g., ``"required"``, ``"pattern"``, ``"accepted_values"``).
        """
        pass

    def null_result(self, attribute_path: str) -> ValidationResult:
        """Return the standard failing result for a present-but-null attribute.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :return: A failing :class:`ValidationResult` saying the attribute is null.
        """
        return ValidationResult(
            "",
            attribute_path,
            self.check_type,
            False,
            f"Attribute '{attribute_path}' is null",
        )

    def null_elements_result(
        self,
        attribute_path: str,
        count: int,
        keys: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Return the standard failing result for null elements inside a value.

        :param attribute_path: The dot-notation path to the attribute being checked.
        :param count: How many ``None`` elements were found.
        :param keys: For mappings, the keys whose values are ``None``; these
            are listed in the message.
        :return: A failing :class:`ValidationResult`.
        """
        message = f"Attribute '{attribute_path}' contains {count} null element(s)"
        if keys:
            message += f": {', '.join(keys)}"
        return ValidationResult("", attribute_path, self.check_type, False, message)
