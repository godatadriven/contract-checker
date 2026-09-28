"""Unit tests for the CLI entry point."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner, Result

from contract_checker.cli import app
from contract_checker.version import version

CUSTOM_FIXTURES = Path(__file__).parent.parent / "fixtures" / "custom"
VALID_CONTRACT = CUSTOM_FIXTURES / "valid-ecommerce-contract.yaml"
VALID_SCHEMA = CUSTOM_FIXTURES / "ecommerce-product-schema.json"
INVALID_SCHEMA = CUSTOM_FIXTURES / "invalid-json-schema.json"


def _write_checks_config(directory: Path, body: str = "data_contract_checks: []\n") -> Path:
    """Write a minimal checks config file and return its path."""
    config = directory / "data-contract-checks.yml"
    config.write_text(body)
    return config


def test_cli_imports_cleanly_in_fresh_interpreter() -> None:
    """Importing the CLI module first must not hit a circular import.

    Pytest can mask import-order cycles because other modules are already
    loaded; a fresh interpreter reproduces what the console script does.
    """
    result = subprocess.run(
        [sys.executable, "-c", "from contract_checker.cli import app"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


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


class TestExitCodes:
    """Test that the exit code reflects the validation outcome and severity."""

    FAILING_CHECKS = (
        "data_contract_checks:\n  - attribute: info.thisdoesnotexist\n    checks:\n      - required: true\n"
    )

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def _invoke(self, config: Path, *extra: str) -> Result:
        return self.runner.invoke(
            app,
            [
                "--contract-path",
                str(VALID_CONTRACT),
                "--custom-schema-path",
                str(VALID_SCHEMA),
                "--checks-config-path",
                str(config),
                *extra,
            ],
        )

    def test_passing_checks_exit_zero(self, tmp_path: Path) -> None:
        """A run with no failing checks exits 0."""
        config = _write_checks_config(tmp_path)
        result = self._invoke(config)
        assert result.exit_code == 0

    def test_failing_checks_exit_one(self, tmp_path: Path) -> None:
        """A failing check exits 1 (default severity 'error') after printing the report."""
        config = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        result = self._invoke(config)
        assert result.exit_code == 1
        # The full report is still printed before exiting non-zero.
        assert "FAIL" in result.output

    def test_failing_checks_with_severity_warn_exit_zero(self, tmp_path: Path) -> None:
        """With --severity warn, failing checks still print but the exit code is 0."""
        config = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        result = self._invoke(config, "--severity", "warn")
        assert result.exit_code == 0
        assert "FAIL" in result.output

    def test_invalid_severity_exits_two(self, tmp_path: Path) -> None:
        """An unknown severity value is a usage error and exits 2."""
        config = _write_checks_config(tmp_path)
        result = self._invoke(config, "--severity", "bogus")
        assert result.exit_code == 2


class TestOutputModes:
    """Test the --output-mode option and the failed-checks summary table rule."""

    FAILING_CHECKS = (
        "data_contract_checks:\n  - attribute: info.thisdoesnotexist\n    checks:\n      - required: true\n"
    )

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def _invoke_on(self, contract_path: Path, config: Path, *extra: str) -> Result:
        return self.runner.invoke(
            app,
            [
                "--contract-path",
                str(contract_path),
                "--custom-schema-path",
                str(VALID_SCHEMA),
                "--checks-config-path",
                str(config),
                *extra,
            ],
        )

    def test_default_hides_summary_table_for_single_contract(self, tmp_path: Path) -> None:
        """A single failing contract shows the detail table but no duplicate summary table."""
        config = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        result = self._invoke_on(VALID_CONTRACT, config)
        assert "Contract 1" in result.output
        assert "Failed Checks Summary" not in result.output

    def test_default_shows_summary_table_for_multiple_contracts(self, tmp_path: Path) -> None:
        """With two failing contracts, the summary table appears as an overview."""
        contracts_dir = tmp_path / "contracts"
        contracts_dir.mkdir()
        for name in ("one.yaml", "two.yaml"):
            (contracts_dir / name).write_text(VALID_CONTRACT.read_text())
        config = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        result = self._invoke_on(contracts_dir, config)
        assert "Contract 2" in result.output
        assert "Failed Checks Summary" in result.output

    def test_summary_mode_shows_scoreboard_not_details(self, tmp_path: Path) -> None:
        """--output-mode summary prints the per-contract scoreboard: contract path
        and failed check types, but no detail tables and no failure messages."""
        config = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        result = self._invoke_on(VALID_CONTRACT, config, "--output-mode", "summary")
        assert "valid-ecommerce-contract.yaml" in result.output
        assert "required" in result.output
        # No per-contract detail tables, no consolidated message table, no messages.
        assert "Contract 1" not in result.output
        assert "Failed Checks Summary" not in result.output
        assert "is missing" not in result.output

    def test_summary_mode_lists_passing_contracts(self, tmp_path: Path) -> None:
        """The scoreboard includes passing contracts so the checked scope is visible."""
        config = _write_checks_config(tmp_path)
        result = self._invoke_on(VALID_CONTRACT, config, "--output-mode", "summary")
        assert "valid-ecommerce-contract.yaml" in result.output

    def test_full_mode_shows_passing_checks(self, tmp_path: Path) -> None:
        """--output-mode full lists passing checks that are hidden by default."""
        config = _write_checks_config(tmp_path)
        default_result = self._invoke_on(VALID_CONTRACT, config)
        full_result = self._invoke_on(VALID_CONTRACT, config, "--output-mode", "full")
        assert "PASS" not in default_result.output
        assert "PASS" in full_result.output

    def test_invalid_output_mode_exits_two(self, tmp_path: Path) -> None:
        """An unknown output mode is a usage error and exits 2."""
        config = _write_checks_config(tmp_path)
        result = self._invoke_on(VALID_CONTRACT, config, "--output-mode", "bogus")
        assert result.exit_code == 2


class TestOutputFormat:
    """Test the --format option and GitHub Actions annotations."""

    FAILING_CHECKS = (
        "data_contract_checks:\n  - attribute: info.thisdoesnotexist\n    checks:\n      - required: true\n"
    )

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def _invoke(self, config: Path, *extra: str, env: dict[str, str] | None = None) -> Result:
        return self.runner.invoke(
            app,
            [
                "--contract-path",
                str(VALID_CONTRACT),
                "--custom-schema-path",
                str(VALID_SCHEMA),
                "--checks-config-path",
                str(config),
                *extra,
            ],
            env=env,
        )

    def test_json_format_outputs_parseable_document(self, tmp_path: Path) -> None:
        """--format json prints a JSON document with failure details, no text report."""
        config = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        result = self._invoke(config, "--format", "json")
        # Parse stdout only: logging goes to stderr, keeping stdout pipeable JSON.
        document = json.loads(result.stdout)
        assert document["version"] == version()
        assert document["total_contracts"] == 1
        assert document["failed_checks"] == 1
        failed = [r for r in document["contracts"][0]["results"] if not r["passed"]]
        assert failed[0]["attribute"] == "info.thisdoesnotexist"
        assert failed[0]["check_type"] == "required"
        assert "is missing" in failed[0]["message"]
        # The human-readable report must not pollute the JSON stdout.
        assert "Data Contract Checker" not in result.stdout

    def test_json_format_keeps_exit_codes(self, tmp_path: Path) -> None:
        """--format json still exits 1 on failing checks and 0 when all pass."""
        failing = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        assert self._invoke(failing, "--format", "json").exit_code == 1
        passing_dir = tmp_path / "passing"
        passing_dir.mkdir()
        passing = _write_checks_config(passing_dir)
        assert self._invoke(passing, "--format", "json").exit_code == 0

    def test_invalid_format_exits_two(self, tmp_path: Path) -> None:
        """An unknown format is a usage error and exits 2."""
        config = _write_checks_config(tmp_path)
        result = self._invoke(config, "--format", "yaml")
        assert result.exit_code == 2

    def test_annotations_emitted_in_github_actions(self, tmp_path: Path) -> None:
        """Inside GitHub Actions, failed checks are emitted as ::error annotations."""
        config = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        result = self._invoke(config, env={"GITHUB_ACTIONS": "true"})
        assert "::error file=" in result.output
        assert "title=required" in result.output

    def test_annotations_absent_outside_github_actions(self, tmp_path: Path) -> None:
        """Without the GITHUB_ACTIONS env var, no annotation lines are printed."""
        config = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        result = self._invoke(config, env={"GITHUB_ACTIONS": ""})
        assert "::error" not in result.output

    def test_no_annotations_flag_suppresses_annotations(self, tmp_path: Path) -> None:
        """--no-annotations disables annotations even inside GitHub Actions."""
        config = _write_checks_config(tmp_path, self.FAILING_CHECKS)
        result = self._invoke(config, "--no-annotations", env={"GITHUB_ACTIONS": "true"})
        assert "::error" not in result.output


class TestLogging:
    """Test default quietness and the verbose version line."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def _invoke(self, config: Path, *extra: str) -> Result:
        return self.runner.invoke(
            app,
            [
                "--contract-path",
                str(VALID_CONTRACT),
                "--custom-schema-path",
                str(VALID_SCHEMA),
                "--checks-config-path",
                str(config),
                *extra,
            ],
        )

    def test_default_run_has_no_info_preamble(self, tmp_path: Path) -> None:
        """Without -v, the INFO/DEBUG log lines stay hidden."""
        config = _write_checks_config(tmp_path)
        result = self._invoke(config)
        assert "Running contract-checker version" not in result.output

    def test_version_always_shown_in_report_header(self, tmp_path: Path) -> None:
        """The report header carries the tool version on every run."""
        config = _write_checks_config(tmp_path)
        result = self._invoke(config)
        assert f"Data Contract Checker v{version()}" in result.output

    def test_verbose_logs_the_real_version(self, tmp_path: Path) -> None:
        """With -v, the version line shows the actual version, never None."""
        config = _write_checks_config(tmp_path)
        result = self._invoke(config, "-v")
        assert f"Running contract-checker version: {version()}" in result.output
        assert "version: None" not in result.output


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
                "--contract-path",
                str(VALID_CONTRACT),
                "--custom-schema-path",
                str(VALID_SCHEMA),
                "--checks-config-path",
                str(config),
            ],
        )
        assert result.exit_code == 0

    def test_schema_path_from_config(self, tmp_path: Path) -> None:
        """The custom schema path can be supplied via the checks config file."""
        config = _write_checks_config(
            tmp_path,
            "data_contract_specification: custom\n"
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
