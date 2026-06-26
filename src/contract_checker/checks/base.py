"""Abstract base classes for validation checks."""

from abc import ABC, abstractmethod
from typing import Any, List

from .models import ValidationResult


class Check(ABC):
    """Abstract base class for all validation check types.

    This class defines the interface that all validation checks must implement.
    Custom checks can be created by subclassing this class and implementing
    the required abstract methods.

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
