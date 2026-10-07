"""Configuration loader utilities."""

import json
import yaml
from pathlib import Path
from typing import Any, Dict


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file.

    Supports JSON and YAML formats.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If unsupported format
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if path.suffix.lower() == ".json":
        with open(path, "r") as f:
            return json.load(f)
    elif path.suffix.lower() in [".yaml", ".yml"]:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    else:
        raise ValueError(f"Unsupported config format: {path.suffix}")
