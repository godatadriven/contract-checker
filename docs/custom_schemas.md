# Custom Schemas

Alongside the built-in **DCS** and **ODCS** standards, Data Contract Checker can validate your
data contracts against a **custom JSON Schema** that you provide. This is useful when your
contracts follow an in-house format, or an extended version of an existing standard, that the
built-in schemas do not cover.

!!! note "Scope"
    Custom schemas are **standalone**: the schema you supply must fully describe a valid contract
    on its own. Custom schema validation **replaces** the attribute-level `data_contract_checks`
    rather than running alongside them.

## Providing a schema

You can point the checker at your schema in two ways. The CLI option always wins when both are set.

=== "CLI option"

    ```bash
    contract-checker \
      --contract-path ./data_contracts \
      --custom-schema-path ./schemas/my-contract-schema.json
    ```

=== "Config file"

    In `data-contract-checks.yml`:

    ```yaml
    data_contract_specification: custom
    custom_schema_path: ./schemas/my-contract-schema.json
    data_contract_checks: []
    ```

    Then simply run `contract-checker`.

## The schema must be a valid JSON Schema

Before any contract is checked, the supplied schema is validated against its own meta-schema (the
draft is auto-detected from the schema's `$schema` field). If the schema itself is missing, is not
valid JSON, or is not a valid JSON Schema, the checker **fails fast** with a clear error and a
non-zero exit code — no contracts are validated.

```text
Custom schema is not a valid JSON Schema (./schemas/my-contract-schema.json): 'not-a-valid-type' is not valid under any of the given schemas
```

## How contracts are validated

Each contract found under `--contract-path` is validated against the custom schema. Every schema
violation is reported as an individual result, with the failing attribute path and the underlying
JSON Schema error message.
