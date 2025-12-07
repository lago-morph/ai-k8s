"""File I/O operations for configuration management."""

import os
import stat
from pathlib import Path
from typing import Dict, Optional

from mk8.core.errors import ConfigurationError


class FileIO:
    """Handles file I/O operations for mk8 configuration."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize file I/O handler.

        Args:
            config_path: Path to config file (defaults to ~/.config/mk8)
        """
        if config_path is None:
            home = Path.home()
            self.config_path = home / ".config" / "mk8"
        else:
            self.config_path = Path(config_path)

    def read_config_file(self) -> Optional[Dict[str, str]]:
        """
        Read configuration from config file.

        Returns:
            Dictionary of key-value pairs or None if file doesn't exist
        """
        if not self.config_path.exists():
            return None

        config = {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Parse key=value format
                    if "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()

            return config
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read config file: {e}",
                suggestions=[
                    "Check file permissions",
                    f"Verify file exists at {self.config_path}",
                    "Run 'mk8 config' to recreate the configuration",
                ],
            )

    def write_config_file(self, config: Dict[str, str]) -> None:
        """
        Write configuration to config file with secure permissions.

        Args:
            config: Dictionary of key-value pairs to write

        Raises:
            ConfigurationError: If file cannot be written
        """
        try:
            # Ensure parent directory exists
            self.ensure_config_directory()

            # Write config file with UTF-8 encoding
            with open(self.config_path, "w", encoding="utf-8") as f:
                for key, value in config.items():
                    f.write(f"{key}={value}\n")

            # Set secure permissions (0600)
            self.set_secure_permissions(str(self.config_path))

        except Exception as e:
            raise ConfigurationError(
                f"Failed to write config file: {e}",
                suggestions=[
                    "Check directory permissions",
                    f"Verify you can write to {self.config_path.parent}",
                    "Ensure sufficient disk space",
                ],
            )

    def ensure_config_directory(self) -> None:
        """Ensure config directory exists."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def set_secure_permissions(self, file_path: str) -> None:
        """
        Set file permissions to 0600 (owner read/write only).

        Args:
            file_path: Path to file

        Raises:
            ConfigurationError: If permissions cannot be set
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise ConfigurationError(
                    f"Cannot set permissions on nonexistent file: {file_path}",
                    suggestions=[
                        "Ensure the file is created before setting permissions",
                    ],
                )

            # Set permissions to 0600 (owner read/write only)
            # On Windows, this may not work as expected, but we try anyway
            if os.name != "nt":
                path.chmod(0o600)

        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Failed to set secure permissions: {e}",
                suggestions=[
                    "Check file ownership",
                    "Verify filesystem supports permission changes",
                ],
            )

    def check_file_permissions(self, file_path: str) -> bool:
        """
        Check if file has secure permissions (0600).

        Args:
            file_path: Path to file

        Returns:
            True if permissions are secure (0600), False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False

            # On Windows, permission checking works differently
            if os.name == "nt":
                return True

            # Check if permissions are 0600
            file_stat = path.stat()
            mode = stat.S_IMODE(file_stat.st_mode)

            # 0600 = 0o600 = owner read/write only
            return mode == 0o600

        except Exception:
            return False
