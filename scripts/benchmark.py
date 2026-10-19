"""Benchmark contract-checker on a generated set of data contracts.

Generates N synthetic DCS 1.2.1 contracts (each with several models and
fields) plus a checks config that exercises every check type, then times
the phases the CLI goes through: loading the contracts, running the checks
(with and without lint), and rendering the report.

Usage:
    uv run python scripts/benchmark.py                 # 100 contracts
    uv run python scripts/benchmark.py --contracts 500 --models 10 --fields 30
    uv run python scripts/benchmark.py --profile       # also print a cProfile top 25
"""

import argparse
import contextlib
import cProfile
import io
import pstats
import statistics
import tempfile
import time
from pathlib import Path
from typing import Callable, List

import yaml

from contract_checker.checks.reporting import render_json
from contract_checker.checks.validator import DataContractValidator
from contract_checker.utils.contract_utils import load_contracts

CHECKS_CONFIG = {
    "data_contract_specification": "dcs",
    "data_contract_checks": [
        {"attribute": "info.title", "checks": [{"required": True}, {"pattern": "^Contract"}]},
        {"attribute": "info.version", "checks": [{"required": True}, {"pattern": r"^\d+\.\d+\.\d+$"}]},
        {"attribute": "info.owner", "checks": [{"accepted_values": ["team-a", "team-b", "team-c"]}]},
        {"attribute": "tags", "checks": [{"accepted_values": ["sales", "finance", "pii"]}, {"max_items": 5}]},
        {"attribute": "servers.*.type", "checks": [{"accepted_values": ["s3", "gcs", "bigquery"]}]},
        {"attribute": "models.*.fields", "checks": [{"min_items": 1}, {"exactly_one": {"primaryKey": True}}]},
        {"attribute": "models.*.fields", "checks": [{"at_least_one": {"required": True}}]},
        {"attribute": "models.*.fields.*.name", "checks": [{"pattern": "^[a-z][a-z0-9_]*$"}]},
        {"attribute": "models.*.fields.*.description", "checks": [{"required": True}]},
        {"attribute": "models.*.fields.*.type", "checks": [{"required": True}]},
        {
            "attribute": "models.*.fields.*.type",
            "checks": [{"accepted_values": ["string", "integer", "timestamp", "boolean", "decimal"]}],
        },
    ],
}

FIELD_TYPES = ["string", "integer", "timestamp", "boolean", "decimal"]


def make_contract(index: int, models: int, fields: int) -> dict:
    """Build one synthetic DCS 1.2.1 contract that is valid against the schema."""
    return {
        "dataContractSpecification": "1.2.1",
        "id": f"contract-{index}",
        "info": {
            "title": f"Contract {index}",
            "version": "1.0.0",
            "owner": ["team-a", "team-b", "team-c", "team-x"][index % 4],
            "description": "Synthetic contract generated for benchmarking.",
        },
        "servers": {
            "production": {"type": "bigquery", "project": "proj", "dataset": f"ds_{index}"},
            "staging": {"type": "s3", "location": f"s3://bucket/{index}/"},
        },
        "tags": ["sales", "pii"] if index % 2 else ["finance"],
        "models": {
            f"model_{m}": {
                "type": "table",
                "description": f"Model {m}",
                "fields": {
                    f"field_{f}": {
                        "type": FIELD_TYPES[f % len(FIELD_TYPES)],
                        "description": f"Field {f}" if (index + f) % 7 else None,
                        "required": f % 3 == 0,
                        "primaryKey": f == 0,
                    }
                    for f in range(fields)
                },
            }
            for m in range(models)
        },
    }


def write_contracts(directory: Path, count: int, models: int, fields: int) -> None:
    for index in range(count):
        path = directory / f"domain_{index % 5}" / f"contract_{index}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(make_contract(index, models, fields), sort_keys=False))


def timeit(fn: Callable[[], object], repeat: int) -> List[float]:
    timings = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn()
        timings.append(time.perf_counter() - start)
    return timings


def fmt(timings: List[float]) -> str:
    return f"median {statistics.median(timings) * 1000:8.1f} ms   (min {min(timings) * 1000:8.1f} ms)"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--contracts", type=int, default=100)
    parser.add_argument("--models", type=int, default=5)
    parser.add_argument("--fields", type=int, default=20)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--profile", action="store_true", help="Print a cProfile top 25 of a full lint run.")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        contracts_dir = Path(tmp)
        write_contracts(contracts_dir, args.contracts, args.models, args.fields)

        def load() -> object:
            return load_contracts(contracts_dir, "dcs")

        contracts = load()

        def validate(lint: bool) -> Callable[[], object]:
            return lambda: DataContractValidator(CHECKS_CONFIG, lint=lint).validate(contracts)

        reports = DataContractValidator(CHECKS_CONFIG, lint=True).validate(contracts)
        total_results = sum(r.total_checks for r in reports)

        def report_text(mode: str) -> Callable[[], object]:
            def run() -> None:
                validator = DataContractValidator(CHECKS_CONFIG)
                with contextlib.redirect_stdout(io.StringIO()):
                    validator.reporter.console.file = io.StringIO()
                    validator.print_results(reports, output_mode=mode)

            return run

        print(
            f"{args.contracts} contracts x {args.models} models x {args.fields} fields, "
            f"{len(CHECKS_CONFIG['data_contract_checks'])} check rules -> {total_results} results (lint on)\n"
        )
        phases = {
            "load contracts (YAML parse)": load,
            "run checks, lint off": validate(False),
            "run checks, lint on": validate(True),
            "report: json": lambda: render_json(reports),
            "report: text summary": report_text("summary"),
            "report: text failures": report_text("failures"),
            "report: text full": report_text("full"),
        }
        for name, fn in phases.items():
            print(f"{name:<30} {fmt(timeit(fn, args.repeat))}")

        if args.profile:
            profiler = cProfile.Profile()
            profiler.enable()
            load()
            validate(True)()
            report_text("failures")()
            profiler.disable()
            print()
            pstats.Stats(profiler).sort_stats("cumulative").print_stats(25)


if __name__ == "__main__":
    main()
