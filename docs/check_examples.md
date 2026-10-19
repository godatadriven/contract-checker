# Pass and fail examples

Each example below was run through the checker. The comment at the top of each contract is the exact result it reports. The examples follow the rule in [Missing vs null values](checks.md#missing-vs-null-values):

- **Key missing** (no line for it): only `required` fails. Every other check is skipped and adds no result to the report.
- **Key left blank** (`owner:` with nothing after it): every check fails with `Attribute '<path>' is null`.
- **Blank item** (a `-` with nothing after it, or a blank entry under `fields:`): fails with `contains N null element(s)` and isn't counted by `min_items` / `max_items`.

Empty values such as `""` or `[]` are not blank: they count as filled in.

## `required`

`required: true` fails when the key is missing or left blank. It is the only check that looks at whether a key exists.

```yaml
data_contract_checks:
  - attribute: info.owner
    checks:
      - required: true
```

=== "Passes"

    ```yaml
    # Owner filled in
    #   PASS: Attribute 'info.owner' is present
    info:
      title: Orders
      owner: alice
    ---
    # Owner is an empty string
    #   PASS: Attribute 'info.owner' is present
    info:
      title: Orders
      owner: ""
    ```

=== "Fails"

    ```yaml
    # Owner line missing
    #   FAIL: Required attribute 'info.owner' is missing
    info:
      title: Orders
    ---
    # Owner left blank
    #   FAIL: Required attribute 'info.owner' is null
    info:
      title: Orders
      owner:
    ```

`required: false` adds nothing to the report, whatever the contract holds. Write it only to document that a field is optional.

```yaml
data_contract_checks:
  - attribute: info.owner
    checks:
      - required: false
```

=== "Skipped"

    ```yaml
    # Owner filled in
    #   (no result)
    info:
      title: Orders
      owner: alice
    ---
    # Owner line missing
    #   (no result)
    info:
      title: Orders
    ---
    # Owner left blank
    #   (no result)
    info:
      title: Orders
      owner:
    ```

## `pattern`

`pattern` fails a value that doesn't match the regular expression, or a key left blank. It skips a missing key.

```yaml
data_contract_checks:
  - attribute: info.owner
    checks:
      - pattern: ^[a-z]+$
```

=== "Passes"

    ```yaml
    # Lowercase owner
    #   PASS: Attribute 'info.owner' value 'alice' matches pattern '^[a-z]+$'
    info:
      title: Orders
      owner: alice
    ```

=== "Fails"

    ```yaml
    # Capitalised owner
    #   FAIL: Attribute 'info.owner' value 'Alice' does not match pattern '^[a-z]+$'
    info:
      title: Orders
      owner: Alice
    ---
    # Owner left blank
    #   FAIL: Attribute 'info.owner' is null
    info:
      title: Orders
      owner:
    ```

=== "Skipped"

    ```yaml
    # Owner line missing
    #   (no result)
    info:
      title: Orders
    ```

## `accepted_values`

`accepted_values` fails a value that isn't in the list, a key left blank, or a blank item in a list. A list gets one result per item.

Values are compared with the type the contract specification gives the field. DCS types
`pii` as a boolean, so the config uses an unquoted `false`:

```yaml
data_contract_checks:
  - attribute: models.*.fields.*.pii
    checks:
      - accepted_values: [false]   # no field may contain PII
```

A quoted `"false"` is a string and never matches the boolean `false`, the same way
`--lint` rejects `pii: "false"` in a contract. A failure caused by quotes says so in its
message. Numbers match by value, so `1` and `1.0` are the same.

Dates and timestamps are strings in every supported specification, so both the contract
and the checks config keep them as the text that was written, quoted or not:
`accepted_values: [2024-01-01T00:00:00Z]` matches a contract `contractCreatedTs: 2024-01-01T00:00:00Z`.

```yaml
data_contract_checks:
  - attribute: info.env
    checks:
      - accepted_values:
          - prod
          - dev
```

=== "Passes"

    ```yaml
    # Allowed value
    #   PASS: Attribute 'info.env' value 'prod' is in the list of accepted values
    info:
      title: Orders
      env: prod
    ---
    # List of allowed values
    #   PASS: Attribute 'info.env' value 'prod' is in the list of accepted values
    #   PASS: Attribute 'info.env' value 'dev' is in the list of accepted values
    info:
      title: Orders
      env:
        - prod
        - dev
    ```

=== "Fails"

    ```yaml
    # Value not in the list
    #   FAIL: Attribute 'info.env' value 'test' is not in the list of accepted values: '['prod', 'dev']'
    info:
      title: Orders
      env: test
    ---
    # List with one bad value
    #   PASS: Attribute 'info.env' value 'prod' is in the list of accepted values
    #   FAIL: Attribute 'info.env' value 'test' is not in the list of accepted values: '['prod', 'dev']'
    info:
      title: Orders
      env:
        - prod
        - test
    ---
    # Env left blank
    #   FAIL: Attribute 'info.env' is null
    info:
      title: Orders
      env:
    ---
    # List with an empty item
    #   FAIL: Attribute 'info.env' contains 1 null element(s)
    #   PASS: Attribute 'info.env' value 'prod' is in the list of accepted values
    info:
      title: Orders
      env:
        - prod
        -
    ```

=== "Skipped"

    ```yaml
    # Env line missing
    #   (no result)
    info:
      title: Orders
    ```

## `min_items`

`min_items` fails a list with too few items, a key left blank, or a blank item in the list. Blank items are not counted.

```yaml
data_contract_checks:
  - attribute: info.tags
    checks:
      - min_items: 2
```

=== "Passes"

    ```yaml
    # Two tags
    #   PASS: Attribute 'info.tags' has at least 2 items
    info:
      title: Orders
      tags:
        - orders
        - sales
    ```

=== "Fails"

    ```yaml
    # One tag
    #   FAIL: Attribute 'info.tags' has fewer than 2 items
    info:
      title: Orders
      tags:
        - orders
    ---
    # Empty list
    #   FAIL: Attribute 'info.tags' has fewer than 2 items
    info:
      title: Orders
      tags: []
    ---
    # Tags left blank
    #   FAIL: Attribute 'info.tags' is null
    info:
      title: Orders
      tags:
    ---
    # One tag plus an empty item
    #   FAIL: Attribute 'info.tags' contains 1 null element(s)
    #   FAIL: Attribute 'info.tags' has fewer than 2 items
    info:
      title: Orders
      tags:
        - orders
        -
    ---
    # Two tags plus an empty item
    #   FAIL: Attribute 'info.tags' contains 1 null element(s)
    #   PASS: Attribute 'info.tags' has at least 2 items
    info:
      title: Orders
      tags:
        - orders
        - sales
        -
    ```

=== "Skipped"

    ```yaml
    # Tags line missing
    #   (no result)
    info:
      title: Orders
    ```

## `max_items`

`max_items` fails a list with too many items, a key left blank, or a blank item in the list. Blank items are not counted.

```yaml
data_contract_checks:
  - attribute: info.tags
    checks:
      - max_items: 2
```

=== "Passes"

    ```yaml
    # Two tags
    #   PASS: Attribute 'info.tags' has at most 2 items
    info:
      title: Orders
      tags:
        - orders
        - sales
    ```

=== "Fails"

    ```yaml
    # Three tags
    #   FAIL: Attribute 'info.tags' has more than 2 items
    info:
      title: Orders
      tags:
        - orders
        - sales
        - finance
    ---
    # Tags left blank
    #   FAIL: Attribute 'info.tags' is null
    info:
      title: Orders
      tags:
    ---
    # Two tags plus an empty item
    #   FAIL: Attribute 'info.tags' contains 1 null element(s)
    #   PASS: Attribute 'info.tags' has at most 2 items
    info:
      title: Orders
      tags:
        - orders
        - sales
        -
    ```

=== "Skipped"

    ```yaml
    # Tags line missing
    #   (no result)
    info:
      title: Orders
    ```

## `at_least_one`

`at_least_one` fails when no field matches, when `fields:` is left blank, or when a field under it is left blank. Point it at the collection; it runs once per model.

```yaml
data_contract_checks:
  - attribute: models.*.fields
    checks:
      - at_least_one:
          primaryKey: true
```

=== "Passes"

    ```yaml
    # One primary key
    #   PASS: Attribute 'models.orders.fields' contains at least one item with 'primaryKey: True'
    models:
      orders:
        fields:
          order_id:
            type: text
            primaryKey: true
          amount:
            type: decimal
    ---
    # Two primary keys
    #   PASS: Attribute 'models.orders.fields' contains at least one item with 'primaryKey: True'
    models:
      orders:
        fields:
          order_id:
            primaryKey: true
          customer_id:
            primaryKey: true
    ```

=== "Fails"

    ```yaml
    # No primary key
    #   FAIL: Attribute 'models.orders.fields' has no items with 'primaryKey: True'
    models:
      orders:
        fields:
          order_id:
            type: text
          amount:
            type: decimal
    ---
    # Fields left blank
    #   FAIL: Attribute 'models.orders.fields' is null
    models:
      orders:
        description: All orders
        fields:
    ---
    # A field left blank
    #   FAIL: Attribute 'models.orders.fields' contains 1 null element(s): amount
    #   PASS: Attribute 'models.orders.fields' contains at least one item with 'primaryKey: True'
    models:
      orders:
        fields:
          order_id:
            primaryKey: true
          amount:
    ```

=== "Skipped"

    ```yaml
    # Fields line missing
    #   (no result)
    models:
      orders:
        description: All orders
    ```

## `exactly_one`

`exactly_one` fails when zero, or two or more, fields match, when `fields:` is left blank, or when a field under it is left blank. Point it at the collection; it runs once per model.

```yaml
data_contract_checks:
  - attribute: models.*.fields
    checks:
      - exactly_one:
          primaryKey: true
```

=== "Passes"

    ```yaml
    # One primary key
    #   PASS: Attribute 'models.orders.fields' contains exactly one item with 'primaryKey: True'
    models:
      orders:
        fields:
          order_id:
            type: text
            primaryKey: true
          amount:
            type: decimal
    ```

=== "Fails"

    ```yaml
    # Two primary keys
    #   FAIL: Attribute 'models.orders.fields' has 2 items with 'primaryKey: True', expected exactly 1
    models:
      orders:
        fields:
          order_id:
            primaryKey: true
          customer_id:
            primaryKey: true
    ---
    # No primary key
    #   FAIL: Attribute 'models.orders.fields' has 0 items with 'primaryKey: True', expected exactly 1
    models:
      orders:
        fields:
          order_id:
            type: text
          amount:
            type: decimal
    ---
    # Fields left blank
    #   FAIL: Attribute 'models.orders.fields' is null
    models:
      orders:
        description: All orders
        fields:
    ---
    # A field left blank
    #   FAIL: Attribute 'models.orders.fields' contains 1 null element(s): amount
    #   PASS: Attribute 'models.orders.fields' contains exactly one item with 'primaryKey: True'
    models:
      orders:
        fields:
          order_id:
            primaryKey: true
          amount:
    ```

=== "Skipped"

    ```yaml
    # Fields line missing
    #   (no result)
    models:
      orders:
        description: All orders
    ```
