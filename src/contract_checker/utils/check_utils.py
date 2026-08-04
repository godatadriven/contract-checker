from typing import Optional

from contract_checker.checks import DataContractValidator
from contract_checker.contract.contract_base import Contract


def validate_contracts(
    contracts: list[Contract],
    checks_dict: dict,
    verbose: bool = False,
    lint: Optional[bool] = None,
) -> None:
    """
    Validate data contracts against the provided checks configuration.

    Args:
        contracts (list[Contract]): List of data contract objects to validate.
        checks_dict (dict): Dictionary containing the checks configuration.
        verbose (bool): If True, print detailed results for all checks; if False, only print failures.
        lint (Optional[bool]): Whether to validate each contract against its JSON Schema.
            When None, falls back to the 'lint' key in the checks config (default off).
    Returns:
        None
    """
    validator = DataContractValidator(checks_dict, lint=lint)
    report = validator.validate(contracts)
    validator.print_results(report, verbose=verbose)
