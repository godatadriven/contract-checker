import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from contract_checker.checks.models import ContractValidationReport, ValidationResult
from contract_checker.contract.contract_base import Contract
from contract_checker.utils.path_filter import filter_contract_paths
from contract_checker.utils.utils import YamlMappingError, is_dir_or_yaml, load_yaml_mapping

# Specifications with vendored schemas under contract_schemas/, and the
# contract key that carries the specification version for each.
SUPPORTED_SPECIFICATIONS = ("dcs", "odcs")
SPECIFICATION_VERSION_KEYS = {"dcs": "dataContractSpecification", "odcs": "apiVersion"}


@dataclass
class LoadedContracts:
    """Outcome of :func:`load_contracts`.

    ``contracts`` are ready to validate. ``failed_reports`` are files that
    could not be loaded (not valid YAML, missing version key, unsupported
    version); each is a failed report so it is printed, counted and
    reflected in the exit code like any other failing contract.
    """

    contracts: list[Contract] = field(default_factory=list)
    failed_reports: list[ContractValidationReport] = field(default_factory=list)


def parse_data_contracts_path_config(
    checks_dict: dict,
) -> tuple[Optional[Path], list[str], list[str]]:
    """Parse the optional 'data_contracts_path' block from the checks config.

    Accepts either a plain string path:

        data_contracts_path: ./contracts/

    or a mapping with optional glob filters:

        data_contracts_path:
          path: ./contracts/
          include_paths:
            - domain/**
          exclude_paths:
            - marts/**

    Args:
        checks_dict: Parsed checks configuration.

    Returns:
        Tuple of (path or None, include_paths, exclude_paths).

    Raises:
        ValueError: If 'data_contracts_path' is neither a string nor a mapping.
    """
    raw = (checks_dict or {}).get("data_contracts_path")
    if raw is None:
        return None, [], []
    if isinstance(raw, str):
        return Path(raw), [], []
    if not isinstance(raw, dict):
        raise ValueError("'data_contracts_path' must be a string or a mapping.")

    for ignored_key in ("include_custom", "exclude_custom"):
        if ignored_key in raw:
            logging.debug(f"'{ignored_key}' in data_contracts_path is not yet supported and will be ignored.")

    path = Path(raw["path"]) if raw.get("path") else None
    return path, raw.get("include_paths") or [], raw.get("exclude_paths") or []


def get_specification_version(contract_content: dict, contract_standard: str) -> str:
    """Get the version of the provided contract based on its standard."""
    if contract_standard == "custom":
        return "custom"

    version_key = SPECIFICATION_VERSION_KEYS.get(contract_standard)
    if version_key is None:
        raise ValueError(
            f"Unsupported data_contract_specification '{contract_standard}'. "
            f"Use one of: {', '.join(SUPPORTED_SPECIFICATIONS)}, or 'custom' with a custom schema."
        )
    if version_key not in contract_content:
        raise ValueError(
            f"Contract is missing the '{version_key}' key, cannot determine its {contract_standard} version."
        )

    # ODCS contracts carry the version as `apiVersion: vX.Y.Z`, but the
    # vendored schema folders are bare semver (e.g. odcs/3.0.2). Strip the
    # leading `v` so the version resolves to a supported schema directory.
    return str(contract_content[version_key]).removeprefix("v")


def parse_specification_from_contract(contract_content: dict, checks_dict: dict) -> tuple[str, str]:
    """Check if the contract matches the expected version."""
    if not contract_content:
        raise ValueError("Contract content is not loaded.")

    if "data_contract_standard" in checks_dict:
        contract_specification = checks_dict["data_contract_standard"]
    else:
        raise ValueError("data_contract_standard not configured.")

    # Maybe we can simplify this with a mapping dict in utils later?
    if contract_specification == "dcs":
        version = contract_content["dataContractSpecification"]
    elif contract_specification == "odcs":
        # Normalise `vX.Y.Z` to bare semver to match the schema folder names.
        version = str(contract_content["apiVersion"]).removeprefix("v")
        return version, contract_specification
    else:
        raise ValueError("Specification field not found in data contract.")

    return version, contract_specification


def _load_failure_report(contract_path: Path, message: str) -> ContractValidationReport:
    """Build the failed report for a contract file that could not be loaded."""
    result = ValidationResult(
        contract_file=str(contract_path),
        attribute="file",
        check_type="load",
        passed=False,
        message=message,
    )
    return ContractValidationReport(
        contract_file=str(contract_path),
        total_checks=1,
        passed_checks=0,
        failed_checks=1,
        results=[result],
    )


