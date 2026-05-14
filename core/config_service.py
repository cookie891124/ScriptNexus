"""ConfigService for managing JSON configuration files."""

import json
import os
from typing import Any, Dict, Optional


class ConfigService:
    """Service for loading, saving, and managing JSON configuration files."""

    def __init__(self, config_path: str):
        """Initialize ConfigService with a configuration file path.

        Args:
            config_path: Path to the JSON configuration file.
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from the JSON file.

        Returns:
            Dictionary containing configuration data, or empty dict if file
            doesn't exist or contains invalid JSON.
        """
        if not os.path.exists(self.config_path):
            self._config = {}
            return self._config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except (json.JSONDecodeError, IOError):
            self._config = {}

        return self._config

    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to the JSON file.

        Args:
            config: Configuration dictionary to save. If None, saves current
                internal state. Creates parent directories if they don't exist.
        """
        if config is not None:
            self._config = config

        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(self.config_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Supports dot notation for nested keys (e.g., "database.host").

        Args:
            key: Configuration key (supports dot notation for nested keys).
            default: Default value to return if key is not found.

        Returns:
            Configuration value, or default if key is not found.
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_path(self, key: str, default: str = "") -> str:
        """Get a path configuration value, validating that it exists.

        Args:
            key: Configuration key (e.g., "paths.scripts_dir").
            default: Default value to return if key is not found or path doesn't exist.

        Returns:
            Path value if it exists, otherwise default.
        """
        value = self.get(key, default)
        if value and isinstance(value, str) and os.path.exists(value):
            return value
        return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by key.

        Supports dot notation for nested keys (e.g., "database.host").

        Args:
            key: Configuration key (supports dot notation for nested keys).
            value: Value to set.
        """
        keys = key.split('.')
        config = self._config

        # Navigate to parent, creating dicts as needed
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        # Set the final value
        config[keys[-1]] = value

    def delete(self, key: str) -> None:
        """Delete a configuration value by key.

        Supports dot notation for nested keys (e.g., "database.host").

        Args:
            key: Configuration key to delete (supports dot notation).
        """
        keys = key.split('.')
        config = self._config

        # Navigate to parent
        for k in keys[:-1]:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return  # Key path doesn't exist, nothing to delete

        # Delete the final key if it exists
        if isinstance(config, dict) and keys[-1] in config:
            del config[keys[-1]]
