# CLI

This page provides documentation for the ```data-contract-checker``` CLI.

## Output behaviour

By default, `contract-checker` shows all contracts with only their **failing checks** — passing
checks are hidden to reduce noise. A summary table of all failures is printed at the end.

Use `--verbose` / `-v` to also show passing checks for each contract:

```bash
contract-checker --verbose
```

::: mkdocs-typer2
    :module: contract_checker.cli
    :name: contract_checker
    :pretty: true
    :engine: native
