"""Abstract base classes for validation checks."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar, List, Optional

from .models import ValidationResult


class Check(ABC):
    """Abstract base class for all validation check types.

    This class defines the interface that all validation checks must implement.
    Custom checks can be created by subclassing this class and implementing
    the required abstract methods.

    **Missing vs null.** The validator applies the same rule to every check:

    - An attribute that is *absent* (``values == []``) is skipped by every
      check except ``required``: return no results. Presence is enforced
      only by ``required``, so a field can be present in some contracts and
      absent in others.
    - An attribute that is *present but null* fails every check. The
      validator handles this before calling :meth:`execute`: it records
      :meth:`null_result` for each ``None`` and passes only the non-null
      values on, so :meth:`execute` never receives a top-level ``None``.
      A check that must inspect nulls itself (such as ``required``) sets
      :attr:`handles_nulls` to ``True`` and receives ``values`` unchanged.
    - ``None`` elements inside a list or mapping value also fail. Use
      :meth:`null_elements_result`.

    To create a custom check:

    1. Subclass :class:`Check`
    2. Implement the :meth:`execute` method with your validation logic
    3. Implement the :attr:`check_type` property to return a unique identifier
    4. Optionally override :meth:`validate_config` to reject malformed
       configuration up front, so it is reported once as a config error
       rather than against every contract
    5. Register the check with the :class:`CheckRegistry`

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

    #: If ``True``, :meth:`execute` receives top-level ``None`` values as-is
    #: and is responsible for reporting them. If ``False`` (the default), the
    #: validator reports them with :meth:`null_result` and filters them out.
    handles_nulls: ClassVar[bool] = False

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
        :param values: List of values found at the attribute path in the data
            contract. Top-level ``None`` values are removed by the validator
            unless :attr:`handles_nulls` is ``True``.
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

    def validate_config(self, check_value: Any) -> None:  # noqa: ANN401
        """Validate this check's configuration value before any contract is read.

        The validator calls this once per check entry in the configuration.
        A malformed value is a configuration error, so it is reported once,
        naming the entry, instead of failing every contract file. The default
        accepts anything; override it to reject values :meth:`execute` cannot
        handle.

        :param check_value: The configuration value for this check, as specified
            in the checks configuration file.
        :raises ValueError: With a message describing what is wrong with the value.
        """
        return None

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
