"""Unit tests for the CLI entry point."""

from __future__ import annotations

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
