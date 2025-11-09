"""Configuration loader for YAML-based configuration system.

This module provides utilities to load and merge configuration from:
1. Default configuration (configs/default.yaml)
2. Environment-specific configuration (configs/{env}.yaml)
3. Environment variables (highest priority)

Configuration hierarchy:
    YAML defaults → Environment-specific YAML → Environment variables → Runtime parameters
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from langgraph_agent.monitoring.logging import get_logger

logger = get_logger(__name__)


def get_config_path() -> Optional[Path]:
    """Get the path to the configs directory.

    Looks for configs in project root: /path/to/project/configs/

    Returns:
        Path to configs directory or None if not found
    """
    # Project root configs directory
    # src/langgraph_agent/utils/config_loader.py -> ../../../configs
    config_path = Path(__file__).parent.parent.parent.parent / "configs"
    if config_path.exists() and config_path.is_dir():
        logger.debug(f"Found configs at: {config_path}")
        return config_path

    logger.warning("Config directory not found, will use hardcoded defaults only")
    logger.warning(f"  Tried path: {config_path}")
    return None


def load_yaml_config(config_path: Optional[Path], filename: str) -> Dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        config_path: Path to configs directory
        filename: Name of the YAML file to load

    Returns:
        Dictionary with configuration, empty dict if file not found
    """
    if config_path is None:
        return {}

    file_path = config_path / filename
    if not file_path.exists():
        logger.debug(f"Config file not found: {file_path}")
        return {}

    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f) or {}
        logger.debug(f"Loaded config from {file_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config from {file_path}: {e}")
        return {}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base dictionary
        override: Dictionary with values to override

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def load_config(environment: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML files and environment.

    Merges configurations in this order:
    1. configs/default.yaml (baseline)
    2. configs/{environment}.yaml (environment-specific overrides)

    Args:
        environment: Environment name (dev, prod, etc.).
                    Defaults to DEPLOYMENT_ENVIRONMENT env var or "dev"

    Returns:
        Merged configuration dictionary
    """
    # Determine environment
    if environment is None:
        environment = os.getenv("DEPLOYMENT_ENVIRONMENT", "dev")

    logger.info(f"Loading configuration for environment: {environment}")

    # Get config directory
    config_path = get_config_path()

    # Load default config
    config = load_yaml_config(config_path, "default.yaml")

    # Load environment-specific config and merge
    env_config = load_yaml_config(config_path, f"{environment}.yaml")
    config = deep_merge(config, env_config)

    logger.info(f"Configuration loaded with {len(config)} top-level keys")
    return config


def get_config_value(config: Dict[str, Any], key_path: str, env_var: Optional[str] = None, default: Any = None) -> Any:
    """Get a configuration value with fallback chain.

    Priority order:
    1. Environment variable (if env_var specified)
    2. Value from config dict at key_path
    3. Default value

    Args:
        config: Configuration dictionary
        key_path: Dot-separated path to config value (e.g., "model.endpoint_name")
        env_var: Environment variable name to check first
        default: Default value if not found

    Returns:
        Configuration value

    Example:
        >>> config = {"model": {"endpoint_name": "claude"}}
        >>> get_config_value(config, "model.endpoint_name", "LLM_ENDPOINT_NAME")
        # Returns env var LLM_ENDPOINT_NAME if set, else "claude"
    """
    # Check environment variable first
    if env_var and env_var in os.environ:
        value = os.getenv(env_var)
        logger.debug(f"Using env var {env_var}={value}")
        return value

    # Navigate through config dict
    keys = key_path.split(".")
    value = config

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            logger.debug(f"Config key not found: {key_path}, using default: {default}")
            return default

    logger.debug(f"Using config value for {key_path}={value}")
    return value


# Global config cache
_config_cache: Optional[Dict[str, Any]] = None


def get_cached_config(environment: Optional[str] = None) -> Dict[str, Any]:
    """Get cached configuration or load if not cached.

    Args:
        environment: Environment name

    Returns:
        Configuration dictionary
    """
    global _config_cache

    if _config_cache is None:
        _config_cache = load_config(environment)

    return _config_cache


def reload_config(environment: Optional[str] = None) -> Dict[str, Any]:
    """Force reload of configuration from files.

    Args:
        environment: Environment name

    Returns:
        Reloaded configuration dictionary
    """
    global _config_cache
    _config_cache = None
    return get_cached_config(environment)
