"""Validation result reporting and output formatting."""

import json
import os
from typing import Any, Dict, List, Union

from rich.console import Console
from rich.table import Table
from rich.text import Text

from contract_checker.version import version as get_version

from .models import ContractValidationReport

# Valid values for the CLI's --output-mode option.
OUTPUT_MODES = ("summary", "failures", "full")

# Valid values for the CLI's --format option.
OUTPUT_FORMATS = ("text", "json")


def build_summary(reports: List[ContractValidationReport]) -> Dict[str, Any]:
    """
    Build a JSON-serializable summary of validation results.

    Includes per-check results for each contract so machine consumers
    (scripts, dashboards, other tools) get the full picture, not just counts.

    Args:
        reports: List of ContractValidationReport objects

    Returns:
        Dictionary with summary statistics and per-contract check results
    """
    return {
        "version": get_version(),
        "total_contracts": len(reports),
        "passed_contracts": sum(1 for r in reports if r.success),
        "failed_contracts": sum(1 for r in reports if not r.success),
        "total_checks": sum(r.total_checks for r in reports),
        "passed_checks": sum(r.passed_checks for r in reports),
        "failed_checks": sum(r.failed_checks for r in reports),
        "contracts": [
            {
                "file": str(r.contract_file),
                "success": r.success,
                "passed": r.passed_checks,
                "failed": r.failed_checks,
                "results": [
                    {
                        "check_type": result.check_type,
                        "attribute": result.attribute,
                        "passed": result.passed,
                        "message": result.message,
                    }
                    for result in r.results
                ],
            }
            for r in reports
        ],
    }


def render_json(reports: List[ContractValidationReport]) -> str:
    """Render validation results as a JSON document for machine consumption."""
    return json.dumps(build_summary(reports), indent=2)


def display_path(path: str) -> str:
    """
    Make a contract path readable and unambiguous: relative to the working
    directory (clickable in most terminals, and distinguishes same-named
    files in different folders). Falls back to the original string when a
    relative path cannot be computed (e.g. a different drive on Windows).
    """
    try:
        return os.path.relpath(str(path))
    except ValueError:
        return str(path)


def _escape_annotation_data(value: str) -> str:
    """Escape the message part of a GitHub workflow command."""
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_annotation_property(value: str) -> str:
    """Escape a property value (file, title) of a GitHub workflow command."""
    return _escape_annotation_data(value).replace(":", "%3A").replace(",", "%2C")


def github_annotations(reports: List[ContractValidationReport]) -> List[str]:
    """
    Build GitHub Actions workflow-command lines for every failed check.

    Each line renders as an error annotation on the contract file in the PR's
    'Files changed' view. Paths are made relative to the working directory
    (the repository root on GitHub runners) so GitHub can match them to files
    in the diff.

    Args:
        reports: List of ContractValidationReport objects

    Returns:
        One '::error ...' line per failed check
    """
    lines = []
    for report in reports:
        for result in report.results:
            if result.passed:
                continue
            file_path = display_path(str(report.contract_file))
            lines.append(
                f"::error file={_escape_annotation_property(file_path)},"
                f"title={_escape_annotation_property(result.check_type)}"
                f"::{_escape_annotation_data(result.message)}"
            )
    return lines


