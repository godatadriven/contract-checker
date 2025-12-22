"""Abstract base classes for validation checks."""
from abc import ABC, abstractmethod
from typing import Any, List

from .models import ValidationResult


class Check(ABC):
    """Abstract base class for all check types"""

    @abstractmethod
    def execute(
        self,
        field_path: str,
        values: List[Any],
        check_value: Any,  # noqa: ANN401
    ) -> List[ValidationResult]:
        """
        Execute the check

        Args:
            field_path: The field path being checked
            values: List of values to check
            check_value: The check configuration value

        Returns:
            List of ValidationResult objects (without contract_file,
            to be added by validator)
        """
        pass

    @property
    @abstractmethod
    def check_type(self) -> str:
        """Return the check type identifier"""
        pass
