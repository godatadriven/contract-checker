from contract_checker.checks import DataContractValidator
from contract_checker.contract.contract_base import Contract


def validate_contracts(
    contracts: list[Contract], checks_config_path: str, summary_only: bool = False
) -> None:
    """
    Validate data contracts against the provided checks configuration.

    Args:
        contracts (list[Contract]): List of data contract objects to validate.
        checks_config_path (str): Path to the checks configuration file.
        summary_only (bool): If True, only print the failed checks summary table.

    Returns:
        None
    """
    validator = DataContractValidator(checks_config_path)
    report = validator.validate(contracts)
    validator.print_results(report, verbose=True, summary_only=summary_only)
