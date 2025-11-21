# import operator
# from functools import reduce
# from pathlib import Path
# from typing import Any, Mapping, Optional

# from contract_checker.utils.utils import parse_yml_to_dict


# def parse_checks_config(checks_config_path: Path) -> Optional[dict]:
#     """Parse checks from a YAML file."""
#     checks_dict = parse_yml_to_dict(file_path=checks_config_path)
#     if not checks_dict:
#         raise ValueError(f"Failed to parse checks from {checks_config_path}")
#     return checks_dict if isinstance(checks_dict, dict) else None


# def parse_field(check_content: dict[str, list[str]], field: str) -> list[str]:
#     """Extract the field to be checked from the check content."""
#     return check_content.get(field, [])


# def get_nested_value(
#     contract_content: Mapping[str, Any], path: str, default: Optional[Any] = None
# ) -> Optional[Any]:
#     """Access nested dict using dot notation string."""
#     keys = path.split(".")
#     try:
#         return reduce(operator.getitem, keys, contract_content)
#     except KeyError as e:
#         if default is not None:
#             return default
#         raise KeyError(f"Key {e} not found in path '{path}'") from e
#     except TypeError as e:
#         if default is not None:
#             return default
#         raise TypeError(f"Cannot access path '{path}': {e}") from e


# def check_if_field_present(
#     contract_content: Mapping[str, Any], check_content: Mapping[str, Any]
# ) -> bool:
#     """Perform a single check on the contract content."""
#     field_path = check_content.get("field")
#     if not isinstance(field_path, str):
#         return False

#     value = get_nested_value(contract_content, field_path)
#     if value:
#         print(f"Field '{field_path}' is present in the contract.")
#         return True
#     return False
