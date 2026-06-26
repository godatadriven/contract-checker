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

## Available Checks

For detailed information about available checks and their configuration, see the [Checks](checks.md) page.
