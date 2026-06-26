---
name: add-check
description: "Scaffold a new check type (validator file, registry, tests, docs)"
argument-hint: "<check-name>"
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
---

<objective>
Scaffold all the boilerplate for a new check type in the contract-checker project. Given a check name in snake_case, create the validator file, register it, export it, add a test class stub, and add a docs placeholder — so the developer only needs to fill in the business logic.
</objective>

<context>
$ARGUMENTS is the check name in snake_case (e.g. `at_least_one`, `not_null`, `min_length`).

Key paths (all relative to the repo root):
- New validator:  `src/contract_checker/checks/validators/<check_name>_check.py`
- Exports:        `src/contract_checker/checks/validators/__init__.py`
- Registry:       `src/contract_checker/checks/registry.py`
- Tests:          `tests/unit/test_checks.py`
- Docs:           `docs/checks.md`

Naming convention:
- File stem:   `<check_name>_check`  (e.g. `at_least_one_check`)
- Class name:  CamelCase + `Check`   (e.g. `AtLeastOneCheck`)
- check_type:  `<check_name>` as-is  (e.g. `at_least_one`)
</context>

<process>
1. Parse `$ARGUMENTS` to derive `check_name`, `class_name`, and `file_stem`.

2. Read `src/contract_checker/checks/validators/__init__.py` and `src/contract_checker/checks/registry.py` to confirm the current state and avoid duplicate entries.

3. Write `src/contract_checker/checks/validators/<file_stem>.py` using this template (substitute all placeholders):

```python
"""<check_name> validation check."""

from typing import Any, List

from ..base import Check
from ..models import ValidationResult


class <ClassName>(Check):
    """TODO: describe what this check does.

    Example configuration:

    ```yaml
    data_contract_checks:
      - attribute: <some.path>
        checks:
          - <check_name>: <value>
    ```
    """

    @property
    def check_type(self) -> str:
        return "<check_name>"

    def execute(
        self,
        attribute_path: str,
        values: List[Any],
        check_value: Any,  # noqa: ANN401
    ) -> List[ValidationResult]:
        # TODO: implement validation logic. Remove this raise once implemented.
        raise NotImplementedError(
            f"{self.check_type} check is not implemented yet"
        )
```

The scaffolded `execute` raises `NotImplementedError` intentionally — a freshly scaffolded check should fail loudly in tests until it's implemented, rather than silently pass.

4. Edit `src/contract_checker/checks/validators/__init__.py`:
   - Add `from .<file_stem> import <ClassName>` in alphabetical order with the existing imports
   - Add `"<ClassName>"` to `__all__` in alphabetical order

5. Edit `src/contract_checker/checks/registry.py`:
   - Add `from .validators.<file_stem> import <ClassName>` with the existing imports
   - Add `<ClassName>()` to the `default_checks` list inside `_register_default_checks`

6. Edit `tests/unit/test_checks.py`:
   - Add `<ClassName>` to the import from `contract_checker.checks.validators`
   - Append this test class stub at the end of the file:

```python
class Test<ClassName>:
    """Test <ClassName> functionality."""

    def setup_method(self) -> None:
        self.check = <ClassName>()

    def test_check_passes(self) -> None:
        """TODO: test the passing case."""
        results = self.check.execute("test.field", [<passing_input>], <check_value>)
        assert len(results) == 1
        assert results[0].passed is True

    def test_check_fails(self) -> None:
        """TODO: test the failing case."""
        results = self.check.execute("test.field", [<failing_input>], <check_value>)
        assert len(results) == 1
        assert results[0].passed is False

    def test_missing_attribute(self) -> None:
        """Test check fails when attribute is missing."""
        results = self.check.execute("test.field", [], <check_value>)
        assert len(results) == 1
        assert results[0].passed is False
```

7. Edit `docs/checks.md` — insert before the final `::: contract_checker.checks.validators` autodoc line:

```markdown
### `<check_name>`

TODO: describe this check.

```yaml
data_contract_checks:
  - attribute: <some.path>
    checks:
      - <check_name>: <value>
```
```

8. Print a summary of all files created/modified and remind the developer to:
   - Implement `execute()` logic in the new validator file
   - Replace `TODO` stubs in the test class with real assertions and inputs
   - Fill in the docs description and example
</process>
