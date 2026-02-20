"""Core data contract validation logic."""

import json
from typing import Any, Dict, List, Optional

import jsonschema
import yaml

from contract_checker.contract.contract_base import Contract

from .models import ContractValidationReport, ValidationResult
from .registry import CheckRegistry


class DataContractValidator:
    """Validates data contract YAML files against defined checks"""

    def __init__(self, checks_file: str, check_registry: Optional[CheckRegistry] = None) -> None:
        """
        Initialize validator with checks configuration

        Args:
            checks_file: Path to the checks YAML file
            check_registry: Optional custom CheckRegistry instance
        """
        with open(checks_file, "r") as f:
            self.checks_config = yaml.safe_load(f)

        self.registry = check_registry or CheckRegistry()

    def run_checks(self, data_contract: Contract) -> ContractValidationReport:
        """
        Run checks on a single data contract

        Args:
            data_contract: Contract object representing the data contract

        Returns:
            ContractValidationReport with results
        """
        results = []

        # If using custom schema, validate against JSON Schema
        if data_contract.custom_schema_path:
            # first do json validation
            schema_results = self._validate_against_custom_schema(data_contract)
            results.extend(schema_results)
        else:
            # Run standard checks only if not using custom schema
            for check_group in self.checks_config["data_contract_checks"]:
                attribute_path = check_group["attribute"]
                checks = check_group["checks"]

                # Get the value(s) at the specified attribute path
                values = self._get_attribute_values(data_contract.contract_content, attribute_path)

                # Run all checks for this attribute
                for check_config in checks:
                    check_type = next(iter(check_config.keys()))
                    check_value = check_config[check_type]

                    # Get the appropriate check handler from registry
                    check_handler = self.registry.get(check_type)

                    # Execute the check
                    check_results = check_handler.execute(attribute_path, values, check_value)

                    # Add contract file to each result
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

    def _validate_against_custom_schema(self, data_contract: Contract) -> List[ValidationResult]:
        """
        Validate contract against custom JSON Schema

        Args:
            data_contract: Contract object to validate

        Returns:
            List of ValidationResult objects
        """
        results = []

        try:
            # Load the custom schema
            with open(data_contract.custom_schema_path, "r") as f:
                schema = json.load(f)

            # Create a validator to get all errors
            validatorClass = jsonschema.validators.validator_for(schema)
            validator = validatorClass(schema)
            errors = list(validator.iter_errors(data_contract.contract_content))

            if not errors:
                # No validation errors - success
                results.append(
                    ValidationResult(
                        contract_file=data_contract.contract_path,
                        attribute="schema",
                        check_type="json_schema",
                        passed=True,
                        message="Contract validates against custom schema",
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

        except FileNotFoundError:
            results.append(
                ValidationResult(
                    contract_file=data_contract.contract_path,
                    attribute="schema",
                    check_type="json_schema",
                    passed=False,
                    message=f"Custom schema file not found: {data_contract.custom_schema_path}",
                )
            )
        except json.JSONDecodeError as e:
            results.append(
                ValidationResult(
                    contract_file=data_contract.contract_path,
                    attribute="schema",
                    check_type="json_schema",
                    passed=False,
                    message=f"Invalid JSON in custom schema file: {e}",
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
        """
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

    def _get_attribute_values(self, data: Dict, attribute_path: str) -> List[Any]:
        """
        Extract values from nested data structure based on attribute path

        Args:
            data: The data dictionary
            attribute_path: Dot-separated attribute path (e.g., 'models.fields.unique')
                Supports wildcard '*' to match all items (e.g., 'models.*.fields')

        Returns:
            List of values found at the attribute path
        """
        parts = attribute_path.split(".")
        return self._traverse_path(data, parts, [])

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
            return [data] if data is not None else []

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
