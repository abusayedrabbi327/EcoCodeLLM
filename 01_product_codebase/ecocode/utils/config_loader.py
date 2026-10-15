"""
config_loader.py — Loads and validates the central config.yaml file.

Provides a singleton-like access point so all modules read from the
same configuration without re-parsing YAML on every call.
"""

import os
import yaml
from pathlib import Path


# Default config path relative to project root
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"

# Module-level cache for the loaded configuration
_config_cache = None


def load_config(config_path: str = None) -> dict:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Optional path to config.yaml. If None, uses the
                     default location at project root.

    Returns:
        dict: The parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    global _config_cache

    if _config_cache is not None and config_path is None:
        return _config_cache

    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}\n"
            f"Please copy config.yaml.example to config.yaml and update settings."
        )

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Validate required sections exist
    required_sections = ["llm", "testing", "profiler", "weights", "output"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: '{section}'")

    # Validate weights sum to 1.0
    weights = config["weights"]
    total = weights.get("energy", 0) + weights.get("time", 0) + weights.get("memory", 0)
    if abs(total - 1.0) > 0.01:
        raise ValueError(
            f"Decision engine weights must sum to 1.0, got {total:.2f}. "
            f"Current: energy={weights.get('energy')}, time={weights.get('time')}, "
            f"memory={weights.get('memory')}"
        )

    _config_cache = config
    return config


def get_config_value(section: str, key: str, default=None):
    """
    Retrieve a specific configuration value.

    Args:
        section: Top-level config section (e.g., 'llm', 'profiler').
        key: Key within the section.
        default: Fallback value if key is not found.

    Returns:
        The configuration value, or the default.
    """
    config = load_config()
    return config.get(section, {}).get(key, default)


def reset_config_cache():
    """Clear the cached configuration (useful for testing)."""
    global _config_cache
    _config_cache = None
