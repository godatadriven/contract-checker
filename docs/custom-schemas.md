# Custom Schemas

Custom schema validation lets you validate contracts against any [JSON Schema](https://json-schema.org/) file, without needing to conform to DCS or ODCS formats.

## When to use it

Use `--custom-schema-path` when your contracts follow a domain-specific structure that is not covered by the built-in DCS/ODCS specifications.

## Usage

```bash
contract-checker \
  --contract-path path/to/contracts/ \
  --custom-schema-path path/to/my-schema.json
```

By default, the `custom-checks-config.yml` at the repo root is used as the config file when `--custom-schema-path` is set. To override it:

```bash
contract-checker \
  --contract-path path/to/contracts/ \
  --custom-schema-path path/to/my-schema.json \
  --custom-config-path path/to/other-config.yml
```

## Schema file format

The schema must be a valid JSON Schema document (draft 2019-09 or later recommended):

```json
{
  "$schema": "https://json-schema.org/draft/2019-09/schema",
  "type": "object",
  "required": ["contract_id", "version"],
  "properties": {
    "contract_id": {
      "type": "string",
      "pattern": "^[a-z0-9-]+$"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    }
  }
}
```

## Config file for custom schemas

When using `--custom-schema-path`, a separate config file is used so you can define additional field-level checks alongside schema validation. The default is `custom-checks-config.yml`:

```yaml
data_contract_specification: "custom"
data_contract_checks: []
```

Set `data_contract_checks` to an empty list to rely solely on JSON Schema validation, or add checks the same way as standard config files.

## Validation behaviour

- Each contract YAML is validated against the JSON Schema.
- If validation passes, one result is recorded with `passed: true`.
- If validation fails, one result per schema violation is recorded, each with the field path and error message.
- Config-driven checks (from the config file) and JSON Schema validation always both run — they are not mutually exclusive.
