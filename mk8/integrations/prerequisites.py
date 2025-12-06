"""Prerequisite checking for external tools."""

import shutil
import subprocess
from typing import Optional

from mk8.integrations.prerequisite_models import (
    PrerequisiteResults,
    PrerequisiteStatus,
)


class PrerequisiteChecker:
    """Checks for required external tools."""

    def check_all(self) -> PrerequisiteResults:
        """
        Check all prerequisites.

        Returns:
            PrerequisiteResults with status of all checks
        """
        return PrerequisiteResults(
            docker=self.check_docker(),
            kind=self.check_kind(),
            kubectl=self.check_kubectl(),
        )

    def check_docker(self) -> PrerequisiteStatus:
        """
        Check Docker installation and daemon status.

        Returns:
            PrerequisiteStatus for Docker
        """
        path = shutil.which("docker")

        if not path:
            return self._create_status(
                name="docker",
                installed=False,
                error="Docker is not installed or not in PATH",
            )

        daemon_running = self.is_docker_daemon_running()

        if not daemon_running:
            return self._create_status(
                name="docker",
                installed=True,
                daemon_running=False,
                path=path,
                error="Docker daemon is not running",
            )

        return self._create_status(
            name="docker",
            installed=True,
            daemon_running=True,
            path=path,
        )

    def check_kind(self) -> PrerequisiteStatus:
        """
        Check kind installation.

        Returns:
            PrerequisiteStatus for kind
        """
        return self._check_tool("kind")

    def check_kubectl(self) -> PrerequisiteStatus:
        """
        Check kubectl installation.

        Returns:
            PrerequisiteStatus for kubectl
        """
        return self._check_tool("kubectl")

    def _check_tool(self, tool_name: str) -> PrerequisiteStatus:
        """
        Check if a tool is installed.

        Args:
            tool_name: Name of the tool to check

        Returns:
            PrerequisiteStatus for the tool
        """
        path = shutil.which(tool_name)

        if not path:
            return self._create_status(
                name=tool_name,
                installed=False,
                error=f"{tool_name} is not installed or not in PATH",
            )

        return self._create_status(
            name=tool_name,
            installed=True,
            path=path,
        )

    def _create_status(
        self,
        name: str,
        installed: bool,
        daemon_running: Optional[bool] = None,
        path: Optional[str] = None,
        error: Optional[str] = None,
    ) -> PrerequisiteStatus:
        """
        Create a PrerequisiteStatus with default values.

        Args:
            name: Tool name
            installed: Whether tool is installed
            daemon_running: Whether daemon is running (for Docker)
            path: Path to tool executable
            error: Error message if check failed

        Returns:
            PrerequisiteStatus with all fields populated
        """
        return PrerequisiteStatus(
            name=name,
            installed=installed,
            version=None,
            version_ok=True,
            daemon_running=daemon_running,
            path=path,
            error=error,
        )

    def is_docker_daemon_running(self) -> bool:
        """
        Check if Docker daemon is running.

        Returns:
            True if daemon is running, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False
