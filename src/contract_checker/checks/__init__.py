"""
Main validation module with backward compatibility.

This module provides the main DataContractValidator class with integrated reporting.
It maintains the same interface as the original monolithic implementation.
"""

from typing import Any, Dict, List, Optional, Union

from .base import Check
from .models import ContractValidationReport
from .registry import CheckRegistry
from .reporting import ValidationReporter
from .validator import DataContractValidator as CoreValidator
from .validators import (
    AcceptedValuesCheck,
    MaxItemsCheck,
    MinItemsCheck,
    PatternCheck,
    RequiredCheck,
)


class DataContractValidator(CoreValidator):
    """
    Enhanced DataContractValidator with integrated reporting capabilities.

    Maintains backward compatibility with the original implementation while
    providing the improved modular structure.
    """

    def __init__(
        self,
        checks_file: str,
        check_registry: Optional[CheckRegistry] = None,
    ) -> None:
        """
        Initialize validator with checks configuration and reporter

        Args:
            checks_file: Path to the checks YAML file
            check_registry: Optional custom CheckRegistry instance
        """
        super().__init__(checks_file, check_registry)
        self.reporter = ValidationReporter()

    def print_results(
        self,
        reports: Union[ContractValidationReport, List[ContractValidationReport]],
        verbose: bool = True,
        summary_only: bool = False,
    ) -> None:
        """
        Print validation results in a readable format

        Delegates to the ValidationReporter for consistent formatting.
        """
        self.reporter.print_results(reports, verbose, summary_only)

    def get_summary(self, reports: List[ContractValidationReport]) -> Dict[str, Any]:
        """
        Get a summary dictionary of validation results

        Delegates to the ValidationReporter for consistent formatting.
        """
        return self.reporter.get_summary(reports)


__all__ = [
    "AcceptedValuesCheck",
    "Check",
    "CheckRegistry",
    "ContractValidationReport",
    "DataContractValidator",
    "MaxItemsCheck",
    "MinItemsCheck",
    "PatternCheck",
    "RequiredCheck",
]
