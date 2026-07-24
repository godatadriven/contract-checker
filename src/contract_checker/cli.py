import logging
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from contract_checker.logger import setup_console_logger
from contract_checker.utils.check_utils import validate_contracts
from contract_checker.utils.contract_utils import load_contracts, parse_data_contracts_path_config
from contract_checker.utils.utils import parse_yml_to_dict
from contract_checker.version import version

app = typer.Typer(
    name="contract-checker",
    help="A CLI tool for validating data contracts against defined schemas and rules.",
)


def version_callback(value: bool) -> None:
    """Handle the --version flag to display version information.

    Args:
        value: If True, print the version and exit the application.

    Raises:
        typer.Exit: Always raised when value is True to terminate the CLI.
    """
    if value:
        print(f"{version()}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    checks_config_path: Annotated[Path, typer.Option(help="The location of the data contract check file.")] = Path(
        "data-contract-checks.yml"
    ),
    severity: Annotated[
        str,
        typer.Option(help="The severity level of the checks. Can be 'error' or 'warn'"),
    ] = "error",
    verbosity: Annotated[bool, typer.Option("--verbose", "-v", help="Enables verbose output.")] = False,
    contract_path: Annotated[
        Optional[Path],
        typer.Option(
            help="Path to a data contract file or directory. Overrides 'data_contracts_path' from the checks config."
        ),
    ] = None,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            help="Outputs the version of the contract-checker package.",
        ),
    ] = None,
    custom_schema_path: Annotated[
        Optional[Path],
        typer.Option(
            help="Path to a custom JSON Schema file for contract validation.",
        ),
    ] = None,
    custom_config_path: Annotated[
        Optional[Path],
        typer.Option(
            help="Optional custom path to configuration file.",
        ),
    ] = Path("custom-checks-config.yml"),
) -> None:
    """Main entry point for the contract-checker CLI.

    Loads data contracts from the specified path, validates them against the
    configured checks, and reports all cases where the checked attributes in the
    data contracts do not meet the specified criteria.

    Args:
        config_path: Path to the YAML file containing data contract check definitions.
        severity: Severity level for validation issues ('error' or 'warn').
        verbosity: Enable verbose/debug output when True.
        contract_path: Optional override for the contract file or directory configured
        via 'data_contracts_path' in the checks config.
        version: Display version information and exit.
        custom_schema_path: Optional path to a custom JSON Schema for validation.
        custom_config_path: Optional path to custom configuration file.

    Raises:
        typer.Exit: Always raised upon completion to properly terminate the CLI.
    """
    setup_console_logger(verbosity)
    if verbosity:
        logging.debug("Verbose mode is enabled.")
    logging.info(f"Running contract-checker version: {version}")
    logging.debug(f"Checks configuration path: {checks_config_path}")
    logging.debug(f"Contract path: {contract_path}")
    logging.debug(f"Severity level: {severity}")
    if custom_schema_path:
        logging.debug(f"Custom schema path: {custom_schema_path}")
        logging.debug(f"Custom configuration path: {custom_config_path}")

    checks_dict = parse_yml_to_dict(checks_config_path)

    config_contract_path, include_paths, exclude_paths = parse_data_contracts_path_config(checks_dict)
    resolved_contract_path = contract_path or config_contract_path
    if resolved_contract_path is None:
        logging.error(
            "No contract path provided. Set 'data_contracts_path' in the checks config or pass --contract-path."
        )
        raise typer.Exit(code=1)

    # Load the contract -> internally identify type of contract -> validate contract
    contracts = load_contracts(
        contract_path=resolved_contract_path,
        contract_specification=checks_dict.get("data_contract_specification"),
        custom_schema_path=custom_schema_path,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
    )

    validate_contracts(contracts, checks_dict, verbose=verbosity)

    raise typer.Exit()


if __name__ == "__main__":
    app()
