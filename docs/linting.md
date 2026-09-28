# Schema Validation (Lint)

Beyond the attribute-level [`data_contract_checks`](checks.md), Data Contract Checker can validate
each contract against its **full JSON Schema**. This is the equivalent of a `datacontract lint`
step: it confirms the contract is structurally valid against the specification, catching things
like unknown fields, wrong types, and missing required keys.

This works for both:

- **Standard contracts** — validated against the built-in **DCS** / **ODCS** schema for the
  contract's specification and version.
- **Custom contracts** — validated against the [custom JSON Schema](custom_schemas.md) you supply.

## Opt-in: off by default

Schema validation is **disabled by default**. Enable it with the `--lint` flag or the `lint` key
in your checks config. This keeps the default run focused on your configured checks; turn linting
on when you also want full structural validation.

=== "CLI flag"

    ```bash
    contract-checker --lint
    ```

    Use `--no-lint` to force it off regardless of the config file.

=== "Config file"

    In `data-contract-checks.yml`:

    ```yaml
    lint: true
    ```

The CLI flag always wins over the config value. The config value must be a YAML boolean; a quoted
`"false"` (or any other non-boolean) is rejected with an error instead of being guessed at.

!!! note "A custom schema alone does not enable linting"
    Providing `custom_schema_path` (or `--custom-schema-path`) does **not** turn on validation by
    itself — `lint` must be enabled. When linting is off, the custom schema is ignored and a note
    is logged.

## What gets validated

| `lint`   | `custom_schema_path` set? | Validated against |
|----------|---------------------------|-------------------|
| off      | either                    | nothing (schema validation skipped) |
| on       | no                        | built-in schema for the contract's spec/version |
| on       | yes                       | the custom schema |

Schema validation runs **in addition** to `data_contract_checks` — both run, and every failure
from either is reported. Set `data_contract_checks: []` (or omit it) for schema-only validation.

## Example

Lint every DCS contract in a directory against the built-in DCS schema:

```yaml
# data-contract-checks.yml
data_contract_specification: dcs
lint: true
data_contracts_path:
  path: ./contracts/
data_contract_checks: []
```

```bash
contract-checker
```

A contract with, for example, an unsupported field type is reported as a failure:

```text
✗ FAIL   JSON_SCHEMA   models.orders.fields.attributes   Schema validation failed:
         'array<struct<...>>' is not one of ['number', 'decimal', ... 'struct', ...]
```

For custom schemas — including extending an existing standard with in-house rules — see
[Custom Schemas](custom_schemas.md).
