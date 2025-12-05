from contract_checker.checks.base_check import DataContractValidator
from contract_checker.contract.contract_base import Contract


def validate_contracts(contracts: list[Contract], checks_config_path: str) -> None:
    """
    Validate data contracts against the provided checks configuration.

    Args:
        contracts (list[Contract]): List of data contract objects to validate.
        checks_config_path (str): Path to the checks configuration file.

    Returns:
        None
    """
    validator = DataContractValidator(checks_config_path)
    report = validator.validate(contracts)
    validator.print_results(report, verbose=True)
