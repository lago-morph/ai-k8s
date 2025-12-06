"""Prerequisite status data models."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PrerequisiteStatus:
    """Status of a single prerequisite check."""

    name: str  # Tool name (e.g., "docker")
    installed: bool  # Whether tool is installed
    version: Optional[str]  # Installed version if available
    version_ok: bool  # Whether version meets minimum requirement
    daemon_running: Optional[bool]  # For tools with daemons (Docker)
    path: Optional[str]  # Path to tool executable
    error: Optional[str]  # Error message if check failed

    def is_satisfied(self) -> bool:
        """
        Check if prerequisite is fully satisfied.

        Returns:
            True if all checks pass, False otherwise
        """
        if not self.installed or not self.version_ok:
            return False
        if self.daemon_running is not None and not self.daemon_running:
            return False
        return True
