# Checks

This page contains lists all validation checks available in `data-contract-checker`.

## Attribute paths

Checks are applied to attributes identified by dot-notation paths, e.g. `info.title` or `models.order.fields.id.description`.

Use `*` as a wildcard segment to match every repeated item at that level. Contract standards represent repeatable objects differently, and `*` handles both:

- **Dicts keyed by name** (DCS style): `*` expands over the dict entries.
- **Lists of named objects** (ODCS style): `*` expands over the list items. Each concrete path is labeled with the item's `name` when it has one, falling back to the item's index.

```yaml
data_contract_checks:
  # DCS: checks every model's fields collection
  - attribute: models.*.fields
    checks:
      - min_items: 1

  # DCS: checks the description of every field in every model
  - attribute: models.*.fields.*.description
    checks:
      - required: true

  # ODCS: checks the logical type of every property in every schema object
  - attribute: schema.*.properties.*.logicalType
    checks:
      - required: true
```

Wildcards can appear at any level and can be combined freely within the same path.

**Resolving `name`.** A `name` leaf directly after a `*` works for both styles: in list-style contracts it reads the item's explicit `name` value, and in dict-style contracts — where the item's name is the key itself — it resolves to the key (an explicit `name` value inside the entry wins over the key). So `models.*.fields.*.name` yields field names regardless of the standard.

**Lists without wildcards.** A non-wildcard segment applied to a list is transparent: it applies to each item, and the matched values are merged under a single path (e.g. `servers.type` collects the `type` of every server). Use `*` when you want checks to run per item instead.

## Missing vs null values

All checks follow the same rule for attributes that are absent or empty:

- **Absent key**: skipped by every check except `required`. The check produces no result, so a field can be present in some contracts and not in others.
- **Key present but null** (`owner:` with no value, `owner: null`, or `owner: ~`): fails every check with `Attribute '<path>' is null`.
- **Null elements inside a value** (`tags: [a, null]`, or a `null` entry in a `fields` mapping): fail with `Attribute '<path>' contains N null element(s)`. Null elements are not counted by `min_items` / `max_items`.

| Contract | `required: true` | Any other check |
|---|---|---|
| `info: {title: X}` (no `owner`) | FAIL: is missing | no result |
| `info: {owner: null}` | FAIL: is null | FAIL: is null |
| `info: {owner: alice}` | PASS | checked normally |

To make a field mandatory, add `required: true`. The other checks never enforce presence:

```yaml
data_contract_checks:
  # Optional: if tags are present, there must be at least one
  - attribute: info.tags
    checks:
      - min_items: 1

  # Mandatory: tags must be present and have at least one item
  - attribute: info.tags
    checks:
      - required: true
      - min_items: 1
```

`required: false` produces no result. You can still write it to document that a field is optional.

A null *parent* (e.g. `info: null`) makes every path below it absent, so `info.owner` is reported as missing by `required` and skipped by the other checks. Add a check on `info` itself to report it as null.

Empty values (`""`, `[]`, `{}`) are not null. They count as present.

See [Pass and fail examples](check_examples.md) for every check run against real contracts.

## Available checks

::: contract_checker.checks.validators
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

### `exactly_one`

Passes when **exactly one** item in a collection satisfies a key-value condition — not zero, not two, not more. Use this when a constraint must hold for a *single* designated item. The motivating case is primary-key enforcement: a model with two `primaryKey: true` fields is a modelling bug that `at_least_one` silently accepts.

Point the `attribute` path at the **collection** (not the leaf attribute), and specify a single key-value pair as the check value using a YAML block mapping:

```yaml
data_contract_checks:
  # Every model must have exactly one primary key field
  - attribute: models.*.fields
    checks:
      - exactly_one:
          primaryKey: true

  # Every model must have exactly one event-time timestamp field
  - attribute: models.*.fields
    checks:
      - exactly_one:
          type: timestamp
```

Failure messages include the actual count, e.g. `has 2 items with 'primaryKey: true', expected exactly 1`.

> **Why point at the collection?** Wildcard paths like `models.*.fields.*.primaryKey` are expanded and checked *per field*. Stopping one level up at `models.*.fields` passes the entire fields dict to the check, so it can count all matching fields together.

> **Per-model, not aggregated.** When the attribute path contains a wildcard (e.g. `models.*.fields`), the check runs **once per expanded path** — once for each model in this example. Each model must independently have *exactly one* match; results are **not** pooled across models. To require a single designated item across *all* models, point `attribute` at a non-wildcarded path instead.

> **Check-value shape contract.** `exactly_one` requires a **single-key** mapping. Anything else fails loudly:
>
> | `check_value`                                  | Result                           |
> |------------------------------------------------|----------------------------------|
> | `{primaryKey: true}`                           | OK — checked                     |
> | `{primaryKey: true, unique: true}`             | FAIL — multi-key rejected        |
> | `{}`                                           | FAIL — empty mapping rejected    |
> | `true` / `"unique"` / `[primaryKey]` / `null`  | FAIL — non-mapping rejected      |
