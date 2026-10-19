"""Lint every ODCS fixture against the vendored schema of its version.

Fixtures live in ``tests/fixtures/odcs/<version>/``; each must declare that version
and pass schema validation, so a fixture that is invalid for its version (e.g. a
copy of an older version with only ``apiVersion`` bumped) fails here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from contract_checker.checks.validator import DataContractValidator
from contract_checker.utils.contract_utils import load_contracts

ODCS_FIXTURES = Path(__file__).parent.parent / "fixtures" / "odcs"
FIXTURES = sorted([*ODCS_FIXTURES.rglob("*.yaml"), *ODCS_FIXTURES.rglob("*.yml")])


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: str(p.relative_to(ODCS_FIXTURES)))
def test_odcs_fixture_passes_schema_of_its_version(fixture: Path) -> None:
    """Each fixture declares its folder's version and passes lint against that schema."""
    version = fixture.relative_to(ODCS_FIXTURES).parts[0]

    loaded = load_contracts(fixture, contract_specification="odcs")
    assert loaded.failed_reports == []
    contracts = loaded.contracts
    assert [c.contract_specification_version for c in contracts] == [version]

    report = DataContractValidator({"data_contract_checks": []}, lint=True).run_checks(contracts[0])
    assert report.failed_checks == 0, [r.message for r in report.results if not r.passed]
