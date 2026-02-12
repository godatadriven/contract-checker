# Checks

This page contains information about the validation checks available in `data-contract-checker`.

## Overview

Data Contract Checker provides a set of built-in validation checks that can be applied to data contract attributes. These checks are configured in your `data-contract-checks.yml` file and are automatically executed during validation.

### Quick Reference

| Check | Purpose | Example |
|-------|---------|---------|
| `required` | Ensure field exists and is not null | `required: true` |
| `pattern` | Validate against regex pattern | `pattern: ^[A-Z]` |
| `accepted_values` | Validate against allowed values | `accepted_values: [a, b, c]` |
| `min_items` | Ensure list has minimum items | `min_items: 1` |
| `max_items` | Ensure list doesn't exceed max items | `max_items: 10` |

### Configuration Example

```yaml
data_contract_checks:
  - attribute: info.title
    checks:
      - required: true
      - pattern: ^Orders

  - attribute: tags
    checks:
      - accepted_values:
          - production
          - staging
      - min_items: 1
      - max_items: 5
```

---

## Validators Module

::: contract_checker.checks.validators
    options:
      show_root_heading: true
      show_root_toc_entry: true
      members_order: source

---

## Built-in Checks

### RequiredCheck

::: contract_checker.checks.validators.RequiredCheck
    options:
      show_root_heading: true
      show_source: true
      members:
        - check_type
        - execute

---

### PatternCheck

::: contract_checker.checks.validators.PatternCheck
    options:
      show_root_heading: true
      show_source: true
      members:
        - check_type
        - execute

---

### AcceptedValuesCheck

::: contract_checker.checks.validators.AcceptedValuesCheck
    options:
      show_root_heading: true
      show_source: true
      members:
        - check_type
        - execute

---

### MinItemsCheck

::: contract_checker.checks.validators.MinItemsCheck
    options:
      show_root_heading: true
      show_source: true
      members:
        - check_type
        - execute

---

### MaxItemsCheck

::: contract_checker.checks.validators.MaxItemsCheck
    options:
      show_root_heading: true
      show_source: true
      members:
        - check_type
        - execute

---

## Base Check Class

For creating custom checks, you can inherit from the base `Check` class:

::: contract_checker.checks.base.Check
    options:
      show_root_heading: true
      show_source: true
      members:
        - execute
        - check_type
