from contract_checker.checks import DataContractValidator
from contract_checker.checks.models import ContractValidationReport
from contract_checker.contract.contract_base import Contract


def validate_contracts(
    contracts: list[Contract], checks_dict: dict, verbose: bool = False
) -> list[ContractValidationReport]:
    """
    Validate data contracts against the provided checks configuration.

    Args:
        contracts (list[Contract]): List of data contract objects to validate.
        checks_dict (dict): Dictionary containing the checks configuration.
        verbose (bool): If True, print detailed results for all checks; if False, only print failures.
    Returns:
        list[ContractValidationReport]: One report per validated contract, so
        callers (e.g. the CLI) can act on the outcome after results are printed.
    """
    validator = DataContractValidator(checks_dict)
    reports: list[ContractValidationReport] = validator.validate(contracts)
    validator.print_results(reports, verbose=verbose)
    return reports