class ValidationReporter:
    """Handles formatting and printing of validation results"""

    def __init__(self) -> None:
        """Initialize the reporter with a rich console"""
        self.console = Console()

    def print_results(
        self,
        reports: Union[ContractValidationReport, List[ContractValidationReport]],
        output_mode: str = "failures",
    ) -> None:
        """
        Print validation results in a readable format with color coding and tables

        Args:
            reports: Single ContractValidationReport or list of reports
            output_mode: One of OUTPUT_MODES.
                'summary'  - verdict line plus a one-line-per-contract scoreboard
                             (failing contracts first with their failed check
                             types, passing contracts dimmed). No messages.
                'failures' - per-contract tables with failing checks (default). The
                             failed-checks summary table is added only when more than
                             one contract has failures, since with a single failing
                             contract it would duplicate the detail table.
                'full'     - like 'failures', but passing checks (and fully passing
                             contracts) are shown as well.
        """
        # Handle single report
        if isinstance(reports, ContractValidationReport):
            reports = [reports]

        self.console.print()  # spacing

        # Print header with the tool version, always visible
        self.console.print(
            f"[bold white]Data Contract Checker[/bold white] [dim]v{get_version()}[/dim]",
            justify="center",
        )
        self.console.print()  # spacing after header

        self._print_top_summary(reports)

        show_passing = output_mode == "full"
        all_passed = all(r.success for r in reports)

        if output_mode == "summary":
            # Scoreboard: one line per contract, failing first. Shown even when
            # everything passes, so the full scope of what was checked is visible.
            self._print_contracts_scoreboard(reports)
            return

        if all_passed:
            # Nothing failed: the verdict line says it all. In 'full' mode the
            # individual passing checks are still listed.
            if show_passing:
                self._print_individual_contracts(reports, show_passing)
            return

        # Print individual contract results (failures only unless in 'full' mode)
        self._print_individual_contracts(reports, show_passing)

        # The failed-checks summary table only earns its place as an overview when
        # failures are spread across multiple contracts; for a single failing
        # contract it would repeat the detail table above verbatim.
        failing_contracts = sum(1 for r in reports if not r.success)
        if failing_contracts > 1:
            # Add big divider before summary table
            self.console.print("═" * 80)
            self._print_failed_checks_summary_table(reports)

    def _print_top_summary(self, reports: List[ContractValidationReport]) -> None:
        """Print a one-line summary at the top of the output"""
        total_checks = sum(r.total_checks for r in reports)
        failed_checks = sum(r.failed_checks for r in reports)
        total_contracts = len(reports)

        if failed_checks == 0:
            self.console.print(
                f"[bold green]✓ All checks passed "
                f"({total_checks} checks across {total_contracts} data contracts)"
                f"[/bold green]"
            )
        else:
            self.console.print(
                f"[bold red]✗ {failed_checks}/{total_checks} checks across "
                f"{total_contracts} data contracts failing[/bold red]"
            )
        self.console.print()  # spacing after summary

    def _print_individual_contracts(self, reports: List[ContractValidationReport], show_passing: bool) -> None:
        """Print detailed results for each contract in individual tables"""

        visible_reports = [(i, r) for i, r in enumerate(reports, 1) if show_passing or not r.success]

        for pos, (i, report) in enumerate(visible_reports):
            # Contract header
            status_text = Text()
            if report.success:
                status_text.append("✓ PASSED", style="bold green")
            else:
                status_text.append("✗ FAILED", style="bold red")

            # Show the path relative to the working directory: unambiguous when
            # contracts in different folders share a filename, and clickable in
            # most terminals.
            filename = display_path(str(report.contract_file))

            # Add divider before each contract (except the first one)
            if pos > 0:
                self.console.print("\n" + " " * 80)

            self.console.print(
                f"\n[bold cyan]📄 Contract {i}: {filename} ~ "
                f"Checks passed: [{report.passed_checks}/"
                f"{report.total_checks}][/bold cyan]"
            )
            if report.success:
                self.console.print(status_text)

            # Create table for this contract's checks
            # No title needed, but excluding it caused error
            title = " "
            table = Table(
                title=title,
                show_header=True,
                header_style="bold white",
                border_style="white",
                padding=(0, 1),  # Add vertical and horizontal padding
            )

            table.add_column("Status", style="bold", width=8)
            table.add_column("Check Type", style="white")
            table.add_column("Attribute", style="white")
            table.add_column("Message", style="white")

            # Add rows for each check result
            visible_results = [r for r in report.results if show_passing or not r.passed]
            for idx, result in enumerate(visible_results):
                # Color code the status
                if result.passed:
                    status = Text("✓ PASS", style="bold green")
                else:
                    status = Text("✗ FAIL", style="bold red")

                # Color code the check type based on result
                check_type_style = "green" if result.passed else "red"

                # Add line break padding to messag
                message_text = Text()
                message_text.append(result.message)
                if idx < len(visible_results) - 1:  # Don't need spacing after last row
                    message_text.append("\n ")

                table.add_row(
                    status,
                    Text(result.check_type.upper(), style=check_type_style),
                    result.attribute,
                    message_text,
                )

            if table.rows:
                self.console.print(table)

            else:
                self.console.print("[dim]No checks to display with current verbosity settings[/dim]")

    def _print_contracts_scoreboard(self, reports: List[ContractValidationReport]) -> None:
        """
        Print a compact scoreboard: one line per contract, failing contracts
        first with their failed check types (no messages), passing contracts
        dimmed below. Answers 'which contracts are broken, and roughly how?'
        at a glance, even for large contract sets.
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("status", width=2)
        table.add_column("contract", overflow="fold")
        table.add_column("checks", justify="right")
        table.add_column("failed checks", overflow="fold")

        ordered = [r for r in reports if not r.success] + [r for r in reports if r.success]
        for report in ordered:
            path = display_path(str(report.contract_file))
            if report.success:
                table.add_row(
                    Text("✓", style="bold green"),
                    Text(path, style="dim"),
                    Text(f"{report.passed_checks}/{report.total_checks} passed", style="dim"),
                    "",
                )
            else:
                failed_types = sorted({result.check_type for result in report.results if not result.passed})
                table.add_row(
                    Text("✗", style="bold red"),
                    Text(path, style="cyan"),
                    Text(f"{report.failed_checks}/{report.total_checks} failed", style="red"),
                    Text(", ".join(failed_types), style="red"),
                )

        self.console.print(table)

    def _print_failed_checks_summary_table(self, reports: List[ContractValidationReport]) -> None:
        """Print summary table showing all failed checks per contract"""

        # Create failed checks summary table
        failed_checks_table = Table(
            title=" ",
            show_header=True,
            header_style="bold white",
            border_style="white",
            padding=(0, 1),  # Add vertical and horizontal padding
        )

        failed_checks_table.add_column("Contract File", style="cyan")
        failed_checks_table.add_column("Check Type", style="yellow")
        failed_checks_table.add_column("Attribute", style="white")
        failed_checks_table.add_column("Failure Message", style="white")

        # Track statistics
        total_contracts = len(reports)
        failed_contracts = 0
        total_failed_checks = 0

        for report in reports:
            filename = display_path(str(report.contract_file))
            failed_results = [r for r in report.results if not r.passed]

            if failed_results:
                failed_contracts += 1
                total_failed_checks += len(failed_results)

                # Add a section separator for each contract with failures
                if failed_contracts > 1:
                    failed_checks_table.add_section()

                # Add rows for each failed check
                for i, result in enumerate(failed_results):
                    # Only show filename for the first failure of each contract
                    contract_name = filename if i == 0 else ""

                    # Add line break padding to message (except last row)
                    message_text = Text()
                    message_text.append(result.message)
                    if i < len(failed_results) - 1:  # Don't add spacing to last row
                        message_text.append("\n ")

                    failed_checks_table.add_row(
                        contract_name,
                        Text(result.check_type.upper(), style="bold red"),
                        result.attribute,
                        message_text,
                    )

        self.console.print(
            f"\n[bold cyan]🔴 Failed Checks Summary ~ "
            f"Contracts with failed checks: [{failed_contracts}/{total_contracts}]"
            f"[/bold cyan]"
        )

        self.console.print(failed_checks_table)

    def get_summary(self, reports: List[ContractValidationReport]) -> Dict[str, Any]:
        """
        Get a summary dictionary of validation results

        Args:
            reports: List of ContractValidationReport objects

        Returns:
            Dictionary with summary statistics and per-contract check results
        """
        return build_summary(reports)
