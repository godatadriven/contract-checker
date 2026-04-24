from contract_checker.checks import DataContractValidator
from contract_checker.contract.contract_base import Contract


def validate_contracts(contracts: list[Contract], checks_dict: dict) -> None:
    """
    Validate data contracts against the provided checks configuration.

    Args:
        contracts (list[Contract]): List of data contract objects to validate.
        checks_dict (dict): Dictionary containing the checks configuration.

    Returns:
        None
    """
    validator = DataContractValidator(checks_dict)
    report = validator.validate(contracts)
    validator.print_results(report, verbose=True)
