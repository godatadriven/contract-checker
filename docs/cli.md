# CLI

This page provides documentation for the ```data-contract-checker``` CLI.

## Output behaviour

By default, `contract-checker` only prints contracts that have **failing checks**, and within those contracts only the individual checks that failed. This keeps the output concise when validating many contracts at once.

Use `--verbose` / `-v` to print all contracts and all checks, including the ones that passed:

```bash
contract-checker --verbose
```

::: mkdocs-typer2
    :module: contract_checker.cli
    :name: contract_checker
    :pretty: true
    :engine: native
