from pathlib import Path

from contract_checker.checks.check_base import Check


class CheckString(Check):
    check_content: dict
    
    def check_if_field_present(contract_content: dict, check_content: dict) -> bool:
        """Perform a single check on the contract content."""
        # Example check logic (to be expanded based on actual requirements)
        field = check_content.get("field")
        if field in contract_content:
            return True
        return False