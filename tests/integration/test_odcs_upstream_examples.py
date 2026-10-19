"""Lint every ODCS fixture against the vendored schema of its version.

``tests/fixtures/odcs/<version>/`` is a snapshot of upstream's ``docs/examples/`` at
tag ``v<version>`` (see ``scripts/update_schemas.py``). Upstream CI validates those
examples against that version's schema, so a failure here means contract-checker
disagrees with upstream, not that the fixture is wrong.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from contract_checker.checks.validator import DataContractValidator
from contract_checker.utils.contract_utils import load_contracts

ODCS_FIXTURES = Path(__file__).parent.parent / "fixtures" / "odcs"
ODCS_SCHEMAS = Path(__file__).parent.parent.parent / "src" / "contract_checker" / "contract_schemas" / "odcs"
# Matches ODCS_EXAMPLES_MIN_VERSION in scripts/update_schemas.py: 2.x has no snapshots.
MIN_SNAPSHOT_VERSION = (3, 0, 0)

FIXTURES = sorted([*ODCS_FIXTURES.rglob("*.yaml"), *ODCS_FIXTURES.rglob("*.yml")])


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: str(p.relative_to(ODCS_FIXTURES)))
def test_odcs_fixture_passes_schema_of_its_version(fixture: Path) -> None:
    """Each fixture declares its folder's version and passes lint against that schema."""
    version = fixture.relative_to(ODCS_FIXTURES).parts[0]

    contracts = load_contracts(fixture, contract_specification="odcs")
    assert [c.contract_specification_version for c in contracts] == [version]

    report = DataContractValidator({"data_contract_checks": []}, lint=True).run_checks(contracts[0])
    assert report.failed_checks == 0, [r.message for r in report.results if not r.passed]


def test_every_vendored_odcs_version_has_fixtures() -> None:
    """A vendored ODCS 3.x schema without fixtures means its examples were never snapshotted."""
    vendored = {d.name for d in ODCS_SCHEMAS.iterdir() if (d / "schema.json").exists()}
    expected = {v for v in vendored if _version_key(v) >= MIN_SNAPSHOT_VERSION}
    with_fixtures = {d.name for d in ODCS_FIXTURES.iterdir() if d.is_dir() and any(d.rglob("*.y*ml"))}

    assert expected <= with_fixtures, f"missing fixtures for: {sorted(expected - with_fixtures)}"
