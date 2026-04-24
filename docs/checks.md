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

### `at_least_one`

Passes when at least one item in a collection satisfies a key-value condition. Use this when a constraint must hold for *some* items rather than *all* items — for example, enforcing that every model has at least one unique field.

Point the `attribute` path at the **collection** (not the leaf attribute), and pass a single-key dict as the check value:

```yaml
data_contract_checks:
  # Every model must have at least one field with unique: true
  - attribute: models.*.fields
    checks:
      - at_least_one: {unique: true}

  # Every model must have at least one primary key field
  - attribute: models.*.fields
    checks:
      - at_least_one: {primaryKey: true}
```

> **Why point at the collection?** Wildcard paths like `models.*.fields.*.unique` are expanded and checked *per field*. Stopping one level up at `models.*.fields` passes the entire fields dict to the check, so it can inspect all fields together.

::: contract_checker.checks.validators
