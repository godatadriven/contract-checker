import logging
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from contract_checker.checks.check_sample import (
    parse_checks_config,
)
from contract_checker.logger import setup_console_logger
from contract_checker.utils.contract_utils import load_contracts
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

    # Check if config file exists
    # Check if config file is valid YAML
    # load_checks()
    checks_dict = parse_checks_config(config_path)

    # Load the contract -> internally identify type of contract -> validate contract
    contracts = load_contracts(
        contract_path=contract_path,
        contract_standard=checks_dict.get("data_contract_standard"),
    )
    print(len(contracts))

    # validate_contracts(contract_path, checks_dict)

    raise typer.Exit()


if __name__ == "__main__":
    app()
