# Contributing to `data-contract-checker`

`data-contract-checker` is open source software. Whether you are a seasoned open source contributor or a first-time committer, we welcome and encourage you to contribute code, documentation, ideas, or problem statements to this project.

## About this document

There are many ways to contribute to the ongoing development of `data-contract-checker`, such as by participating in discussions and issues.

The rest of this document serves as a more granular guide for contributing code changes to `data-contract-checker` (this repository). It is not intended as a guide for using `data-contract-checker`, and some pieces assume a level of familiarity with Python development (virtualenvs, `uv`, etc). Specific code snippets in this guide assume you are using macOS or Linux and are comfortable with the command line.

If you get stuck, we're happy to help! Just open an issue or draft PR and we'll do our best to help out.

### Note

- **Branches:** All pull requests from community contributors should target the `main` branch (default).

## Getting the code

### Installing git

You will need `git` in order to download and modify the `data-contract-checker` source code. On macOS, the best way to download git is to just install [Xcode](https://developer.apple.com/support/xcode/).

### Contributors

You can contribute to `data-contract-checker` by forking the `data-contract-checker` repository. For a detailed overview on forking, check out the [GitHub docs on forking](https://help.github.com/en/articles/fork-a-repo). In short, you will need to:

1. Fork the `data-contract-checker` repository.
1. Clone your fork locally.
1. Check out a new branch for your proposed changes.
1. Push changes to your fork.
1. Open a pull request from your forked repository.

## Setting up an environment

There are some tools that will be helpful to you in developing locally. While this is the list relevant for `data-contract-checker` development, many of these tools are used commonly across open-source python projects.

### Tools

These are the tools used in `data-contract-checker` development and testing:

- [`typer`](https://typer.tiangolo.com/) to create our CLI interface.
- [GitHub Actions](https://github.com/features/actions) for automating tests and checks, once a PR is pushed to the `data-contract-checker` repository.
- [`make`](https://www.gnu.org/software/make/manual/make.html) to run multiple setup or test steps in combination.
- [`mypy`](https://mypy.readthedocs.io/en/stable/) for static type checking.
- [`uv`](https://docs.astral.sh/uv/) to manage our python virtual environment and dependencies.
- [`pre-commit`](https://pre-commit.com) to easily run those checks.
- [`Pydantic`](https://docs.pydantic.dev/latest/) for data validation.
- [`pytest`](https://docs.pytest.org/en/latest/) to define, discover, and run tests.
- [`Ruff`](https://github.com/astral-sh/ruff) to lint and format python code.

A deep understanding of these tools in not required to effectively contribute to `data-contract-checker`, but we recommend checking out the attached documentation if you're interested in learning more about each one.

#### Virtual environments

We strongly recommend using virtual environments when developing code in `data-contract-checker`. We recommend creating this virtualenv in the root of the `data-contract-checker` repository. To create and activate a new virtualenv, run:

```shell
uv venv && source .venv/bin/activate
```

This will create a new Python virtual environment in `.venv/` and install all dependencies.

## Running `data-contract-checker` in development

### Installation

First make sure that you set up your `virtualenv` as described in [Setting up an environment](#setting-up-an-environment). Next, install `data-contract-checker`, its dependencies and `pre-commit`:

```shell
make install
uv run pre-commit install
```

When installed in this way, any changes you make to your local copy of the source code will be reflected immediately in your next `data-contract-checker` run.

### Running `data-contract-checker`

With your virtualenv activated, you can run `data-contract-checker` using the provided example configuration file via:

```shell
uv run contract-checker --help
uv run contract-checker --verbose --contract-path tests/fixtures/dcs/1.2.0/
```

## Testing

Once you're able to manually test that your code change is working as expected, it's important to run existing automated tests, as well as adding some new ones. These tests will ensure that:
- Your code changes do not unexpectedly break other established functionality
- Your code changes can handle all known edge cases
- The functionality you're adding will _keep_ working in the future

### Test commands

There are a few methods for running tests locally.

#### `makefile`

There are multiple targets in the `makefile` to run common test suites:

```shell
# Runs unit tests
make test-unit

# Runs all tests
make test
```

#### `pre-commit`
[`pre-commit`](https://pre-commit.com) takes care of running all code-checks for formatting and linting. Run `uv run pre-commit install` to install `pre-commit` in your local environment. Once this is done you can use the git pre-commit hooks to ensure proper formatting and linting.

#### `pytest`

Finally, you can also run a specific test or group of tests using [`pytest`](https://docs.pytest.org/en/latest/) directly. With dev dependencies installed you can do things like:

```shell
# run all unit tests
uv run pytest ./tests/unit

# run all unit tests in a file
uv run pytest ./tests/unit/test_cli.py

# run a specific unit test
uv run pytest ./tests/unit/test_cli.py::test_specific_function
```

> See [pytest usage docs](https://docs.pytest.org/en/8.1.x/how-to/usage.html) for an overview of useful command-line options.

#### ODCS fixtures

`tests/fixtures/odcs/<version>/` holds upstream's ODCS example contracts as they were at release tag `v<version>`, and every one of them is linted against that version's schema. Don't edit them by hand: they are generated by `scripts/update_schemas.py`. To regenerate all of them run:

```shell
uv run python scripts/update_schemas.py --resnapshot-odcs-examples
```

### Assorted development tips

* Append `# type: ignore` to the end of a line if you need to disable `mypy` on that line, preferably with the specific rule to ignore such as `# type: ignore[union-attr]`.

## Adding a new check

To add a new check follow the below steps:

1. In `./src/contract_checker/checks/validators/` create a new file for your check (e.g., `my_check.py`), or add to an existing file if appropriate.

1. Create a new class that inherits from `Check` (from `contract_checker.checks.base`). Your class must:

    - Implement the `check_type` property that returns a unique string identifier (e.g., `"my_custom_check"`).
    - Implement the `execute` method that performs the validation and returns a list of `ValidationResult` objects.
    - Have a clear message in the event of a failure.

    Example:

    ```python
    from typing import Any, List
    from contract_checker.checks.base import Check
    from contract_checker.checks.models import ValidationResult

    class MyCustomCheck(Check):
        @property
        def check_type(self) -> str:
            return "my_custom_check"

        def execute(
            self,
            field_path: str,
            values: List[Any],
            check_value: Any,
        ) -> List[ValidationResult]:
            results = []
            for value in values:
                passed = value is not None  # Your validation logic here
                message = "Passed" if passed else f"Field '{field_path}' failed custom check"
                results.append(
                    ValidationResult("", field_path, self.check_type, passed, message)
                )
            return results
    ```

1. Register your check in `./src/contract_checker/checks/validators/__init__.py` by importing it and adding it to the registry.

1. Add the check to `data-contract-checks.yml` and run `uv run contract-checker` to ensure the check works as expected.

1. Add at least one happy path and one unhappy path test to `./tests/unit/`. The test file should match the check being tested.

1. Run `make test` to ensure the tests pass.

1. Open a PR!

## Submitting a Pull Request

Code can be merged into the current development branch `main` by opening a pull request. If the proposal looks like it's on the right track, then a `data-contract-checker` maintainer will review the PR. They may suggest code revision for style or clarity, or request that you add unit or integration test(s). These are good things! We believe that, with a little bit of help, anyone can contribute high-quality code. Once merged, your contribution will be available for the next release of `data-contract-checker`.

Automated tests run via GitHub Actions. If you're a first-time contributor, all tests will require a maintainer to approve.

Once all tests are passing and your PR has been approved, a `data-contract-checker` maintainer will merge your changes into the active development branch. And that's it! Happy developing :tada:
