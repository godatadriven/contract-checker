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

If the filters exclude every discovered contract, a warning is logged so a
misconfigured pattern cannot silently produce a passing run.

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
