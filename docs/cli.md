# CLI

This page provides documentation for the ```data-contract-checker``` CLI.

## Output behaviour

By default, `contract-checker` shows all contracts with only their **failing checks** — passing
checks are hidden to reduce noise. A summary table of all failures is printed at the end.

Use `--verbose` / `-v` to also show passing checks for each contract:

```bash
contract-checker --verbose
```

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
