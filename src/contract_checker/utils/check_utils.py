from contract_checker.checks.models import ContractValidationReport
from contract_checker.contract.contract_base import Contract


def validate_contracts(
    contracts: list[Contract], checks_dict: dict, output_mode: str = "failures"
) -> list[ContractValidationReport]:
    """
    Validate data contracts against the provided checks configuration.

    Args:
        contracts (list[Contract]): List of data contract objects to validate.
        checks_dict (dict): Dictionary containing the checks configuration.
        output_mode (str): How much of the report to print: 'summary', 'failures'
            (default), or 'full'. See ValidationReporter.print_results.
    Returns:
        list[ContractValidationReport]: One report per validated contract, so
        callers (e.g. the CLI) can act on the outcome after results are printed.
    """
    # Imported here rather than at module level to break the circular import
    # checks/__init__ -> validator -> utils/__init__ -> check_utils -> validator.
    from contract_checker.checks.validator import DataContractValidator

    validator = DataContractValidator(checks_dict)
    reports: list[ContractValidationReport] = validator.validate(contracts)
    validator.print_results(reports, output_mode=output_mode)
    return reports
