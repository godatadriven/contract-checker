"""Unit tests for the CLI entry point."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from contract_checker.cli import app
from contract_checker.version import version


class TestCli:
    """Test the Typer CLI application."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_version_flag(self) -> None:
        """Test that --version exits 0 and prints the version string."""
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert version() in result.output

    def test_missing_checks_config(self) -> None:
        """Test that a non-existent checks config path causes a non-zero exit."""
        result = self.runner.invoke(app, ["nonexistent-checks.yml"])
        assert result.exit_code != 0

    def test_missing_contract_path_errors(self, tmp_path: Path) -> None:
        """No --contract-path and no data_contracts_path in config -> exit code 1."""
        checks = tmp_path / "checks.yml"
        checks.write_text("data_contract_specification: dcs\ndata_contract_checks: []\n")
        result = self.runner.invoke(app, [str(checks)])
        assert result.exit_code == 1
