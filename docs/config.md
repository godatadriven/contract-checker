# Configuration

Create a `data-contract-checks.yml` file in your project root to define validation rules for your data contracts.

## Example Configuration

```yaml
data_contract_specification: dcs

data_contract_checks:
  - attribute: info.title
    checks:
      - required: true
      - pattern: ^[A-Z]

  - attribute: info.version
    checks:
      - required: true
      - pattern: ^\d+\.\d+\.\d+$

  - attribute: tags
    checks:
      - accepted_values:
          - production
          - staging
          - development

  - attribute: models.*.fields
    checks:
      - min_items: 1

  - attribute: models.*.fields.*.description
    checks:
      - required: true
```

## Configuration Options

### `data_contract_specification`

Specifies the data contract specification format being used.

```yaml
data_contract_specification: dcs
```

Supported values:

- `dcs` - Data Contract Specification
- `odcs` - Open Data Contract Standard
- `custom` - Validate against a custom JSON Schema (see [Custom Schemas](custom_schemas.md))

### `custom_schema_path`

Path to a custom JSON Schema file. Only used when `data_contract_specification` is `custom`. The
`--custom-schema-path` CLI option overrides this value.

When a custom schema is set, each contract is validated against that JSON Schema **and** against
any `data_contract_checks` you configure — both run. Set `data_contract_checks: []` (or omit it)
for schema-only validation.

```yaml
data_contract_specification: custom
custom_schema_path: ./schemas/my-contract-schema.json
data_contract_checks: []   # or add checks to run on top of the schema
```

See [Custom Schemas](custom_schemas.md) for the full behaviour.

### `data_contracts_path`

Defines where contracts are loaded from, with optional include/exclude filtering:

```yaml
data_contracts_path:
  path: ./contracts/
  include_paths:
    - domain/**              # everything under domain/, any depth
    - source/orders_*.yaml   # matching files directly in source/
  exclude_paths:
    - archive/**             # skip archived contracts
    - "**/draft_*.yaml"      # skip drafts anywhere in the tree
```

Patterns are globs, matched against the full path **relative to `path`** (a leading `/` is
ignored):

- `*` matches within one folder level, `**` crosses levels
- A pattern without wildcards matches exactly one file (e.g. `domain/orders.yaml`)
- If `include_paths` is omitted, every contract is included
- `exclude_paths` is applied after `include_paths` and always wins
- A pattern ending in a bare `/` is rejected with a hint (use `domain/**`, not `domain/`)

If the filters exclude every discovered contract, a warning is logged and the run
exits 1 (no contracts found), so a misconfigured pattern cannot silently produce a
passing run.

A short form is also supported when no filtering is needed:

```yaml
data_contracts_path: ./contracts/
```

The `--contract-path` CLI option overrides `path` — useful for validating a single
contract ad hoc (filters are skipped when it points to a single file).

`include_custom` / `exclude_custom` (filtering by contract field values) are accepted
in the config but not yet implemented; they are ignored with a debug log message.

## Available Checks

For detailed information about available checks and their configuration, see the [Checks](checks.md) page.

## How the config file is validated

The checks file is validated **before any contract is read**. A problem is reported
once, naming the offending entry, and the run exits 1:

```text
ERROR: Invalid checks config: data_contract_checks entry 2 ('info.version'): 'pattern' is not a valid regular expression ('^\d+(.\d+$'): missing ), unterminated subpattern at position 3
```

The following are rejected:

- The file is missing, not valid YAML, empty, or not a mapping at the top level
- `data_contract_checks` is not a list; an entry is not a mapping; an entry has no
  `attribute` or no `checks` list
- A check is not a single-key mapping (`- pattern: ^a` and `required: true` in the same
  item would silently drop one of them, so it is an error instead)
- An unknown check type (the message lists the available ones)
- A check value its check cannot use: `required` must be `true`/`false` (a bare `required:`
  with no value is rejected, since it is almost always a forgotten `true`), `pattern` must be
  a string that compiles as a regular expression, `accepted_values` a non-empty list (or a
  single string), `min_items` / `max_items` a non-negative integer, and `at_least_one` /
  `exactly_one` a single-key mapping
- `data_contract_specification` missing or not one of `dcs`, `odcs` — unless a custom
  schema is given, in which case it is not needed
