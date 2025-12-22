# contract-checker
An open source Python package that is able to parse data contract standards and allows users to configure checks

## Project Structure

```
checks/
├── __init__.py              # Main module with backward compatibility
├── base.py                  # Abstract base classes - contract definitions for extensibility
├── models.py                # Data structures
├── registry.py              # Check registry system
├── validator.py             # Core validation logic - path traversal and validation orchestration
├── reporting.py             # Output formatting and reporting
└── validators/              # Individual check implementations - each check type in its own file
    ├── __init__.py         
    ├── required_check.py    # Required field validation
    ├── pattern_check.py     # Regex pattern validation
    └── items_check.py       # Min/max items validation
```


### How to use the Data Contract Checker
1. Define your validation rules in ```data-contract-checks.yml```. This YAML file should specify the validation rules for your data contracts, such as required fields, regex patterns, or item count constraints.
2. Run the CLI based validator to check your data.
3. Review the output for any issues.


Example validation rules:
```fields:
  name:
    required: true
    pattern: "^[A-Za-z ]+$"
  age:
    required: true
    min: 0
    max: 120
  tags:
    min_items: 1
    max_items: 5    
```


# How to run locally
- Initialize venv
- ```uv sync``` to synchronize dependencies from `uv.lock`
- ```uv run python -m contract_checker.cli --help``` to see available commands
- ```uv run python -m contract_checker.cli --verbose --contract-path tests/fixtures/dcs/1.2.0/``` to run with a sample contract using dcs standard
