"""Prerequisite status data models."""

from dataclasses import dataclass
from typing import List, Optional


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


@dataclass
class PrerequisiteResults:
    """Results from checking all prerequisites."""

    docker: PrerequisiteStatus
    kind: PrerequisiteStatus
    kubectl: PrerequisiteStatus

    def all_satisfied(self) -> bool:
        """
        Check if all prerequisites are satisfied.

        Returns:
            True if all prerequisites are satisfied, False otherwise
        """
        return all(
            [
                self.docker.is_satisfied(),
                self.kind.is_satisfied(),
                self.kubectl.is_satisfied(),
            ]
        )

    def get_missing(self) -> List[str]:
        """
        Get list of missing prerequisite names.

        Returns:
            List of tool names that are not satisfied
        """
        missing = []
        if not self.docker.is_satisfied():
            missing.append("docker")
        if not self.kind.is_satisfied():
            missing.append("kind")
        if not self.kubectl.is_satisfied():
            missing.append("kubectl")
        return missing

    def get_status_summary(self) -> str:
        """
        Get formatted status summary of all prerequisites.

        Returns:
            Multi-line string with status of each prerequisite
        """
        lines = []
        for prereq in [self.docker, self.kind, self.kubectl]:
            if prereq.is_satisfied():
                status_icon = "✓"
                status_text = f"{prereq.name}: {status_icon} {prereq.version}"
                if prereq.path:
                    status_text += f" ({prereq.path})"
            else:
                status_icon = "✗"
                status_text = f"{prereq.name}: {status_icon}"
                if prereq.version:
                    status_text += f" {prereq.version}"
                if prereq.error:
                    status_text += f" - {prereq.error}"
            lines.append(status_text)
        return "\n".join(lines)
