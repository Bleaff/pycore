"""core.utils.config_loader

This module contains a single function to load a YAML configuration file for the (NUDC) pipeline.

"""

import yaml
from pathlib import Path

def load_config(path: str | Path) -> dict:
    """
    Load YAML pipeline configuration.

    Args:
        path (str | Path): Path to YAML config.

    Returns:
        dict: Parsed configuration dictionary.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"YAML config not found: {path}")

    with open(path, "r") as f:
        return yaml.safe_load(f)
