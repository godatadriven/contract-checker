import logging
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from contract_checker.checks.check_sample import (
    parse_checks_config,
)
from contract_checker.contract.data_contract_parser import load_contracts
from contract_checker.logger import setup_console_logger
from contract_checker.version import version

app = typer.Typer()


def version_callback(value: bool) -> None:
    """A CLI tool for checking data contracts."""
    if value:
        print(f"{version()}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    config_path: Annotated[
        Path, typer.Argument(help="The location of the data contract check file.")
    ] = Path("data-contract-checks.yml"),
    severity: Annotated[
        str,
        typer.Option(help="The severity level of the checks. Can be 'error' or 'warn'"),
    ] = "error",
    verbosity: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enables verbose output.")
    ] = False,
    contract_path: Annotated[
        Optional[Path], typer.Option(help="The location of the data contract file.")
    ] = Path("tests/fixtures/dcs/"),
) -> None:
    """A CLI tool for checking data contracts."""
    setup_console_logger(verbosity)
    if verbosity:
        logging.debug("Verbose mode is enabled.")
    logging.info(f"Running contract-checker version: {version}")
    logging.debug(f"Configuration path: {config_path}")
    logging.debug(f"Contract path: {contract_path}")
    logging.debug(f"Severity level: {severity}")

    # Parse the config file
    checks_dict = parse_checks_config(config_path)
    # print(f"Parsed Checks: {checks}")

    ## Check if config file exists
    ## Check if config file is valid YAML

    # Parse the data contract specification
    # spec_version = parse_field(checks, "data_contract_standard_version")
    # spec_kind = parse_field(checks, "data_contract_standard")
    # # Parse the data contracts

    # # # Load the contract

    contracts = load_contracts(
        contract_directory_path=contract_path,
        contract_standard=checks_dict.get("data_contract_standard"),
    )
    print(contracts)
    # contract = parse_yml_to_dict(file_path=contract_path)
    # parse_yml_to_dict(file_path=contract_path)

    # # Identify type of contract
    # spec_version, spec_kind = parse_specification_from_contract(
    #   contract_content=contract,
    #   checks_dict=checks_dict
    # )
    # print(f"Specification Version: {spec_version}, Specification Kind: {spec_kind}")

    # # Parse the contract
    # if spec_kind == "dataContractSpecification":
    #     # Initialize the DataContractSpecification contract
    #     data_contract = DataContract(
    #         contract_path=contract_path,
    #         contract_content=contract,
    #         version=spec_version,
    #         contract_specification=spec_kind,
    #     )
    # elif spec_kind == "DataContract":
    #     # Initialize the OpenDataContractSpecification contract
    #     pass
    # else:
    #     raise ValueError(f"Unsupported contract specification kind: {spec_kind}")
    # # print(f"Initialized Contract: {data_contract}")

    # # Compare contracts vs. checks
    # for check in checks_dict.get("data_contract_checks"):
    #     result = check_if_field_present(
    #         contract_content=data_contract.contract_content,
    #         check_content=check,
    #     )
    #     print(f"Check: {check.get('field')}, Result: {result}")
    #     # Remove break to perform all checks``
    #     break
    # # Return results

    raise typer.Exit()


if __name__ == "__main__":
    app()
