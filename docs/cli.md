# CLI

This page provides documentation for the ```data-contract-checker``` CLI.

## Output behaviour

By default, `contract-checker` shows all contracts with only their **failing checks** — passing
checks are hidden to reduce noise. A summary table of all failures is printed at the end.

Use `--verbose` / `-v` to also show passing checks for each contract:

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
