import unittest
from typing import Any, Dict


class TestCheck(unittest.TestCase):
    def set_up_contract(self) -> None:
        self.base_contract: Dict[str, Any] = {}

        self.contract_with_required_field_missing: Dict[str, Any] = {}

        self.contract_with_field_to_exclude: Dict[str, Any] = {}

        self.contract_with_pattern_mismatch: Dict[str, Any] = {}

        self.contract_with_minimum_number_of_items: Dict[str, Any] = {}

        self.contract_with_less_than_minimum_items: Dict[str, Any] = {}

    def test_if_required_field_present(self) -> None:
        pass

    def test_if_field_excluded(self) -> None:
        pass

    def test_if_pattern_matched(self) -> None:
        pass

    def test_if_minimum_number_of_items(self) -> None:
        pass
