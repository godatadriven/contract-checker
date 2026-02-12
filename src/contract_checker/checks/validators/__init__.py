"""Built-in validation checks for data contract validation.

This module provides the standard set of validation checks that can be used to
validate data contract attributes. Each check is implemented as a class that
inherits from :class:`~contract_checker.checks.base.Check`.

Available Checks
----------------

- :class:`RequiredCheck` - Validates that a field exists and is not null
- :class:`PatternCheck` - Validates that values match a regex pattern
- :class:`AcceptedValuesCheck` - Validates that values are in an allowed list
- :class:`MinItemsCheck` - Validates that lists have a minimum number of items
- :class:`MaxItemsCheck` - Validates that lists don't exceed a maximum number of items

Usage in Configuration
----------------------

Checks are configured in your ``data-contract-checks.yml`` file:

.. code-block:: yaml

    data_contract_checks:
      - attribute: info.title
        checks:
          - required: true
          - pattern: ^[A-Z]

      - attribute: tags
        checks:
          - accepted_values:
              - production
              - staging
          - min_items: 1
          - max_items: 10
"""

from .accepted_values_check import AcceptedValuesCheck
from .items_check import MaxItemsCheck, MinItemsCheck
from .pattern_check import PatternCheck
from .required_check import RequiredCheck

__all__ = [
    "AcceptedValuesCheck",
    "MaxItemsCheck",
    "MinItemsCheck",
    "PatternCheck",
    "RequiredCheck",
]
