# Checks

This page contains information about the validation checks available in ```data-contract-checker```.

### `at_least_one`

Passes when at least one item in a collection satisfies a key-value condition. Use this when a constraint must hold for *some* items rather than *all* items — for example, enforcing that every model has at least one unique field.

Point the `attribute` path at the **collection** (not the leaf attribute), and specify a single key-value pair as the check value using a YAML block mapping:

```yaml
data_contract_checks:
  # Every model must have at least one field with unique: true
  - attribute: models.*.fields
    checks:
      - at_least_one:
          unique: true

  # Every model must have at least one primary key field
  - attribute: models.*.fields
    checks:
      - at_least_one:
          primaryKey: true
```

> **Why point at the collection?** Wildcard paths like `models.*.fields.*.unique` are expanded and checked *per field*. Stopping one level up at `models.*.fields` passes the entire fields dict to the check, so it can inspect all fields together.
