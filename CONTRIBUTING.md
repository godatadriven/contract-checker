# Contributing to Data Contract Checker

Contributions are welcome — bug reports, feature requests, documentation improvements, and code all help.

## Reporting issues

Use [GitHub Issues](https://github.com/godatadriven/contract-checker/issues) to report bugs or request features. Include:
- Your Python version and `contract-checker` version
- A minimal reproducible example (contract file + config)
- The actual vs expected output

## Development setup

**Requirements:** Python 3.11–3.15, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/godatadriven/contract-checker.git
cd contract-checker
make install                 # install all dependencies
uv run pre-commit install    # install pre-commit hooks
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
from typing import Any, List

from contract_checker.checks.base import Check
from contract_checker.checks.models import ValidationResult

class MyCheck(Check):
    @property
    def check_type(self) -> str:
        return "my_check"

    def execute(self, field_path: str, values: List[Any], check_value: Any) -> List[ValidationResult]:
        results = []
        for value in values:
            passed = ...  # your logic here
            message = "Passed" if passed else f"Field '{field_path}' failed my_check"
            results.append(ValidationResult("", field_path, self.check_type, passed, message))
        return results
```

3. Export it from `src/contract_checker/checks/validators/__init__.py` and register it in
   `src/contract_checker/checks/registry.py`
4. Add tests in `tests/unit/test_checks.py` and document the check in `docs/checks.md` and the
   README's checks table

See the [contributing guide](https://godatadriven.github.io/contract-checker/contributing/#adding-a-new-check)
for the full walkthrough, including config validation with `validate_config`.

## Submitting a pull request

1. Fork the repository and create a branch from `main`
2. Make your changes and ensure all tests pass (`make test`)
3. Open a pull request — describe what you changed and why. Use a
   [Conventional Commits](https://www.conventionalcommits.org/) title, e.g. `feat: add unique check`
   or `fix: handle null lists in pattern check`. PRs are squash-merged, so the PR title becomes the
   commit message on `main` — no need to tidy up the individual commits on your branch
4. A code owner reviews and approves the PR; CI must pass before it can be merged

Releases are cut by maintainers; see [Releasing](https://godatadriven.github.io/contract-checker/releasing/).
