"""Validation check registry system."""

from typing import Dict, List

from .base import Check
from .validators.accepted_values_check import AcceptedValuesCheck
from .validators.at_least_one_check import AtLeastOneCheck
from .validators.exactly_one_check import ExactlyOneCheck
from .validators.items_check import MaxItemsCheck, MinItemsCheck
from .validators.pattern_check import PatternCheck
from .validators.required_check import RequiredCheck


class CheckRegistry:
    """Registry for all available check types"""

    def __init__(self) -> None:
        self._checks: Dict[str, Check] = {}
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register all default check types"""
        default_checks = [
            RequiredCheck(),
            PatternCheck(),
            AcceptedValuesCheck(),
            MinItemsCheck(),
            MaxItemsCheck(),
            AtLeastOneCheck(),
            ExactlyOneCheck(),
        ]

        for check in default_checks:
            self.register(check)

    def register(self, check: Check) -> None:
        """Register a new check type"""
        self._checks[check.check_type] = check

    def get(self, check_type: str) -> Check:
        """Get a check by type"""
        if check_type not in self._checks:
            raise ValueError(f"Unknown check type: {check_type}")
        return self._checks[check_type]

    def list_available(self) -> List[str]:
        """List all available check types"""
        return list(self._checks.keys())