def _validation_error_message(error: ValidationError) -> str:
    """Reduce a pydantic ValidationError to the message(s) our model validator raised."""
    return "; ".join(str(err["msg"]).removeprefix("Value error, ") for err in error.errors())


def _load_contract(contract_path: Path, specification: str, custom_schema_path: Optional[Path]) -> Contract:
    """Parse one contract file and wrap it in a :class:`Contract`."""
    contract_content = load_yaml_mapping(contract_path)
    version = get_specification_version(contract_content, specification)
    return Contract(
        contract_path=contract_path,
        contract_content=contract_content,
        contract_specification=specification,
        contract_specification_version=version,
        custom_schema_path=custom_schema_path,
    )


def load_contracts(
    contract_path: Path,
    contract_specification: Optional[str],
    custom_schema_path: Optional[Path] = None,
    include_paths: Optional[list[str]] = None,
    exclude_paths: Optional[list[str]] = None,
) -> LoadedContracts:
    """Load all data contracts within a user-provided path.

    Configuration problems (unknown specification, missing path) raise,
    since nothing can be validated. Problems with an individual file do not
    abort the run: the file is returned as a failed report in
    ``LoadedContracts.failed_reports`` and loading continues.

    Args:
        contract_path: A contract file, or a directory searched recursively
            for ``*.yaml`` / ``*.yml`` files.
        contract_specification: ``"dcs"`` or ``"odcs"``. Ignored when
            ``custom_schema_path`` is given (the contracts are then ``"custom"``).
        custom_schema_path: Optional JSON Schema to validate contracts against.
        include_paths: Glob patterns to include (directories only).
        exclude_paths: Glob patterns to exclude (directories only).

    Returns:
        The loadable contracts and a failed report per unloadable file.
        Note: this used to return a plain ``list[Contract]``; callers of the
        Python API should now read ``.contracts`` (and ``.failed_reports``).

    Raises:
        ValueError: If the specification is missing, unknown, or ``"custom"``
            without a custom schema.
        FileNotFoundError: If ``contract_path`` does not exist.
    """
    if custom_schema_path is not None:
        specification = "custom"
    elif contract_specification == "custom":
        # A 'custom' specification is meaningless without a schema to validate against.
        raise ValueError(
            "data_contract_specification is 'custom' but no custom schema was provided. "
            "Set 'custom_schema_path' in the checks config file or pass --custom-schema-path."
        )
    elif contract_specification is None or contract_specification not in SUPPORTED_SPECIFICATIONS:
        raise ValueError(
            f"data_contract_specification must be one of: {', '.join(SUPPORTED_SPECIFICATIONS)} "
            f"(got {contract_specification!r}). Set it in the checks config file, or pass --custom-schema-path."
        )
    else:
        specification = contract_specification

    # Check if the contract_path exists before proceeding
    if not contract_path.exists():
        raise FileNotFoundError(f"Provided contract path does not exist: {contract_path}")

    path_type = is_dir_or_yaml(contract_path)
    if path_type == "yaml_file":
        contract_paths = [contract_path]
    else:
        contract_paths = sorted([*contract_path.rglob("*.yaml"), *contract_path.rglob("*.yml")])
        discovered_count = len(contract_paths)
        contract_paths = filter_contract_paths(contract_paths, contract_path, include_paths or [], exclude_paths or [])
        logging.debug(
            f"Discovered {discovered_count} contract file(s), {len(contract_paths)} remaining after filtering."
        )
        if discovered_count > 0 and not contract_paths:
            logging.warning(
                "include_paths/exclude_paths filtered out ALL discovered contracts, nothing will be validated. "
                "Check your patterns in 'data_contracts_path'."
            )

    loaded = LoadedContracts()
    for path in contract_paths:
        try:
            loaded.contracts.append(_load_contract(path, specification, custom_schema_path))
        except ValidationError as e:
            # Raised by Contract.validate_version for an unsupported version.
            # pydantic wraps our ValueError; keep only the message we wrote.
            loaded.failed_reports.append(_load_failure_report(path, _validation_error_message(e)))
        except (YamlMappingError, ValueError) as e:
            # Not valid YAML, not a mapping, or missing the version key.
            loaded.failed_reports.append(_load_failure_report(path, str(e)))

    return loaded
