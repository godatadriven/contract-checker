# Contributing to Data Contract Checker

Contributions are welcome — bug reports, feature requests, documentation improvements, and code all help.

## Reporting issues

Use [GitHub Issues](https://github.com/godatadriven/contract-checker/issues) to report bugs or request features. Include:
- Your Python version and `contract-checker` version
- A minimal reproducible example (contract file + config)
- The actual vs expected output

## Development setup

**Requirements:** Python 3.10+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/godatadriven/contract-checker.git
cd contract-checker
make install          # install all dependencies
pre-commit install    # install pre-commit hooks
```

## Running tests

```bash
make test             # unit + integration tests
make test-unit        # unit tests only
make test-integration # integration tests only
```

## Adding a new check

1. Create a new file in `src/contract_checker/checks/validators/`
2. Implement the `Check` abstract base class from `contract_checker.checks.base`:

```python
from contract_checker.checks.base import Check
from contract_checker.checks.models import ValidationResult

class MyCheck(Check):
    @property
    def check_type(self) -> str:
        return "my_check"

    def execute(self, attribute: str, value: object, config: object) -> ValidationResult:
        passed = ...  # your logic here
        return ValidationResult(
            attribute=attribute,
            check_type=self.check_type,
            passed=passed,
            message="..." if not passed else "",
        )
```

3. Register it in `src/contract_checker/checks/registry.py`
4. Add tests in `tests/unit/`

## Submitting a pull request

1. Fork the repository and create a branch from `main`
2. Make your changes and ensure all tests pass (`make test`)
3. Open a pull request — describe what you changed and why
