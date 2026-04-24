# Checks

This page contains lists all validation checks available in `data-contract-checker`.

## Attribute paths

Checks are applied to attributes identified by dot-notation paths, e.g. `info.title` or `models.order.fields.id.description`.

Use `*` as a wildcard segment to match all keys at that level:

```yaml
data_contract_checks:
  # Checks every model's fields list
  - attribute: models.*.fields
    checks:
      - min_items: 1

  # Checks the description of every field in every model
  - attribute: models.*.fields.*.description
    checks:
      - required: true
```

Wildcards can appear at any level and can be combined freely within the same path.

## Available checks

::: contract_checker.checks.validators
