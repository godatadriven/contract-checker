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

> **Per-model, not aggregated.** When the attribute path contains a wildcard (e.g. `models.*.fields`), the check runs **once per expanded path** — once for each model in this example. Each model must independently satisfy the condition; results are **not** pooled across models. If two of three models have a `unique: true` field and one does not, you'll get two pass results and one fail, not a single combined verdict. To require that at least one unique field exists *somewhere* across all models, point `attribute` at a non-wildcarded path instead.

**Check value shape.** `at_least_one` requires a **single-key mapping**, for example:

```yaml
checks:
  - at_least_one:
      unique: true
```

Multi-key mappings, empty mappings, and non-mapping values (scalars, lists) are rejected with a failing result.
