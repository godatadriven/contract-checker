import logging
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

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
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            help="Outputs the version of the contract-checker package.",
        ),
    ] = None,
) -> None:
    """A CLI tool for checking data contracts."""
    setup_console_logger(verbosity)
    if verbosity:
        logging.debug("Verbose mode is enabled.")
    logging.info(f"Running contract-checker version: {version}")
    logging.debug(f"Configuration path: {config_path}")
    logging.debug(f"Severity level: {severity}")

    # Do stuff here.

    # Parse the config file
    ## Check if config file exists
    ## Check if config file is valid YAML

    # Parse the data contract specification
    # Parse the data contracts

    # Compare contracts vs. checks

    # Return results

    raise typer.Exit()
