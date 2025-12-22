"""Validation result reporting and output formatting."""
from typing import Any, Dict, List, Union

from rich.console import Console
from rich.table import Table
from rich.text import Text

from .models import ContractValidationReport, ValidationResult


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
        detailed_failures: bool = True,
    ) -> None:
        """
        Print validation results in a readable format with color coding and tables

        Args:
            reports: Single ContractValidationReport or list of reports
            verbose: If True, print all results; if False, only print failures
            summary_only: If True, only print summary without individual check details
            detailed_failures: If True, print a detailed failure report at the end
        """
        # Handle single report
        if isinstance(reports, ContractValidationReport):
            reports = [reports]

        self.console.print()  # Add spacing
        
        if summary_only:
            self._print_contract_summary_table(reports)
            if detailed_failures:
                self._print_check_type_summary_table(reports)
        else:
            # Print individual contract results
            self._print_individual_contracts(reports, verbose)
            
            # Print overall summary
            self._print_contract_summary_table(reports)
            
            # Print check type summary
            self._print_check_type_summary_table(reports)

    def _print_individual_contracts(
        self, reports: List[ContractValidationReport], verbose: bool
    ) -> None:
        """Print detailed results for each contract in individual tables"""
        
        for i, report in enumerate(reports, 1):
            # Contract header
            status_text = Text()
            if report.success:
                status_text.append("✓ PASSED", style="bold green")
            else:
                status_text.append("✗ FAILED", style="bold red")
            
            self.console.print(
                f"\n[bold]Contract {i}/{len(reports)}:[/bold] {report.contract_file}"
            )
            self.console.print(status_text)
            
            # Create table for this contract's checks
            title = (
                f"Validation Results "
                f"({report.passed_checks}/{report.total_checks} passed)"
            )
            table = Table(
                title=title,
                show_header=True,
                header_style="bold blue",
                border_style="blue"
            )
            
            table.add_column("Status", style="bold", width=8)
            table.add_column("Check Type", style="cyan")
            table.add_column("Attribute", style="magenta")
            table.add_column("Message", style="white")
            
            # Add rows for each check result
            for result in report.results:
                if verbose or not result.passed:
                    # Color code the status
                    if result.passed:
                        status = Text("✓ PASS", style="bold green")
                    else:
                        status = Text("✗ FAIL", style="bold red")
                    
                    # Color code the check type based on result
                    check_type_style = "green" if result.passed else "red"
                    
                    table.add_row(
                        status,
                        Text(result.check_type.upper(), style=check_type_style),
                        result.attribute,
                        result.message
                    )
            
            if table.rows:  # Only show table if there are rows to display
                self.console.print(table)
            else:
                self.console.print(
                    "[dim]No checks to display with current verbosity settings[/dim]"
                )

    def _print_contract_summary_table(
        self, reports: List[ContractValidationReport]
    ) -> None:
        """Print summary table of all contracts"""
        
        # Calculate overall statistics
        total_contracts = len(reports)
        successful_contracts = sum(1 for r in reports if r.success)
        failed_contracts = total_contracts - successful_contracts
        total_checks = sum(r.total_checks for r in reports)
        total_passed = sum(r.passed_checks for r in reports)
        
        # Create summary table
        summary_table = Table(
            title="📋 Contract Validation Summary",
            show_header=True,
            header_style="bold blue",
            border_style="blue"
        )
        
        summary_table.add_column("Contract File", style="cyan")
        summary_table.add_column("Status", style="bold", width=10)
        summary_table.add_column("Passed", style="green", justify="center")
        summary_table.add_column("Failed", style="red", justify="center")
        summary_table.add_column("Total", style="blue", justify="center")
        summary_table.add_column("Success Rate", style="white", justify="center")
        
        for report in reports:
            # Status with color
            if report.success:
                status = Text("✓ PASSED", style="bold green")
            else:
                status = Text("✗ FAILED", style="bold red")
            
            # Calculate success rate
            if report.total_checks > 0:
                success_rate = report.passed_checks / report.total_checks * 100
            else:
                success_rate = 0
            
            # Color code the success rate
            if success_rate == 100:
                rate_style = "bold green"
            elif success_rate >= 80:
                rate_style = "yellow"
            else:
                rate_style = "red"
            
            summary_table.add_row(
                report.contract_file.split('/')[-1],  # Just filename
                status,
                str(report.passed_checks),
                str(report.failed_checks),
                str(report.total_checks),
                Text(f"{success_rate:.1f}%", style=rate_style)
            )
        
        # Add totals row
        if total_checks > 0:
            overall_success_rate = total_passed / total_checks * 100
        else:
            overall_success_rate = 0
        
        if overall_success_rate == 100:
            rate_style = "bold green"
        elif overall_success_rate >= 80:
            rate_style = "yellow"
        else:
            rate_style = "red"
        
        summary_table.add_section()
        summary_table.add_row(
            Text("TOTAL", style="bold white"),
            Text(f"✓ {successful_contracts} / ✗ {failed_contracts}", style="bold white"),
            Text(str(total_passed), style="bold green"),
            Text(str(total_checks - total_passed), style="bold red"),
            Text(str(total_checks), style="bold blue"),
            Text(f"{overall_success_rate:.1f}%", style=rate_style)
        )
        
        self.console.print(summary_table)

    def _print_check_type_summary_table(self, reports: List[ContractValidationReport]) -> None:
        """Print summary table showing failure statistics by check type"""
        
        # Collect all failures by check type and count contracts affected
        check_type_stats: Dict[str, Dict[str, Any]] = {}
        
        for report in reports:
            contract_file = report.contract_file
            for result in report.results:
                check_type = result.check_type
                
                if check_type not in check_type_stats:
                    check_type_stats[check_type] = {
                        'total_checks': 0,
                        'failed_checks': 0,
                        'affected_contracts': set(),
                        'total_contracts': set()
                    }
                
                check_type_stats[check_type]['total_checks'] += 1
                check_type_stats[check_type]['total_contracts'].add(contract_file)
                
                if not result.passed:
                    check_type_stats[check_type]['failed_checks'] += 1
                    check_type_stats[check_type]['affected_contracts'].add(contract_file)
        
        if not check_type_stats:
            return
        
        # Create check type summary table
        check_table = Table(
            title="📊 Check Type Failure Summary",
            show_header=True,
            header_style="bold blue",
            border_style="blue"
        )
        
        check_table.add_column("Check Type", style="cyan")
        check_table.add_column("Total Checks", style="blue", justify="center")
        check_table.add_column("Failed Checks", style="red", justify="center")
        check_table.add_column("Contracts Affected", style="orange1", justify="center")
        check_table.add_column("Failure Rate", style="white", justify="center")
        check_table.add_column("Impact", style="white", justify="center")
        
        # Sort by failure count (descending)
        sorted_stats = sorted(
            check_type_stats.items(),
            key=lambda x: x[1]['failed_checks'],
            reverse=True
        )
        
        total_contracts = len(reports)
        
        for check_type, stats in sorted_stats:
            failed_checks = stats['failed_checks']
            total_checks = stats['total_checks']
            contracts_affected = len(stats['affected_contracts'])
            total_contracts_with_check = len(stats['total_contracts'])
            
            # Calculate failure rate
            failure_rate = (failed_checks / total_checks * 100) if total_checks > 0 else 0
            
            # Calculate impact (percentage of contracts affected)
            impact = (contracts_affected / total_contracts * 100) if total_contracts > 0 else 0
            
            # Color code based on severity
            if failed_checks == 0:
                check_type_style = "green"
                failure_style = "green"
                impact_style = "green"
            elif failure_rate > 50:
                check_type_style = "red"
                failure_style = "red" 
                impact_style = "red" if impact > 30 else "orange1"
            elif failure_rate > 20:
                check_type_style = "orange1"
                failure_style = "orange1"
                impact_style = "orange1" if impact > 15 else "yellow"
            else:
                check_type_style = "yellow"
                failure_style = "yellow"
                impact_style = "yellow"
            
            check_table.add_row(
                Text(check_type.upper(), style=check_type_style),
                str(total_checks),
                Text(str(failed_checks), style=failure_style),
                Text(f"{contracts_affected}/{total_contracts_with_check}", style=impact_style),
                Text(f"{failure_rate:.1f}%", style=failure_style),
                Text(f"{impact:.1f}%", style=impact_style)
            )
        
        self.console.print("\n")
        self.console.print(check_table)

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
