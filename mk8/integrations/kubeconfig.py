"""Kubeconfig file handling for kubectl configuration management."""

import os
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from mk8.core.errors import MK8Error


class KubeconfigError(MK8Error):
    """Base exception for kubeconfig operations."""

    pass


class KubeconfigManager:
    """
    Manages kubectl configuration file operations.

    Handles all kubeconfig operations including reading, writing, parsing,
    merging, backups, and atomic updates in a single cohesive class.
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        max_backups: int = 5,
    ):
        """
        Initialize the kubeconfig manager.

        Args:
            config_path: Path to kubeconfig file
                (defaults to ~/.kube/config or KUBECONFIG)
            max_backups: Maximum number of backup files to retain
        """
        if config_path is None:
            self.config_path = self._get_config_path()
        else:
            self.config_path = Path(config_path)

        self.max_backups = max_backups
        self._previous_context: Optional[str] = None

    def _get_config_path(self) -> Path:
        """
        Get kubeconfig path from environment or default.

        Returns:
            Path to kubeconfig file
        """
        kubeconfig_env = os.environ.get("KUBECONFIG")
        if kubeconfig_env:
            # Use first path if multiple are specified
            return Path(kubeconfig_env.split(":")[0])
        return Path.home() / ".kube" / "config"

    def _read_config(self) -> Dict[str, Any]:
        """
        Read and parse kubeconfig file.

        Returns:
            Parsed kubeconfig as dictionary

        Raises:
            KubeconfigError: If file cannot be read or parsed
        """
        if not self.config_path.exists():
            # Return empty config structure
            return {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [],
                "contexts": [],
                "users": [],
                "current-context": None,
                "preferences": {},
            }

        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise KubeconfigError(
                    f"Kubeconfig file contains invalid structure: {self.config_path}",
                    suggestions=[
                        "Validate YAML syntax: yamllint ~/.kube/config",
                        "Restore from backup in ~/.kube/backups/",
                        "Check for manual edits that may have introduced errors",
                    ],
                )

            # Validate required fields
            required_fields = ["apiVersion", "kind", "clusters", "contexts", "users"]
            for field in required_fields:
                if field not in config:
                    raise KubeconfigError(
                        f"Kubeconfig file missing required field: {field}",
                        suggestions=[
                            "Restore from backup in ~/.kube/backups/",
                            "Recreate kubeconfig file",
                        ],
                    )

            return config

        except yaml.YAMLError as e:
            raise KubeconfigError(
                f"Kubeconfig file contains invalid YAML: {e}",
                suggestions=[
                    "Validate YAML syntax: yamllint ~/.kube/config",
                    "Restore from backup in ~/.kube/backups/",
                    "Check for manual edits that may have introduced errors",
                ],
            )
        except Exception as e:
            raise KubeconfigError(
                f"Failed to read kubeconfig file: {e}",
                suggestions=[
                    f"Check file permissions: chmod 600 {self.config_path}",
                    f"Ensure you own the file: ls -la {self.config_path}",
                ],
            )

    def _write_config(self, config: Dict[str, Any]) -> None:
        """
        Write kubeconfig atomically with backup.

        Args:
            config: Kubeconfig dictionary to write

        Raises:
            KubeconfigError: If write operation fails
        """
        # Ensure directory exists with correct permissions
        self.config_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Create backup if file exists
        if self.config_path.exists():
            self._create_backup()

        # Write to temp file
        temp_path = self.config_path.with_suffix(".tmp")
        try:
            # Validate config can be serialized
            yaml_content = yaml.safe_dump(config, default_flow_style=False)

            # Write to temp file
            with open(temp_path, "w") as f:
                f.write(yaml_content)

            # Validate temp file can be parsed back
            with open(temp_path, "r") as f:
                yaml.safe_load(f)

            # Atomic rename
            temp_path.replace(self.config_path)

            # Set secure permissions
            self.config_path.chmod(0o600)

            # Cleanup old backups
            self._cleanup_old_backups()

        except Exception as e:
            raise KubeconfigError(
                f"Failed to write kubeconfig file: {e}",
                suggestions=[
                    "Check directory permissions",
                    f"Verify you can write to {self.config_path.parent}",
                    "Ensure sufficient disk space",
                ],
            )
        finally:
            # Clean up temp file if it still exists
            if temp_path.exists():
                temp_path.unlink()

    def _create_backup(self) -> None:
        """
        Create timestamped backup of current config.

        Raises:
            KubeconfigError: If backup creation fails
        """
        if not self.config_path.exists():
            return

        try:
            # Create backups directory
            backup_dir = self.config_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True, mode=0o700)

            # Create timestamped backup filename
            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            backup_path = backup_dir / f"config.backup.{timestamp}"

            # Copy file
            shutil.copy2(self.config_path, backup_path)

            # Set secure permissions on backup
            backup_path.chmod(0o600)

        except Exception as e:
            raise KubeconfigError(
                f"Failed to create backup: {e}",
                suggestions=[
                    "Check directory permissions",
                    f"Verify you can write to {backup_dir}",
                ],
            )

    def _cleanup_old_backups(self) -> None:
        """Remove old backups beyond retention limit."""
        backup_dir = self.config_path.parent / "backups"
        if not backup_dir.exists():
            return

        try:
            # Get all backup files sorted by modification time (newest first)
            backups = sorted(
                backup_dir.glob("config.backup.*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            # Remove backups beyond the limit
            for backup in backups[self.max_backups :]:
                backup.unlink()

        except Exception:
            # Don't fail the operation if cleanup fails
            pass

    def add_cluster(
        self,
        cluster_name: str,
        cluster_config: Dict[str, Any],
        set_current: bool = True,
    ) -> None:
        """
        Add a new cluster configuration to kubeconfig.

        Args:
            cluster_name: Name of the cluster
            cluster_config: Cluster configuration dict with server, ca, etc.
            set_current: Whether to set this cluster as current context

        Raises:
            KubeconfigError: If operation fails
        """
        try:
            # Read existing config
            config = self._read_config()

            # Store previous context if setting new one
            if set_current:
                self._previous_context = config.get("current-context")

            # Handle naming conflicts
            final_cluster_name = self._resolve_naming_conflict(
                cluster_name, [c["name"] for c in config.get("clusters", [])]
            )

            # Add cluster entry
            cluster_entry = {"name": final_cluster_name, "cluster": cluster_config}
            if "clusters" not in config:
                config["clusters"] = []
            config["clusters"].append(cluster_entry)

            # Add context entry
            context_entry = {
                "name": final_cluster_name,
                "context": {"cluster": final_cluster_name, "user": final_cluster_name},
            }
            if "contexts" not in config:
                config["contexts"] = []
            config["contexts"].append(context_entry)

            # Add user entry (placeholder - will be populated by cluster creation)
            user_entry = {"name": final_cluster_name, "user": {}}
            if "users" not in config:
                config["users"] = []
            config["users"].append(user_entry)

            # Set current context if requested
            if set_current:
                config["current-context"] = final_cluster_name

            # Write updated config
            self._write_config(config)

        except KubeconfigError:
            raise
        except Exception as e:
            raise KubeconfigError(
                f"Failed to add cluster: {e}",
                suggestions=[
                    "Check cluster configuration is valid",
                    "Ensure kubeconfig file is not corrupted",
                    "Verify file permissions",
                ],
            )

    def _resolve_naming_conflict(
        self, desired_name: str, existing_names: List[str]
    ) -> str:
        """
        Resolve naming conflicts by appending numeric suffix.

        Args:
            desired_name: Desired cluster name
            existing_names: List of existing cluster names

        Returns:
            Unique cluster name
        """
        if desired_name not in existing_names:
            return desired_name

        # Find next available suffix
        suffix = 2
        while f"{desired_name}-{suffix}" in existing_names:
            suffix += 1

        return f"{desired_name}-{suffix}"

    def remove_cluster(
        self,
        cluster_name: str,
        restore_previous_context: bool = True,
    ) -> None:
        """
        Remove a cluster configuration from kubeconfig.

        Args:
            cluster_name: Name of the cluster to remove
            restore_previous_context: Whether to restore previous context

        Raises:
            KubeconfigError: If operation fails
        """
        try:
            # Read existing config
            config = self._read_config()

            # Check if cluster exists
            if not any(c["name"] == cluster_name for c in config.get("clusters", [])):
                raise KubeconfigError(
                    f"Cluster '{cluster_name}' not found in kubeconfig",
                    suggestions=[
                        "List available clusters: kubectl config get-clusters",
                        "Check cluster name spelling",
                    ],
                )

            # Remove cluster entry
            config["clusters"] = [
                c for c in config.get("clusters", []) if c["name"] != cluster_name
            ]

            # Remove context entry
            config["contexts"] = [
                c for c in config.get("contexts", []) if c["name"] != cluster_name
            ]

            # Remove user entry
            config["users"] = [
                u for u in config.get("users", []) if u["name"] != cluster_name
            ]

            # Handle current context
            if config.get("current-context") == cluster_name:
                # Try to restore previous context
                if restore_previous_context and self._previous_context:
                    # Check if previous context still exists
                    if any(
                        c["name"] == self._previous_context
                        for c in config.get("contexts", [])
                    ):
                        config["current-context"] = self._previous_context
                    elif config.get("contexts"):
                        # Select first available context
                        config["current-context"] = config["contexts"][0]["name"]
                    else:
                        config["current-context"] = None
                elif config.get("contexts"):
                    # Select first available context
                    config["current-context"] = config["contexts"][0]["name"]
                else:
                    # No contexts left
                    config["current-context"] = None

            # Write updated config
            self._write_config(config)

        except KubeconfigError:
            raise
        except Exception as e:
            raise KubeconfigError(
                f"Failed to remove cluster: {e}",
                suggestions=[
                    "Ensure kubeconfig file is not corrupted",
                    "Verify file permissions",
                ],
            )

    def get_current_context(self) -> Optional[str]:
        """
        Get the current kubectl context.

        Returns:
            Current context name or None if not set
        """
        try:
            config = self._read_config()
            return config.get("current-context")
        except Exception:
            return None

    def set_current_context(self, context_name: str) -> None:
        """
        Set the current kubectl context.

        Args:
            context_name: Name of the context to set as current

        Raises:
            KubeconfigError: If operation fails
        """
        try:
            config = self._read_config()

            # Store previous context
            self._previous_context = config.get("current-context")

            # Set new context
            config["current-context"] = context_name

            # Write updated config
            self._write_config(config)

        except KubeconfigError:
            raise
        except Exception as e:
            raise KubeconfigError(
                f"Failed to set current context: {e}",
                suggestions=[
                    "Verify context exists: kubectl config get-contexts",
                    "Check context name spelling",
                ],
            )

    def list_clusters(self) -> List[str]:
        """
        List all cluster names in kubeconfig.

        Returns:
            List of cluster names
        """
        try:
            config = self._read_config()
            return [c["name"] for c in config.get("clusters", [])]
        except Exception:
            return []

    def cluster_exists(self, cluster_name: str) -> bool:
        """
        Check if a cluster exists in kubeconfig.

        Args:
            cluster_name: Name of the cluster to check

        Returns:
            True if cluster exists, False otherwise
        """
        try:
            config = self._read_config()
            return any(c["name"] == cluster_name for c in config.get("clusters", []))
        except Exception:
            return False
