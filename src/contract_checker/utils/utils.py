import logging
from pathlib import Path
from typing import Optional

import yaml


def parse_yml_to_dict(file_path: Path) -> Optional[dict]:
    """Parse a data contract from a YAML string."""
    try:
        with open(file_path, "r") as file:
            yaml_dict = yaml.safe_load(file)
        return yaml_dict if isinstance(yaml_dict, dict) else None
    except Exception as e:
        logging.warning(f"Failed to parse YAML: {e}")
        return None


def is_dir_or_yaml(path: Path) -> str:
    """Check if the provided path is a directory or a YAML file."""
    if path.is_dir():
        return "directory"
    elif path.is_file() and path.suffix in [".yaml", ".yml"]:
        return "yaml_file"
    else:
        raise ValueError(
            'Provided path is neither a directory nor a file with ".yaml" extension.'
        )
