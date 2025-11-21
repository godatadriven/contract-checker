import json
from pathlib import Path

from contract_checker.utils.utils import load_json_schema

path = Path(
    "/Users/sonu/Developer/3Resources/4AEContractChecker/contract-checker/src/contract_checker/contract_schemas/dcs/1.1.0/schema.json"
)
schema_content = load_json_schema(path)
print(json.dumps(schema_content, indent=2))
