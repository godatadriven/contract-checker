from pathlib import Path
from typing import Optional

from contract_checker.checks.models import ContractValidationReport
from contract_checker.contract.contract_base import Contract


def validate_contracts(
    contracts: list[Contract],
    checks_dict: dict,
    output_mode: str = "failures",
    output_format: str = "text",
    load_failures: Optional[list[ContractValidationReport]] = None,
    lint: bool = False,
) -> list[ContractValidationReport]:
    """
    Validate data contracts against the provided checks configuration.

    Args:
        contracts (list[Contract]): List of data contract objects to validate.
        checks_dict (dict): Dictionary containing the checks configuration.
        output_mode (str): How much of the report to print: 'summary', 'failures'
            (default), or 'full'. See ValidationReporter.print_results. Only
            applies to the 'text' format.
        output_format (str): 'text' (default) prints the human-readable report;
            'json' prints a machine-readable JSON document to stdout instead.
        load_failures (list[ContractValidationReport] | None): Reports for files
            that could not be loaded (see load_contracts); printed and counted
            alongside the validation reports, in file order.
        lint (bool): Whether to validate each contract against its JSON Schema.
            Already resolved by the caller (see utils.resolve_lint); default off.
    Returns:
        list[ContractValidationReport]: One report per validated contract, so
        callers (e.g. the CLI) can act on the outcome after results are printed.
    """
    # Imported here rather than at module level to break the circular import
    # checks/__init__ -> validator -> utils/__init__ -> check_utils -> validator.
    from contract_checker.checks.reporting import render_json
    from contract_checker.checks.validator import DataContractValidator

    validator = DataContractValidator(checks_dict, lint=lint)
    # Keep the report in discovery (sorted path) order, so "Contract N" and the
    # JSON contracts[] match the file list whether or not a file failed to load.
    # Same key as the discovery sort in load_contracts (Path, not str).
    reports: list[ContractValidationReport] = sorted(
        [*(load_failures or []), *validator.validate(contracts)],
        key=lambda report: Path(report.contract_file),
    )
    if output_format == "json":
        # Plain print, not rich: stdout must stay clean, unwrapped JSON for
        # piping into jq, files, or other tools.
        print(render_json(reports))
    else:
        validator.print_results(reports, output_mode=output_mode)
    return reports
