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
          contract-checker --contract-path path/to/your/datacontract.yaml
```
