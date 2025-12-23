"""Data models for validation results and reports."""

from dataclasses import dataclass
from typing import List


@dataclass
class ValidationResult:
    """Represents the result of a validation check"""

    contract_file: str
    attribute: str
    check_type: str
    passed: bool
    message: str


@dataclass
class ContractValidationReport:
    """Summary report for a single contract validation"""

    contract_file: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: List[ValidationResult]

    @property
    def success(self) -> bool:
        return self.failed_checks == 0
