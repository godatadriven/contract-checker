"""Unit tests for the CLI entry point."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from contract_checker.cli import app
from contract_checker.version import version

CUSTOM_FIXTURES = Path(__file__).parent.parent / "fixtures" / "custom"
VALID_CONTRACT = CUSTOM_FIXTURES / "valid-ecommerce-contract.yaml"
VALID_SCHEMA = CUSTOM_FIXTURES / "ecommerce-product-schema.json"
INVALID_SCHEMA = CUSTOM_FIXTURES / "invalid-json-schema.json"

DCS_FIXTURES = Path(__file__).parent.parent / "fixtures" / "dcs"
VALID_DCS_CONTRACT = DCS_FIXTURES / "1.2.1" / "time_data_type_example.yaml"
INVALID_DCS_CONTRACT = DCS_FIXTURES / "1.2.1" / "invalid_field_type.yaml"


def _write_checks_config(directory: Path, body: str = "data_contract_checks: []\n") -> Path:
    """Write a minimal checks config file and return its path."""
    config = directory / "data-contract-checks.yml"
    config.write_text(body)
    return config


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
        result = self.runner.invoke(app, ["--checks-config-path", "nonexistent-checks.yml"])
        assert result.exit_code != 0


class TestCustomSchemaCli:
    """Test the custom JSON Schema validation path of the CLI."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_schema_fails_fast(self, tmp_path: Path) -> None:
        """An invalid custom schema exits non-zero before contracts are checked."""
        config = _write_checks_config(tmp_path)
        result = self.runner.invoke(
            app,
            [
                "--lint",
                "--contract-path",
                str(VALID_CONTRACT),
                "--custom-schema-path",
                str(INVALID_SCHEMA),
                "--checks-config-path",
                str(config),
            ],
        )
        assert result.exit_code == 1
        assert "not a valid JSON Schema" in result.output

    def test_valid_schema_passes(self, tmp_path: Path) -> None:
        """A valid contract against a valid custom schema exits 0."""
        config = _write_checks_config(tmp_path)
        result = self.runner.invoke(
            app,
            [
                "--lint",
                "--contract-path",
                str(VALID_CONTRACT),
                "--custom-schema-path",
                str(VALID_SCHEMA),
                "--checks-config-path",
                str(config),
            ],
        )
        assert result.exit_code == 0

    def test_custom_schema_skipped_without_lint(self, tmp_path: Path) -> None:
        """Without --lint (the default), an invalid custom schema is ignored, exiting 0."""
        config = _write_checks_config(tmp_path)
        result = self.runner.invoke(
            app,
            [
                "--contract-path",
                str(VALID_CONTRACT),
                "--custom-schema-path",
                str(INVALID_SCHEMA),
                "--checks-config-path",
                str(config),
            ],
        )
        # Linting is off, so the invalid schema is never loaded — no fail-fast.
        assert result.exit_code == 0

    def test_schema_path_from_config(self, tmp_path: Path) -> None:
        """The custom schema path can be supplied via the checks config file."""
        config = _write_checks_config(
            tmp_path,
            "data_contract_specification: custom\n"
            "lint: true\n"
            f'custom_schema_path: "{VALID_SCHEMA.as_posix()}"\n'
            "data_contract_checks: []\n",
        )
        result = self.runner.invoke(app, ["--contract-path", str(VALID_CONTRACT), "--checks-config-path", str(config)])
        assert result.exit_code == 0

    def test_custom_spec_without_schema_exits_cleanly(self, tmp_path: Path) -> None:
        """A 'custom' spec with no schema exits 1 with a clear error, not a traceback."""
        config = _write_checks_config(
            tmp_path,
            "data_contract_specification: custom\ndata_contract_checks: []\n",
        )
        result = self.runner.invoke(app, ["--contract-path", str(VALID_CONTRACT), "--checks-config-path", str(config)])
        assert result.exit_code == 1
        # A clean typer exit, not an unhandled exception surfaced by the runner.
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "no custom schema was provided" in result.output

    def test_cli_flag_overrides_config(self, tmp_path: Path) -> None:
        """The --custom-schema-path flag overrides the config file value."""
        # Config points at a valid schema, but the CLI flag points at an invalid one.
        config = _write_checks_config(
            tmp_path,
            f'custom_schema_path: "{VALID_SCHEMA.as_posix()}"\ndata_contract_checks: []\n',
        )
        result = self.runner.invoke(
            app,
            [
                "--lint",
                "--contract-path",
                str(VALID_CONTRACT),
                "--custom-schema-path",
                str(INVALID_SCHEMA),
                "--checks-config-path",
                str(config),
            ],
        )
        # The CLI flag wins, so the invalid schema triggers the fail-fast exit.
        assert result.exit_code == 1
        assert "not a valid JSON Schema" in result.output


class TestStandardSchemaLintCli:
    """Test JSON Schema linting of standard (DCS/ODCS) contracts via the CLI."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_valid_standard_contract_lints_clean(self, tmp_path: Path) -> None:
        """A conforming DCS contract passes when --lint is enabled."""
        config = _write_checks_config(tmp_path, "data_contract_specification: dcs\ndata_contract_checks: []\n")
        result = self.runner.invoke(
            app,
            ["--lint", "--contract-path", str(VALID_DCS_CONTRACT), "--checks-config-path", str(config)],
        )
        assert result.exit_code == 0

    def test_invalid_standard_contract_fails_lint(self, tmp_path: Path) -> None:
        """A DCS contract with an illegal field type fails when --lint is enabled."""
        config = _write_checks_config(tmp_path, "data_contract_specification: dcs\ndata_contract_checks: []\n")
        result = self.runner.invoke(
            app,
            ["--lint", "--contract-path", str(INVALID_DCS_CONTRACT), "--checks-config-path", str(config)],
        )
        # The CLI itself exits cleanly; the failure surfaces in the reported summary.
        assert result.exit_code == 0
        assert "failing" in result.output
        assert "All checks passed" not in result.output

    def test_standard_contract_not_linted_by_default(self, tmp_path: Path) -> None:
        """Without --lint, an invalid standard contract is not schema-checked."""
        config = _write_checks_config(tmp_path, "data_contract_specification: dcs\ndata_contract_checks: []\n")
        result = self.runner.invoke(
            app,
            ["--contract-path", str(INVALID_DCS_CONTRACT), "--checks-config-path", str(config)],
        )
        assert result.exit_code == 0
        # No schema checks ran, so nothing fails.
        assert "failing" not in result.output
