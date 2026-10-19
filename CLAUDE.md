# contract-checker

CLI (`contract-checker`, built with Typer) that validates data contracts (DCS / ODCS YAML files) against
rules defined in a checks config (`data-contract-checks.yml`), and optionally against the full JSON Schema
of the contract standard ("lint").

## Commands

```bash
uv sync --group dev --group lint          # install (make install also adds docs)
uv run pytest                             # all tests (make test-unit / make test-integration)
uv run pre-commit run --all-files         # ruff, ruff-format, mypy + hygiene hooks
uv run contract-checker                   # run against the example config in the repo root
uv run mkdocs serve                       # docs (needs --group docs)
```

CI (`.github/workflows/ci.yml`) runs pre-commit, then pytest on Python 3.11–3.15 × ubuntu/windows.
Keep code compatible with Python 3.11 and with Windows paths.

## Layout

```
src/contract_checker/
  cli.py                     # Typer app; all options live on the `main` callback
  checks/
    base.py                  # Check ABC — the contract every check implements
    registry.py              # CheckRegistry: maps check_type -> Check instance
    validator.py             # DataContractValidator: path expansion, null handling, lint, runs checks
    reporting.py             # text / json output, GitHub annotations, summary tables
    models.py                # ValidationResult, ContractValidationReport (dataclasses)
    validators/*_check.py    # one file per check type
  contract/contract_base.py  # Contract pydantic model + standard schema path lookup
  contract_schemas/{dcs,odcs}/{version}/schema.json   # vendored standard schemas
  utils/                     # config parsing, contract loading, path filters, schema loading
tests/unit/                  # per-module tests (test_checks.py holds all check tests)
tests/integration/           # end-to-end validator / lint / custom schema tests
tests/fixtures/{dcs,odcs,custom}/
docs/                        # mkdocs site; docs/checks.md documents every check
scripts/update_schemas.py    # used by update-schemas.yml to vendor new schema versions monthly
```

## Writing a check

Use the `/add-check <name>` skill to scaffold. A check:

- subclasses `Check` in `checks/validators/<name>_check.py`, class `<Name>Check`, `check_type` = `<name>`;
- implements `execute(field_path, values, check_value) -> List[ValidationResult]`
  (leave `contract_file` as `""`; the validator fills it in);
- is exported in `validators/__init__.py`, added to `_register_default_checks` in `registry.py`,
  tested in `tests/unit/test_checks.py` (passing + failing cases) and documented in `docs/checks.md`.

Null/missing semantics (see the `Check` docstring) apply to every check:

- absent attribute (`values == []`) → return no results; only `required` enforces presence;
- present-but-null → the validator reports it via `null_result()` and strips it before `execute`,
  unless the check sets `handles_nulls = True`;
- `None` inside a list/mapping value → fail with `null_elements_result()`.

## Conventions

- ruff (line length 120, rules F/E/I/ANN/RUF) and mypy with `disallow_untyped_defs`: every function needs
  type hints. Use `# noqa: ANN401` only where `Any` is genuinely required.
- Docstrings use Sphinx style (`:param x:` / `:return:`) in `checks/`; Google style (`Args:` / `Returns:`)
  in `cli.py`. Match the file you are in.
- YAML is loaded with `yaml.safe_load` only.
- Adding a schema version = dropping `schema.json` into `contract_schemas/{spec}/{version}/`; support is
  filesystem-driven, no code change needed.
- Changing a CLI option or the checks-config format is user-facing: update `docs/cli.md` / `docs/config.md`
  and the README.

## Automation

- `pull_request_ai_review.yml` runs via `workflow_run` after the `CI` workflow passes on a PR (so fork PRs
  can be commented on), resolves the PR with `.github/actions/resolve-pr-from-workflow-run`, and has
  Claude Code review the diff with read-only tools. The job checks out the default branch and fetches the PR
  head as git objects only (never into the working tree), because Claude Code would otherwise load the PR's
  own `.claude/` hooks/settings/skills, `.mcp.json` and `CLAUDE.md`. Keep it that way: do not add a checkout
  of the PR head or `allow-unsafe-pr-checkout`. It upserts a single PR comment marked
  `<!-- ai-pr-review-marker -->`; runs are queued per PR branch (`concurrency`, no cancelling) and skip
  posting if the PR head moved during the review. Claude only runs when the PR author and triggering actor are in the
  `ALLOWED_USERS` allowlist in the workflow. Otherwise the comment just says the agent is not available.
  If Claude fails or writes no review (retried once), an earlier real review is kept with a note that it
  is of an earlier commit. Only comments by `github-actions[bot]` count as the review comment.
- `CLAUDE_CODE_OAUTH_TOKEN` is a secret of the `claude-review` environment, restricted to the `main`
  branch. Never move it to a repo-level secret or reference that environment from other workflows.
  `.github/CODEOWNERS` makes `.github/` changes require approval from the token owners.
- `workflow_run` workflows always run from the default branch: changes to the review workflow only take
  effect after merge to `main`.
- The review criteria live in the `review-pr` skill (`.claude/skills/review-pr/SKILL.md`); the workflow just
  invokes `/review-pr <base> <head> <output-file>`. CI uses the skill from the default branch, so skill changes
  only affect reviews after merge. Update the skill when conventions above change. Run
  `/review-pr` locally to review the current branch against `origin/main`. Renaming
  the `CI` workflow breaks the trigger.
