# CLI

This page provides documentation for the ```data-contract-checker``` CLI.

## Output behaviour

How much of the report is printed is controlled by `--output-mode`:

| Mode | What is printed |
| ---- | --------------- |
| `failures` (default) | A verdict line, then one table per failing contract with its failing checks. When **more than one** contract fails, a consolidated failed-checks summary table is added at the end (for a single failing contract it would just duplicate the detail table, so it is skipped). |
| `summary` | The verdict line and the failed-checks summary table only — no per-contract detail. Handy for large contract sets. |
| `full` | Like `failures`, but passing checks and fully passing contracts are shown too. |

```bash
contract-checker --output-mode summary
```

Use `--verbose` / `-v` to enable debug logging (this no longer affects the report itself):

```bash
contract-checker --verbose
```

## Exit codes

All checks always run and the full report is always printed; the exit code signals the
overall outcome so CI pipelines can pass or fail on it:

| Code | Meaning |
| ---- | ------- |
| 0 | All checks passed, or failures occurred with `--severity warn` |
| 1 | One or more checks failed with `--severity error` (the default), or a config/load error |
| 2 | Usage error (e.g. an invalid `--severity` value) |

Use `--severity warn` to keep the checker advisory: the same report is printed, but the
run always exits 0 so the pipeline stays green.

## Contract discovery

Contracts are loaded from `data_contracts_path` in the checks config, including any
`include_paths` / `exclude_paths` glob filters (see [Configuration](config.md)).
The `--contract-path` option overrides the configured path — handy for validating a
single contract file ad hoc; filters are skipped when it points to a single file.

::: mkdocs-typer2
    :module: contract_checker.cli
    :name: contract_checker
    :pretty: true
    :engine: native
