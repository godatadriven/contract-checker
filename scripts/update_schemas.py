#!/usr/bin/env python3
"""Vendor new ODCS and DCS schema versions from their upstream repositories.

Support for a contract version in this project is filesystem-driven: a version is
supported iff ``src/contract_checker/contract_schemas/{spec}/{version}/schema.json``
exists (see ``contract_checker.contract.contract_base.Contract.validate_version``).
This script discovers versions published upstream, vendors any that are missing,
refreshes the version ranges quoted in the docs, and scaffolds a starter test
fixture for each newly added version.

It is dependency-free (standard library only) so it can run in CI without adding a
runtime dependency. Set ``GITHUB_TOKEN`` in the environment to raise the GitHub API
rate limit (the CI workflow passes ``github.token``).

Run from anywhere:

    uv run python scripts/update_schemas.py

Exit code is always 0 on a successful run (including "nothing to do"); individual
download failures are logged and skipped rather than aborting the whole run.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "src" / "contract_checker" / "contract_schemas"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "index.md"

# A strict X.Y.Z version (pre-releases / previews are intentionally ignored).
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

ODCS_CONTENTS_API = "https://api.github.com/repos/bitol-io/open-data-contract-standard/contents/schema?ref=main"
ODCS_FILE_RE = re.compile(r"^odcs-json-schema-v(\d+\.\d+\.\d+)\.json$")

# DCS publishes every release as its own directory under versions/, each containing a
# datacontract.schema.json. Versions are discovered by listing that directory.
DCS_VERSIONS_API = "https://api.github.com/repos/datacontract/datacontract-specification/contents/versions?ref=main"
DCS_SCHEMA_RAW = (
    "https://raw.githubusercontent.com/datacontract/datacontract-specification/"
    "main/versions/{version}/datacontract.schema.json"
)


def log(message: str) -> None:
    """Write a progress line to stderr (stdout is reserved for the summary)."""
    print(message, file=sys.stderr)


def version_key(version: str) -> tuple[int, ...]:
    """Sort key for an ``X.Y.Z`` version string."""
    return tuple(int(part) for part in version.split("."))


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _request(url: str) -> bytes:
    """GET ``url`` with a User-Agent and optional GitHub auth header."""
    headers = {"User-Agent": "contract-checker-schema-updater"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return bytes(resp.read())


def fetch_json(url: str) -> object:
    return json.loads(_request(url).decode("utf-8"))


def fetch_schema(url: str) -> dict:
    """Download a schema and confirm it parses as a JSON object."""
    data = json.loads(_request(url).decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"schema at {url} is not a JSON object")
    return data


# ---------------------------------------------------------------------------
# Upstream discovery
# ---------------------------------------------------------------------------


def discover_odcs() -> dict[str, str]:
    """Return ``{version: download_url}`` for ODCS schemas published upstream."""
    entries = fetch_json(ODCS_CONTENTS_API)
    if not isinstance(entries, list):
        raise ValueError("unexpected ODCS contents API response")
    versions: dict[str, str] = {}
    for entry in entries:
        match = ODCS_FILE_RE.match(entry["name"])
        if match:
            versions[match.group(1)] = entry["download_url"]
    return versions


def discover_dcs() -> dict[str, str]:
    """Return ``{version: download_url}`` for DCS schemas published upstream.

    Each version has its own directory under ``versions/`` containing a
    ``datacontract.schema.json``.
    """
    entries = fetch_json(DCS_VERSIONS_API)
    if not isinstance(entries, list):
        raise ValueError("unexpected DCS versions API response")
    versions: dict[str, str] = {}
    for entry in entries:
        name = entry["name"]
        if entry.get("type") == "dir" and SEMVER_RE.match(name):
            versions[name] = DCS_SCHEMA_RAW.format(version=name)
    return versions


# ---------------------------------------------------------------------------
# Local state
# ---------------------------------------------------------------------------


def vendored_versions(spec: str) -> set[str]:
    spec_dir = SCHEMAS_DIR / spec
    if not spec_dir.is_dir():
        return set()
    return {child.name for child in spec_dir.iterdir() if child.is_dir() and (child / "schema.json").exists()}


def write_schema(spec: str, version: str, schema: dict) -> None:
    dest = SCHEMAS_DIR / spec / version / "schema.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Docs + fixtures
# ---------------------------------------------------------------------------


def _replace_range(line: str, mn: str, mx: str) -> str:
    """Rewrite the ``X.Y.Z <sep> X.Y.Z`` range on a line, preserving the separator."""
    # Matches an en dash (U+2013, used in README), a plain hyphen, or the word "through".
    pattern = re.compile(r"\d+\.\d+\.\d+(\s*(?:\u2013|-|through)\s*)\d+\.\d+\.\d+")
    return pattern.sub(lambda m: f"{mn}{m.group(1)}{mx}", line)


def update_docs(ranges: dict[str, tuple[str, str]]) -> list[Path]:
    """Update the version ranges quoted in README.md and docs/index.md.

    ``ranges`` maps spec -> (min, max). README rows are matched by ``[DCS`` / ``[ODCS``;
    docs/index bullets by ``**DCS`` / ``**ODCS``.
    """
    changed: list[Path] = []
    targets = [
        (README, {"dcs": "[DCS", "odcs": "[ODCS"}),
        (DOCS_INDEX, {"dcs": "**DCS", "odcs": "**ODCS"}),
    ]
    for path, markers in targets:
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        new_lines = []
        for line in lines:
            for spec, marker in markers.items():
                if marker in line and spec in ranges:
                    mn, mx = ranges[spec]
                    line = _replace_range(line, mn, mx)
            new_lines.append(line)
        new_text = "".join(new_lines)
        if new_text != path.read_text(encoding="utf-8"):
            path.write_text(new_text, encoding="utf-8")
            changed.append(path)
    return changed


def scaffold_fixture(spec: str, version: str) -> Path | None:
    """Create a starter fixture for ``version`` by copying the newest existing one.

    Best-effort: the version field is bumped, but a new spec release may add required
    fields the copied fixture does not satisfy, so the result must be reviewed.
    """
    spec_fix_dir = FIXTURES_DIR / spec
    if not spec_fix_dir.is_dir():
        return None
    source_versions = sorted(
        (d for d in spec_fix_dir.iterdir() if d.is_dir() and SEMVER_RE.match(d.name)),
        key=lambda d: version_key(d.name),
    )
    if not source_versions:
        return None
    source_dir = source_versions[-1]
    source_files = sorted(source_dir.glob("*.yaml"))
    if not source_files:
        return None
    source_file = source_files[0]

    text = source_file.read_text(encoding="utf-8")
    if spec == "dcs":
        text = re.sub(
            r"^dataContractSpecification:.*$",
            f"dataContractSpecification: {version}",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    elif spec == "odcs":
        text = re.sub(
            r"^apiVersion:.*$",
            f"apiVersion: v{version}",
            text,
            count=1,
            flags=re.MULTILINE,
        )

    dest_dir = spec_fix_dir / version
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / source_file.name
    dest.write_text(text, encoding="utf-8")
    return dest


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def validate_fixture(spec: str, version: str, fixture: Path) -> bool | None:
    """Validate a scaffolded fixture against the freshly vendored schema.

    Returns True/False, or None if the validation tooling (jsonschema/PyYAML, both
    project dependencies) is unavailable so the script still works standalone.
    """
    try:
        import jsonschema
        import yaml
    except ImportError:
        return None
    schema = json.loads((SCHEMAS_DIR / spec / version / "schema.json").read_text(encoding="utf-8"))
    data = yaml.safe_load(fixture.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError:
        return False
    return True


def process_spec(
    spec: str,
    discover: Callable[[], dict[str, str]],
    needs_review: list[str],
) -> list[str]:
    """Vendor missing versions for ``spec`` and scaffold fixtures.

    Returns the list of added versions; appends "spec version (file): reason" entries to
    ``needs_review`` for scaffolded fixtures that fail validation against the new schema.
    """
    log(f"[{spec}] discovering upstream versions...")
    upstream = discover()
    have = vendored_versions(spec)
    missing = sorted((set(upstream) - have), key=version_key)
    log(f"[{spec}] upstream={sorted(upstream, key=version_key)} vendored={sorted(have, key=version_key)}")

    added: list[str] = []
    for version in missing:
        url = upstream[version]
        try:
            schema = fetch_schema(url)
        except (urllib.error.URLError, ValueError, KeyError) as exc:
            log(f"[{spec}] WARN: could not fetch {version} from {url}: {exc}")
            continue
        write_schema(spec, version, schema)
        added.append(version)
        fixture = scaffold_fixture(spec, version)
        if fixture is None:
            log(f"[{spec}] added {version}")
            continue
        valid = validate_fixture(spec, version, fixture)
        status = {True: "valid", False: "NEEDS REVIEW", None: "unvalidated"}[valid]
        log(f"[{spec}] added {version} (+fixture {fixture.name}: {status})")
        if valid is False:
            needs_review.append(f"`{spec}/{version}/{fixture.name}` does not validate against the new schema")
    return added


def emit_summary(
    added: dict[str, list[str]],
    docs_changed: list[Path],
    needs_review: list[str],
) -> None:
    """Print a human summary to stdout and append it to $GITHUB_STEP_SUMMARY."""
    total = sum(len(v) for v in added.values())
    lines = ["## Schema update summary", ""]
    if total == 0:
        lines.append("No new schema versions found. Everything is up to date.")
    else:
        for spec, versions in added.items():
            if versions:
                lines.append(f"- **{spec.upper()}**: added {', '.join(versions)}")
        if docs_changed:
            lines.append("")
            lines.append("Updated docs: " + ", ".join(p.name for p in docs_changed))
        if needs_review:
            lines.append("")
            lines.append("### Fixtures needing manual review")
            lines.extend(f"- {item}" for item in needs_review)
        lines.append("")
        lines.append(
            "> Scaffolded fixtures are starter copies of the previous version with the "
            "version field bumped — review them, and consider dedicated checks for the new versions."
        )
    summary = "\n".join(lines) + "\n"
    print(summary)
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write(summary)


def main() -> int:
    needs_review: list[str] = []
    added = {
        "odcs": process_spec("odcs", discover_odcs, needs_review),
        "dcs": process_spec("dcs", discover_dcs, needs_review),
    }

    ranges: dict[str, tuple[str, str]] = {}
    for spec in ("dcs", "odcs"):
        versions = vendored_versions(spec)
        if versions:
            ordered = sorted(versions, key=version_key)
            ranges[spec] = (ordered[0], ordered[-1])

    docs_changed = update_docs(ranges) if any(added.values()) else []
    emit_summary(added, docs_changed, needs_review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
