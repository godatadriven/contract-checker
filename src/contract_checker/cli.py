import logging
import os
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from contract_checker.checks.reporting import OUTPUT_FORMATS, OUTPUT_MODES, github_annotations
from contract_checker.logger import setup_console_logger
from contract_checker.utils.check_utils import validate_contracts
from contract_checker.utils.contract_utils import load_contracts, parse_data_contracts_path_config
from contract_checker.utils.utils import CustomSchemaError, load_and_validate_json_schema, parse_yml_to_dict
from contract_checker.version import version as get_version

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
        print(f"{get_version()}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    checks_config_path: Annotated[Path, typer.Option(help="The location of the data contract check file.")] = Path(
        "data-contract-checks.yml"
    ),
    severity: Annotated[
        str,
        typer.Option(
            help="The severity level of the checks. 'error' exits with code 1 when checks fail "
            "(fails CI); 'warn' prints the same report but always exits 0."
        ),
    ] = "error",
    output_mode: Annotated[
        str,
        typer.Option(
            help="How much of the report to print. 'summary': verdict plus the failed-checks "
            "summary table; 'failures': per-contract failure details (default); "
            "'full': also show passing checks."
        ),
    ] = "failures",
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            help="Output format. 'text': human-readable report (default); "
            "'json': machine-readable JSON document on stdout.",
        ),
    ] = "text",
    no_annotations: Annotated[
        bool,
        typer.Option(
            "--no-annotations",
            help="Disable GitHub Actions error annotations (emitted automatically when running in GitHub Actions).",
        ),
    ] = False,
    verbosity: Annotated[bool, typer.Option("--verbose", "-v", help="Enables verbose (debug) logging.")] = False,
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
            help="Path to a custom JSON Schema file for contract validation. "
            "Overrides 'custom_schema_path' in the checks config file.",
        ),
    ] = None,
) -> None:
    """Main entry point for the contract-checker CLI.

    Loads data contracts from the specified path, validates them against the
    configured checks, and reports all cases where the checked attributes in the
    data contracts do not meet the specified criteria.

    Args:
        config_path: Path to the YAML file containing data contract check definitions.
        severity: Severity level for validation issues ('error' or 'warn').
        output_mode: How much of the report to print ('summary', 'failures', or 'full').
        output_format: 'text' for the human-readable report, 'json' for machine output.
        no_annotations: Disable the GitHub Actions error annotations.
        verbosity: Enable verbose (debug) logging when True.
        contract_path: Optional override for the contract file or directory configured
        via 'data_contracts_path' in the checks config.
        version: Display version information and exit.
        custom_schema_path: Optional path to a custom JSON Schema for validation.

    Raises:
        typer.Exit: Always raised upon completion to properly terminate the CLI.
    """
    setup_console_logger(verbosity)
    if verbosity:
        logging.debug("Verbose mode is enabled.")
    # get_version(), not the shadowing --version flag parameter (always None here).
    logging.info(f"Running contract-checker version: {get_version()}")
    logging.debug(f"Checks configuration path: {checks_config_path}")
    logging.debug(f"Contract path: {contract_path}")
    logging.debug(f"Severity level: {severity}")

    if severity not in ("error", "warn"):
        logging.error(f"Invalid severity '{severity}'. Use 'error' or 'warn'.")
        raise typer.Exit(code=2)

    if output_mode not in OUTPUT_MODES:
        logging.error(f"Invalid output mode '{output_mode}'. Use one of: {', '.join(OUTPUT_MODES)}.")
        raise typer.Exit(code=2)

    if output_format not in OUTPUT_FORMATS:
        logging.error(f"Invalid format '{output_format}'. Use one of: {', '.join(OUTPUT_FORMATS)}.")
        raise typer.Exit(code=2)

    checks_dict = parse_yml_to_dict(checks_config_path)

    # Resolve the contract path: the CLI flag wins, otherwise fall back to the
    # 'data_contracts_path' block in the checks config file (which may also carry
    # include/exclude glob filters).
    config_contract_path, include_paths, exclude_paths = parse_data_contracts_path_config(checks_dict)
    resolved_contract_path = contract_path or config_contract_path
    if resolved_contract_path is None:
        logging.error(
            "No contract path provided. Set 'data_contracts_path' in the checks config or pass --contract-path."
        )
        raise typer.Exit(code=1)

    # Resolve the custom schema path: the CLI flag wins, otherwise fall back to the
    # 'custom_schema_path' key in the checks config file.
    config_schema_path = checks_dict.get("custom_schema_path") if checks_dict else None
    resolved_schema_path = custom_schema_path or (Path(config_schema_path) if config_schema_path else None)

    # Fail fast: a custom schema must itself be a valid JSON Schema before we
    # attempt to validate any contracts against it.
    if resolved_schema_path is not None:
        logging.debug(f"Custom schema path: {resolved_schema_path}")
        try:
            load_and_validate_json_schema(resolved_schema_path)
        except CustomSchemaError as e:
            logging.error(str(e))
            raise typer.Exit(code=1)

    # Load the contract -> internally identify type of contract -> validate contract.
    # Misconfiguration (e.g. a 'custom' spec with no schema, or a missing contract
    # path) surfaces as a clear error and a non-zero exit, matching the fail-fast
    # handling above rather than leaking a stack trace.
    try:
        contracts = load_contracts(
            contract_path=resolved_contract_path,
            contract_specification=checks_dict.get("data_contract_specification") if checks_dict else None,
            custom_schema_path=resolved_schema_path,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
        )
    except (ValueError, FileNotFoundError) as e:
        logging.error(str(e))
        raise typer.Exit(code=1)

    reports = validate_contracts(contracts, checks_dict, output_mode=output_mode, output_format=output_format)

    # Inside GitHub Actions (detected via the GITHUB_ACTIONS env var the runner
    # always sets), also emit workflow-command lines so failures show up as
    # inline annotations on the PR diff. Text format only: JSON consumers get
    # the same information structured in the document itself.
    if output_format == "text" and not no_annotations and os.environ.get("GITHUB_ACTIONS") == "true":
        for line in github_annotations(reports):
            print(line)

    # All checks have run and the full report has been printed above; the exit
    # code only signals the overall outcome to the shell/CI. With severity
    # 'warn' the run always exits 0, keeping the check advisory.
    failed_checks = sum(report.failed_checks for report in reports)
    if failed_checks > 0 and severity == "error":
        raise typer.Exit(code=1)

    raise typer.Exit()


if __name__ == "__main__":
    app()
