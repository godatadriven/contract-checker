"""Core data contract validation logic with integrated reporting."""

from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jsonschema

from contract_checker.contract.contract_base import Contract, get_standard_schema_path
from contract_checker.utils.utils import CustomSchemaError, load_and_validate_json_schema

from .base import Check
from .models import ContractValidationReport, ValidationResult
from .registry import CheckRegistry
from .reporting import ValidationReporter


class ChecksConfigError(ValueError):
    """Raised when the 'data_contract_checks' configuration is malformed."""


def validate_checks_config(checks_dict: Optional[dict], registry: Optional[CheckRegistry] = None) -> None:
    """Validate the ``data_contract_checks`` configuration before any contract is read.

    Each entry must be a mapping with a non-empty string ``attribute`` and a
    ``checks`` list; each check must be a single-key mapping whose key is a
    registered check type and whose value passes that check's
    :meth:`Check.validate_config`. A problem here is a configuration error,
    so it is raised once, naming the entry, rather than being reported
    against every contract file.

    Args:
        checks_dict: Parsed checks configuration (may be None).
        registry: Registry used to resolve check types (the default registry if None).

    Raises:
        ChecksConfigError: Describing the first offending entry.
    """
    registry = registry or CheckRegistry()
    available = registry.list_available()
    rules = (checks_dict or {}).get("data_contract_checks") or []
    if not isinstance(rules, list):
        raise ChecksConfigError("'data_contract_checks' must be a list of attribute/checks entries.")

    for index, rule in enumerate(rules, 1):
        where = f"data_contract_checks entry {index}"
        if not isinstance(rule, dict):
            raise ChecksConfigError(f"{where} must be a mapping with 'attribute' and 'checks' keys.")
        attribute = rule.get("attribute")
        if not isinstance(attribute, str) or not attribute:
            raise ChecksConfigError(f"{where} is missing a non-empty 'attribute'.")
        checks = rule.get("checks")
        if not isinstance(checks, list):
            raise ChecksConfigError(f"{where} ('{attribute}') must have a 'checks' list.")

        for check in checks:
            if not isinstance(check, dict) or len(check) != 1:
                raise ChecksConfigError(
                    f"{where} ('{attribute}'): each check must be a single-key mapping "
                    f"such as '- required: true', got {check!r}."
                )
            check_type, check_value = next(iter(check.items()))
            if check_type not in available:
                raise ChecksConfigError(
                    f"{where} ('{attribute}'): unknown check type '{check_type}'. Available: {', '.join(available)}."
                )
            try:
                registry.get(check_type).validate_config(check_value)
            except ValueError as e:
                raise ChecksConfigError(f"{where} ('{attribute}'): {e}") from e


def _to_json_compatible(value: Any) -> Any:  # noqa: ANN401
    """Convert YAML-parsed values back to JSON types before schema validation.

    ``yaml.safe_load`` turns unquoted dates (``2022-10-03``) into ``date`` and
    ``datetime`` objects, which JSON has no type for, so a ``"type": "string"``
    schema rejects them. Render them as ISO strings (``datetime`` uses the ``T``
    separator that JSON Schema's ``date-time`` format expects).
    """
    if isinstance(value, dict):
        return {key: _to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_json_compatible(item) for item in value]
    if isinstance(value, date):  # also matches datetime, a subclass of date
        return value.isoformat()
    return value


