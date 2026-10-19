# Data Contract Checker

> Validate data contracts against configurable rules — with human-readable output.

[![PyPI version](https://img.shields.io/pypi/v/contract-checker)](https://pypi.org/project/contract-checker/)
[![Python versions](https://img.shields.io/pypi/pyversions/contract-checker)](https://pypi.org/project/contract-checker/)
[![License](https://img.shields.io/github/license/godatadriven/contract-checker)](LICENSE)

📖 **Full documentation: [godatadriven.github.io/contract-checker](https://godatadriven.github.io/contract-checker)**

Data Contract Checker is an open source Python package for defining, enforcing, and maintaining validation rules across your data contracts. Define the best practices and naming conventions you care about once — required fields, naming patterns, accepted values — then enforce them consistently across a large number of contracts. Run the CLI and get clear pass/fail feedback on every contract in your repository.

This makes it practical to keep a large, growing set of data contracts consistent: instead of reviewing each contract by hand, you codify your team's conventions as checks and let the tool enforce them everywhere.

It supports the two major open data contract standards out of the box, with custom JSON Schema support for everything else.

---

## Supported standards

| Standard | Versions |
|---|---|
| [DCS — Data Contract Specification](https://datacontract.com) | 0.9.0 – 1.2.1 |
| [ODCS — Open Data Contract Standard](https://bitol-io.github.io/open-data-contract-standard/) | 2.2.1 – 3.1.0 |
| Custom JSON Schema | any |

See the [documentation](https://godatadriven.github.io/contract-checker/) for the full version-compatibility detail per standard.

---

## Installation

```bash
pip install contract-checker
```

```bash
# or with uv
uv add contract-checker
```

Requires Python 3.11–3.15.

---

## Quick start

**1. Create a `data-contract-checks.yml` file** in your project root:

```yaml
data_contract_specification: dcs   # or "odcs" / "custom"

data_contracts_path:
  path: ./contracts/               # where your contracts live
  exclude_paths:
    - archive/**                   # optional glob filters

data_contract_checks:
  - attribute: info.title
    checks:
      - required: true
      - pattern: "^[A-Z]"          # title must start with a capital letter

  - attribute: info.version
    checks:
      - required: true
      - pattern: "^\\d+\\.\\d+\\.\\d+$"  # must be semver

  - attribute: models.*.fields.*.description
    checks:
      - required: true             # every field must have a description

  - attribute: servers.type
    checks:
      - accepted_values:
          - s3
          - gcs
          - azure_blob
```

**2. Run the checker** against your contracts:

```bash
contract-checker
```

With verbose output (shows passing checks too):

```bash
contract-checker --verbose
```

To validate a different location (or a single contract) ad hoc, override the
configured path with `--contract-path`:

```bash
contract-checker --contract-path ./contracts/orders.yaml
```

To also validate each contract against its full JSON Schema (the built-in DCS/ODCS schema, or your custom one) — the equivalent of `datacontract lint` — enable linting. It's off by default:

```bash
contract-checker --lint
```

For the full config-file schema — path filtering, severity overrides, linting, and custom schemas — see the [configuration guide](https://godatadriven.github.io/contract-checker/config/).

---

## Available checks

| Check | YAML key | Description |
|---|---|---|
| Required | `required: true` | Field must exist and be non-null |
| Pattern | `pattern: "^regex$"` | Value must match a regular expression (for list attributes, every item must match) |
| Accepted values | `accepted_values: [a, b]` | Value must be one of the listed options |
| Min items | `min_items: 2` | List or mapping must contain at least N items; skipped if missing, fails if not a collection |
| Max items | `max_items: 10` | List or mapping must contain at most N items; skipped if missing, fails if not a collection |

Only `required` checks whether a field exists: every other check skips an absent field, and every check fails a field that is present but null. See [missing vs null values](https://godatadriven.github.io/contract-checker/checks/#missing-vs-null-values).

See the [checks reference](https://godatadriven.github.io/contract-checker/checks/) for full details and examples of each check type.

---

## Key features

- **Wildcard path support** — apply checks across all models and fields with `models.*.fields.*.unique`
- **Severity levels** — configure checks as `error`, `warn`, or `info`, either globally or per field
- **Contract filtering** — include or exclude contracts with glob patterns (`domain/**`, `**/draft_*.yaml`); filtering by field value (e.g. only `status: active` contracts) is planned
- **Schema validation (lint)** — opt into full JSON Schema validation with `--lint`, against the built-in DCS/ODCS schema or your own custom schema (like `datacontract lint`)
- **Custom JSON Schema** — validate contracts against your own schema, on top of your configured checks
- **Rich output** — colour-coded pass/fail tables per contract plus a summary across all contracts
- **Extensible** — implement the `Check` abstract base class to add your own check types via the Python API

---

## Configuration reference

The full configuration schema — including path filtering, severity overrides, and custom schema options — is documented at [godatadriven.github.io/contract-checker](https://godatadriven.github.io/contract-checker).

---

## Contributing

Bug reports, feature requests, and pull requests are all welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, how to add a new check type, and the PR process.
