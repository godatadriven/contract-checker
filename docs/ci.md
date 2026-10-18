# GitHub Actions

Run `contract-checker` as part of your CI pipeline to validate your data contracts on every push or pull request.

## Example Workflow

Create a file at `.github/workflows/data-contract-check.yml`:

```yaml
name: Data Contract Validation

on:
  pull_request:
    branches: [main]

jobs:
  validate-contracts:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
            python-version: 3.13

      - name: Sync uv dependencies
        run: uv sync

      - name: Run contract-checker
        run: |
          contract-checker --contract-path path/to/your/datacontracts.yaml
```

## Pull request annotations

When contract-checker detects it is running inside GitHub Actions, every failed
check is emitted as an [error annotation](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#setting-an-error-message):
GitHub renders these inline on the contract files in the pull request's
"Files changed" tab, so authors see exactly what failed without opening the logs.
No configuration is needed; pass `--no-annotations` to turn this off.

A failing check also makes the step exit non-zero (see
[exit codes](cli.md#exit-codes)), so the workflow fails and can block the merge.
Use `--severity warn` while rolling out new checks to keep the report visible
without failing the pipeline.

Two things fail the step even with `--severity warn`: a contract file that cannot be
loaded at all (not valid YAML, unsupported specification version, …), which is also
annotated on the file with the title `load`, and a run that finds no contracts to check.
Both mean the checker could not do its job, which should never look like a green build.
