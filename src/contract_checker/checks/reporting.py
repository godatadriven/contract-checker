"""Validation result reporting and output formatting."""

from typing import Any, Dict, List, Union

from rich.console import Console
from rich.table import Table
from rich.text import Text

from .models import ContractValidationReport


class ValidationReporter:
    """Handles formatting and printing of validation results"""

    def __init__(self) -> None:
        """Initialize the reporter with a rich console"""
        self.console = Console()

    def print_results(
        self,
        reports: Union[ContractValidationReport, List[ContractValidationReport]],
        verbose: bool = True,
        summary_only: bool = False,
    ) -> None:
        """
        Print validation results in a readable format with color coding and tables

        Args:
            reports: Single ContractValidationReport or list of reports
            verbose: If True, print all results; if False, only print failures
            summary_only: If True, only print summary without individual check details
        """
        # Handle single report
        if isinstance(reports, ContractValidationReport):
            reports = [reports]

        self.console.print()  # spacing

        # Print header
        self.console.print("[bold white]Data Contract Checker[/bold white]", justify="center")
        self.console.print()  # spacing after header

        if summary_only:
            self._print_failed_checks_summary_table(reports)
        else:
            # Print individual contract results
            self._print_individual_contracts(reports, verbose)

            # Add big divider before summary table
            self.console.print("═" * 80)

            # Print failed checks summary table
            self._print_failed_checks_summary_table(reports)

    def _print_individual_contracts(self, reports: List[ContractValidationReport], verbose: bool) -> None:
        """Print detailed results for each contract in individual tables"""

        for i, report in enumerate(reports, 1):
            # Contract header
            status_text = Text()
            if report.success:
                status_text.append("✓ PASSED", style="bold green")
            else:
                status_text.append("✗ FAILED", style="bold red")

            # Extract just the filename from the path
            filename = f"{report.contract_file!s}".split("/")[-1]

            # Add divider before each contract (except the first one)
            if i > 1:
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
            visible_results = [r for r in report.results if verbose or not r.passed]
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
            filename = f"{report.contract_file!s}".split("/")[-1]
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
            Dictionary with summary statistics
        """
        return {
            "total_contracts": len(reports),
            "passed_contracts": sum(1 for r in reports if r.success),
            "failed_contracts": sum(1 for r in reports if not r.success),
            "total_checks": sum(r.total_checks for r in reports),
            "passed_checks": sum(r.passed_checks for r in reports),
            "failed_checks": sum(r.failed_checks for r in reports),
            "contracts": [
                {
                    "file": r.contract_file,
                    "success": r.success,
                    "passed": r.passed_checks,
                    "failed": r.failed_checks,
                }
                for r in reports
            ],
        }
