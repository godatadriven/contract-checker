# Custom Schemas

Alongside the built-in **DCS** and **ODCS** standards, Data Contract Checker can validate your
data contracts against a **custom JSON Schema** that you provide. This is useful when your
contracts follow an in-house format, or an extended version of an existing standard, that the
built-in schemas do not cover.

!!! note "Schema and checks compose"
    A custom schema does **not** replace the attribute-level `data_contract_checks`. When a
    custom schema is set, each contract is validated against the JSON Schema **and** against any
    `data_contract_checks` you configure — both run, and every failure from either is reported.
    Leave `data_contract_checks` empty (or omit it) for schema-only validation, or add checks to
    layer extra rules on top of the schema. See
    [Combining a schema with attribute checks](#combining-a-schema-with-attribute-checks).

The schema you supply must fully describe a valid contract on its own; the checker does not merge
it with the built-in DCS/ODCS schemas.

!!! warning "Enable linting to run schema validation"
    Schema validation is **off by default**. Supplying a custom schema does not by itself validate
    anything — you must also enable [linting](linting.md) with `--lint` or `lint: true`. With
    linting off, the custom schema is ignored; a warning is shown unless you disabled linting
    explicitly (`--no-lint` or `lint: false`).

## Providing a schema

You can point the checker at your schema in two ways. The CLI option always wins when both are set.
In both cases, remember to enable [linting](linting.md).

=== "CLI option"

    ```bash
    contract-checker \
      --lint \
      --contract-path ./data_contracts \
      --custom-schema-path ./schemas/my-contract-schema.json
    ```

=== "Config file"

    In `data-contract-checks.yml`:

    ```yaml
    data_contract_specification: custom
    custom_schema_path: ./schemas/my-contract-schema.json
    lint: true
    data_contract_checks: []
    ```

    Then simply run `contract-checker`.

## The schema must be a valid JSON Schema

Before any contract is checked, the supplied schema is validated against its own meta-schema (the
draft is auto-detected from the schema's `$schema` field). If the schema itself is missing, is not
valid JSON, or is not a valid JSON Schema, the checker **fails fast** with a clear error and a
non-zero exit code — no contracts are validated. The checks config file is validated the same
way (see [How the config file is validated](config.md#how-the-config-file-is-validated)).

```text
Schema is not a valid JSON Schema (./schemas/my-contract-schema.json): 'not-a-valid-type' is not valid under any of the given schemas
```

## How contracts are validated

Each contract found under `--contract-path` is validated against the custom schema. Every schema
violation is reported as an individual result, with the failing attribute path and the underlying
JSON Schema error message.

## Combining a schema with attribute checks

A custom schema and the attribute-level `data_contract_checks` run **together**. This lets you
keep the structural rules in the schema while expressing rules that are awkward in JSON Schema —
or that you want to reuse across standards — as checks. Both are evaluated against every contract
and all failures are reported.

```yaml
data_contract_specification: custom
custom_schema_path: ./schemas/my-contract-schema.json

# Runs in addition to the JSON Schema validation above.
data_contract_checks:
  - attribute: quality_requirements.completeness.critical_fields
    checks:
      - min_items: 1
```

For schema-only validation, set `data_contract_checks: []` (or omit it entirely).

## Extending an existing standard

A custom schema does not have to be an entirely in-house format — it can be an existing standard
with extra rules layered on top. Because JSON Schema's `allOf` requires an instance to satisfy
every subschema, you can reference the base standard and add your own required fields and
constraints:

```json
{
  "$schema": "https://json-schema.org/draft/2019-09/schema",
  "title": "Extended ODCS Data Contract Schema",
  "allOf": [
    { "$ref": "#/$defs/OdcsBase" },
    { "$ref": "#/$defs/HouseRules" }
  ],
  "$defs": {
    "OdcsBase": { "...": "the full ODCS schema" },
    "HouseRules": {
      "type": "object",
      "required": ["description", "domain", "tags", "team"],
      "properties": {
        "status": { "enum": ["draft", "active", "deprecated", "retired"] },
        "tags": { "type": "array", "minItems": 1 }
      }
    }
  }
}
```

A contract must then pass **both** the base standard and your house rules. Because the schema is
standalone, embed the base standard's definitions in `$defs` rather than pointing at a remote URL —
the checker resolves `$ref`s within the file and does not fetch over the network.
[`tests/fixtures/custom/odcs-extended-schema.json`](https://github.com/godatadriven/contract-checker/blob/main/tests/fixtures/custom/odcs-extended-schema.json)
is a complete, working example built on top of ODCS v3.0.2.
