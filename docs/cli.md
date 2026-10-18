# CLI

This page provides documentation for the ```data-contract-checker``` CLI.

## Output behaviour

How much of the report is printed is controlled by `--output-mode`:

| Mode | What is printed |
| ---- | --------------- |
| `failures` (default) | A verdict line, then one table per failing contract with its failing checks. When **more than one** contract fails, a consolidated failed-checks summary table is added at the end (for a single failing contract it would just duplicate the detail table, so it is skipped). |
| `summary` | A scoreboard: one line per contract, failing contracts first with their failed check *types* (no messages), passing contracts dimmed below. Answers "which contracts are broken, and roughly how?" at a glance — handy for large contract sets. |
| `full` | Like `failures`, but passing checks and fully passing contracts are shown too. |

```bash
contract-checker --output-mode summary
```

Use `--verbose` / `-v` to enable debug logging (this no longer affects the report itself):

```bash
contract-checker --verbose
```

## Machine-readable output

`--format json` replaces the human-readable report with a JSON document on stdout,
including per-check results for every contract. Logging goes to stderr, so stdout
stays clean for piping. Exit codes work exactly as in text mode.

```bash
# list all failing contract files
contract-checker --format json | jq -r '.contracts[] | select(.success | not) .file'
```

When running inside GitHub Actions (auto-detected via the `GITHUB_ACTIONS` env var),
failed checks are additionally emitted as `::error` workflow commands, which GitHub
renders as inline annotations on the PR diff. Disable with `--no-annotations`.
See [GitHub Actions](ci.md) for details.

## Exit codes

All checks always run and the full report is always printed; the exit code signals the
overall outcome so CI pipelines can pass or fail on it:

| Code | Meaning |
| ---- | ------- |
| 0 | All checks passed, or checks failed with `--severity warn` |
| 1 | One or more checks failed with `--severity error` (the default); a contract file could not be loaded; a configuration error; or no contracts were found |
| 2 | Usage error (e.g. an invalid `--severity` value) |

Use `--severity warn` to keep *checks* advisory: the same report is printed, but failed
checks do not fail the run. The other exit-1 causes are not affected by `--severity`,
because they mean the run could not do its job rather than that a contract broke a rule.

## Three kinds of problem

The checker distinguishes three situations and handles each differently, so that the
cause of a failure is always reported where it belongs:

| Problem | Example | What happens |
| ------- | ------- | ------------ |
| **Configuration error** | Checks file missing or not valid YAML; unknown check type; invalid regex in `pattern`; `data_contract_specification` missing; `--contract-path` does not exist | Reported **once**, on stderr, before any contract is read. Exit 1. |
| **Contract file cannot be loaded** | Not valid YAML; empty file; root is a list; missing `dataContractSpecification` / `apiVersion`; unsupported specification version | The file appears in the report as a failed contract with check type `load`. The **other contracts are still checked.** Exit 1 regardless of `--severity`. |
| **Contract fails a check** | `info.title` does not match `^Orders` | Reported per attribute in the usual way. Exit 1 with `--severity error`, 0 with `--severity warn`. |

Finding **no contracts at all** (an empty directory, or `include_paths` / `exclude_paths`
that filter everything out) is treated as a configuration error: a run that checks
nothing must not turn a CI gate green.

```text
$ contract-checker --contract-path ./contracts   # output abridged
✗ 2/9 checks across 3 data contracts failing

📄 Contract 1: contracts/orders.yaml ~ Checks passed: [3/4]
  ✗ FAIL  PATTERN  info.title  Attribute 'info.title' value 'Order events' does not match pattern '^Orders'

📄 Contract 3: contracts/payments.yaml ~ Checks passed: [0/1]
  ✗ FAIL  LOAD     file        contracts/payments.yaml is not valid YAML: while parsing a flow sequence ...
```

In `--format json` a load failure is an ordinary entry in `contracts[]` whose single
result has `"check_type": "load"` and `"attribute": "file"`; it counts as one failed
check in the totals.

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