class DataContractValidator:
    """Validates data contract YAML files against defined checks"""

    def __init__(
        self,
        checks_dict: dict,
        check_registry: Optional[CheckRegistry] = None,
        lint: bool = False,
    ) -> None:
        """
        Initialize validator with checks configuration and reporter

        Args:
            checks_dict: Dictionary containing the checks configuration
            check_registry: Optional custom CheckRegistry instance
            lint: Whether to validate the whole contract against its JSON Schema
                (the custom schema when one is supplied, otherwise the vendored
                standard schema). Already resolved by the caller (see
                ``resolve_lint``); the ``lint`` key in ``checks_dict`` is not read here.
        """
        self.checks_config = checks_dict
        self.lint = lint

        self.registry = check_registry or CheckRegistry()
        # Initialize the reporter for output formatting and summary generation
        self.reporter = ValidationReporter()
        # One compiled JSON Schema validator per schema file. All contracts of
        # the same standard/version (or one custom schema) share a schema, and
        # loading + meta-validating it is far more expensive than validating a
        # contract against it, so do that once per schema, not once per contract.
        self._schema_validators: Dict[Path, Any] = {}

    def run_checks(self, data_contract: Contract) -> ContractValidationReport:
        """
        Run checks on a single data contract

        Args:
            data_contract: Contract object representing the data contract

        Returns:
            ContractValidationReport with results
        """
        results = []

        # When linting is enabled, validate the whole contract against its JSON
        # Schema first. This does not replace the attribute-level checks below:
        # the two compose, so schema validation and data_contract_checks run
        # together.
        if self.lint:
            schema_results = self._validate_against_schema(data_contract)
            results.extend(schema_results)

        # Run the attribute-level checks. The list may be empty, omitted, or the
        # whole config may be absent (None) — e.g. schema-only validation driven
        # entirely by --custom-schema-path. All of these mean "no extra checks".
        for attribute in (self.checks_config or {}).get("data_contract_checks") or []:
            attribute_path = attribute["attribute"]
            checks = attribute["checks"]

            if "*" in attribute_path:
                # Wildcard path: expand into concrete paths and run
                # checks individually per matched item
                expanded = self._expand_wildcard_paths(data_contract.contract_content, attribute_path)
                for concrete_path, values in expanded.items():
                    for check_config in checks:
                        check_type = next(iter(check_config.keys()))
                        check_value = check_config[check_type]
                        check_handler = self.registry.get(check_type)
                        check_results = self._run_check(check_handler, concrete_path, values, check_value)
                        for result in check_results:
                            result.contract_file = data_contract.contract_path
                        results.extend(check_results)
            else:
                # Non-wildcard path: original behavior
                values = self._get_attribute_values(data_contract.contract_content, attribute_path)

                for check_config in checks:
                    check_type = next(iter(check_config.keys()))
                    check_value = check_config[check_type]
                    check_handler = self.registry.get(check_type)
                    check_results = self._run_check(check_handler, attribute_path, values, check_value)
                    for result in check_results:
                        result.contract_file = data_contract.contract_path
                    results.extend(check_results)

        # Create report
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        return ContractValidationReport(
            contract_file=data_contract.contract_path,
            total_checks=len(results),
            passed_checks=passed,
            failed_checks=failed,
            results=results,
        )

    def _run_check(
        self,
        check_handler: Check,
        attribute_path: str,
        values: List[Any],
        check_value: Any,  # noqa: ANN401
    ) -> List[ValidationResult]:
        """
        Run one check, reporting top-level nulls before the check sees them

        Every ``None`` in ``values`` gets the standard null failure, and only
        the non-null values reach ``execute()``. This keeps custom checks from
        receiving ``None``. An absent attribute (``values == []``) still
        reaches ``execute()`` so ``required`` can report it as missing. Checks
        with ``handles_nulls = True`` receive ``values`` unchanged.

        Args:
            check_handler: The check to run
            attribute_path: Concrete attribute path being checked
            values: Values found at the path ([] if absent, None if null)
            check_value: Configuration value for the check

        Returns:
            List of ValidationResult objects
        """
        if check_handler.handles_nulls:
            return check_handler.execute(attribute_path, values, check_value)

        non_null = [v for v in values if v is not None]
        results = [check_handler.null_result(attribute_path) for v in values if v is None]
        if non_null or not values:
            results.extend(check_handler.execute(attribute_path, non_null, check_value))
        return results

    def _resolve_schema_path(self, data_contract: Contract) -> Path:
        """Return the JSON Schema path to validate a contract against.

        A custom schema, when supplied, takes precedence; otherwise the vendored
        standard schema for the contract's specification and version is used.
        """
        if data_contract.custom_schema_path:
            return Path(data_contract.custom_schema_path)
        return Path(
            get_standard_schema_path(
                data_contract.contract_specification,
                data_contract.contract_specification_version,
            )
        )

    def _get_schema_validator(self, schema_path: Path) -> Any:  # noqa: ANN401
        """Return the compiled JSON Schema validator for a schema file, cached per path.

        The first call for a path loads the schema, checks it against its
        meta-schema, and builds the validator; later calls reuse it. A broken
        schema is not cached, so it raises again for every contract and each one
        reports the failure.

        Args:
            schema_path: Path to the JSON Schema file

        Returns:
            A jsonschema validator instance for the schema

        Raises:
            CustomSchemaError: If the schema is missing, not valid JSON, or not a valid JSON Schema.
        """
        if schema_path not in self._schema_validators:
            schema = load_and_validate_json_schema(schema_path)
            validator_class = jsonschema.validators.validator_for(schema)
            self._schema_validators[schema_path] = validator_class(schema)
        return self._schema_validators[schema_path]

    def _validate_against_schema(self, data_contract: Contract) -> List[ValidationResult]:
        """
        Validate a contract against its JSON Schema.

        Uses the custom schema when one is attached to the contract, otherwise
        the vendored standard schema for the contract's specification/version.

        Args:
            data_contract: Contract object to validate

        Returns:
            List of ValidationResult objects
        """
        results = []

        # Load and meta-validate the schema here too (not just at the CLI layer),
        # so the "schema is itself a valid JSON Schema" guarantee holds even when
        # the validator is driven directly. A bad schema surfaces as a single,
        # clear failure instead of a generic runtime error.
        try:
            schema_path = self._resolve_schema_path(data_contract)
            validator = self._get_schema_validator(schema_path)
        except CustomSchemaError as e:
            results.append(
                ValidationResult(
                    contract_file=data_contract.contract_path,
                    attribute="schema",
                    check_type="json_schema",
                    passed=False,
                    message=str(e),
                )
            )
            return results

        try:
            errors = list(validator.iter_errors(_to_json_compatible(data_contract.contract_content)))

            if not errors:
                # No validation errors - success
                results.append(
                    ValidationResult(
                        contract_file=data_contract.contract_path,
                        attribute="schema",
                        check_type="json_schema",
                        passed=True,
                        message=f"Contract validates against JSON Schema ({schema_path})",
                    )
                )
            else:
                # Create a ValidationResult for each error
                for error in errors:
                    # Build a readable attribute path
                    if error.absolute_path:
                        attribute_path = ".".join(str(p) for p in error.absolute_path)
                    else:
                        attribute_path = "root"

                    results.append(
                        ValidationResult(
                            contract_file=data_contract.contract_path,
                            attribute=attribute_path,
                            check_type="json_schema",
                            passed=False,
                            message=f"Schema validation failed: {error.message}",
                        )
                    )
        except Exception as e:
            results.append(
                ValidationResult(
                    contract_file=data_contract.contract_path,
                    attribute="schema",
                    check_type="json_schema",
                    passed=False,
                    message=f"Schema validation error: {e}",
                )
            )

        return results

    def validate(self, data_contracts: List[Contract]) -> List[ContractValidationReport]:
        """
        Validate multiple data contract YAML files

        Args:
            data_contracts: List of Contract objects

        Returns:
            List of ContractValidationReport objects

        Raises:
            ChecksConfigError: If the checks configuration is malformed.
        """
        validate_checks_config(self.checks_config, self.registry)
        reports = []

        for contract in data_contracts:
            try:
                report = self.run_checks(contract)
                reports.append(report)
            except Exception as e:
                # Create a failed report for files that can't be processed
                error_result = ValidationResult(
                    contract_file=contract.contract_path,
                    attribute="file",
                    check_type="validation",
                    passed=False,
                    message=f"Error processing file: {e!s}",
                )
                reports.append(
                    ContractValidationReport(
                        contract_file=contract.contract_path,
                        total_checks=1,
                        passed_checks=0,
                        failed_checks=1,
                        results=[error_result],
                    )
                )

        return reports

    def print_results(
        self,
        reports: Union[ContractValidationReport, List[ContractValidationReport]],
        output_mode: str = "failures",
    ) -> None:
        """
        Print validation results in a readable format

        Delegates to the ValidationReporter for consistent formatting.
        See ValidationReporter.print_results for the available output modes.
        """
        self.reporter.print_results(reports, output_mode)

    def get_summary(self, reports: List[ContractValidationReport]) -> Dict[str, Any]:
        """
        Get a summary dictionary of validation results

        Delegates to the ValidationReporter for consistent formatting.
        """
        return self.reporter.get_summary(reports)

    def _get_attribute_values(self, data: Dict, attribute_path: str) -> List[Any]:
        """
        Extract values from nested data structure based on attribute path

        Args:
            data: The data dictionary
            attribute_path: Dot-separated attribute path (e.g., 'models.fields.unique')
        Returns:
            List of values found at the attribute path
        """
        parts = attribute_path.split(".")
        return self._traverse_path(data, parts, [])

    def _expand_wildcard_paths(self, data: Dict, attribute_path: str) -> Dict[str, List[Any]]:
        """
        For paths containing wildcards, expand into concrete paths and collect
        values for each. This allows checks to run per-item rather than across
        all matched items combined.

        A ``*`` segment matches each repeated item regardless of how the
        repetition is represented in the contract standard:

        - dict keyed by name (DCS style): ``*`` expands over the dict entries,
          e.g. ``models.*.fields.*.unique``
        - list of objects (ODCS style): ``*`` expands over the list items,
          e.g. ``schema.*.properties.*.logicalType``

        List items are labeled by their ``name``, falling back to their index.
        Items whose label is not unique (duplicate names) are labeled
        ``label[index]`` so each one is checked separately.

        A trailing ``name`` segment after a dict ``*`` resolves to the dict key
        itself when the entry is a dict without an explicit ``name`` value, so
        ``models.*.fields.*.name`` yields field names for both standards. Null
        or scalar entries are not named objects and resolve to missing.

        Args:
            data: The data dictionary
            attribute_path: Dot-separated path with wildcards (e.g., 'models.*.fields.*.unique')

        Returns:
            Dict mapping each concrete expanded path to its list of values.
            Paths where the leaf attribute is missing will map to an empty list.
        """
        parts = attribute_path.split(".")
        return self._expand_and_collect(data, parts, [])

    def _expand_and_collect(
        self,
        data: Any,  # noqa: ANN401
        parts: List[str],
        current_path: List[str],
    ) -> Dict[str, List[Any]]:
        """
        Recursively expand wildcards and collect values per concrete path.

        Args:
            data: Current data node
            parts: Remaining parts of the field path
            current_path: Concrete path segments accumulated so far

        Returns:
            Dict mapping concrete path strings to their values
        """
        if not parts:
            path_str = ".".join(current_path)
            return {path_str: [data]}

        current_part = parts[0]
        remaining = parts[1:]

        if data is None:
            path_str = ".".join(current_path + parts)
            return {path_str: []}

        if isinstance(data, dict):
            if current_part == "*":
                # Wildcard: expand into each entry of the dict (DCS-style
                # repeatable objects are dicts keyed by name).
                results_wildcard: Dict[str, List[Any]] = {}
                for key, value in data.items():
                    if remaining == ["name"] and isinstance(value, dict) and "name" not in value:
                        # Key-as-name: in dict-style contracts the entry name
                        # is the key itself (e.g. DCS `fields:`). An explicit
                        # `name` value inside the entry wins over the key, and
                        # null or scalar entries are not named objects.
                        results_wildcard[".".join([*current_path, key, "name"])] = [key]
                    else:
                        sub = self._expand_and_collect(value, remaining, [*current_path, key])
                        results_wildcard.update(sub)
                return results_wildcard
            elif current_part in data:
                return self._expand_and_collect(data[current_part], remaining, [*current_path, current_part])
            else:
                path_str = ".".join(current_path + parts)
                return {path_str: []}

        elif isinstance(data, list):
            results: Dict[str, List[Any]] = {}
            if current_part == "*":
                # Wildcard: expand into each item of the list (ODCS-style
                # repeatable objects are lists of named objects). Each item
                # gets a unique label so items are never merged.
                for label, item in zip(self._list_item_labels(data), data):
                    sub = self._expand_and_collect(item, remaining, [*current_path, label])
                    for k, v in sub.items():
                        results.setdefault(k, []).extend(v)
            else:
                # Non-wildcard segment: lists are transparent, the segment
                # applies to each item (e.g. `servers.type`).
                for item in data:
                    sub = self._expand_and_collect(item, parts, current_path)
                    for k, v in sub.items():
                        results.setdefault(k, []).extend(v)
            return results

        path_str = ".".join(current_path + parts)
        return {path_str: []}

    @staticmethod
    def _list_item_labels(items: List[Any]) -> List[str]:
        """
        Build a unique path label for each item of a list.

        An item is labeled with its ``name`` when it is a non-empty string,
        falling back to its index. When a label occurs more than once
        (duplicate names, or a name equal to another item's index), each of
        those items is labeled ``label[index]`` instead, so they are checked
        separately rather than merged under one path.

        Args:
            items: The list being expanded by a ``*`` segment

        Returns:
            One label per item, in list order
        """
        labels = []
        for index, item in enumerate(items):
            name = item.get("name") if isinstance(item, dict) else None
            labels.append(name if isinstance(name, str) and name else str(index))
        counts = Counter(labels)
        return [f"{label}[{index}]" if counts[label] > 1 else label for index, label in enumerate(labels)]

    def _traverse_path(
        self,
        data: Any,  # noqa: ANN401
        parts: List[str],
        current_path: List[str],
    ) -> List[Any]:
        """
        Recursively traverse the data structure following the field path

        Args:
            data: Current data node
            parts: Remaining parts of the field path
            current_path: Current traversed path for context

        Returns:
            List of values found
        """
        if not parts:
            return [data]

        current_part = parts[0]
        remaining_parts = parts[1:]

        if data is None:
            return []

        # Handle dictionary
        if isinstance(data, dict):
            if current_part in data:
                return self._traverse_path(data[current_part], remaining_parts, [*current_path, current_part])
            else:
                return []

        # Handle list - traverse all items
        elif isinstance(data, list):
            results = []
            for item in data:
                results.extend(self._traverse_path(item, parts, current_path))
            return results

        return []
