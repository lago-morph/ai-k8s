"""Helm client for package management operations."""

import subprocess
import time
import yaml
from typing import Dict, Any, List, Optional

from mk8.core.errors import MK8Error


class HelmError(MK8Error):
    """Helm operation failed."""

    pass


class HelmClient:
    """
    Client for Helm operations.

    Provides a Python interface to Helm CLI commands with
    error handling and output parsing.
    """

    def __init__(self, context: str = "kind-mk8-bootstrap"):
        """
        Initialize the Helm client.

        Args:
            context: Kubernetes context to use for operations
        """
        self.context = context

    def _run_helm_command(self, args: List[str], timeout: int = 300) -> str:
        """
        Run a helm command and return output.

        Args:
            args: Command arguments
            timeout: Command timeout in seconds

        Returns:
            Command stdout

        Raises:
            HelmError: If command fails
        """
        cmd = ["helm"] + args + ["--kube-context", self.context]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode != 0:
                raise HelmError(
                    f"helm command failed: {result.stderr}",
                    suggestions=self._parse_helm_error(result.stderr),
                )
            return result.stdout
        except subprocess.TimeoutExpired:
            raise HelmError(
                f"helm command timed out after {timeout} seconds",
                suggestions=[
                    "Check cluster connectivity",
                    "Check if cluster is responsive: kubectl get nodes",
                    "Try increasing timeout",
                ],
            )
        except FileNotFoundError:
            raise HelmError(
                "helm command not found",
                suggestions=[
                    "Install Helm: https://helm.sh/docs/intro/install/",
                    "Ensure helm is in your PATH",
                    "Verify installation: helm version",
                ],
            )

    def _parse_helm_error(self, stderr: str) -> List[str]:
        """
        Parse helm error output and provide suggestions.

        Args:
            stderr: Error output from helm

        Returns:
            List of suggestions
        """
        suggestions = []

        if "not found" in stderr.lower() and "repository" in stderr.lower():
            suggestions.extend(
                [
                    "Add the repository: helm repo add <name> <url>",
                    "Update repositories: helm repo update",
                    "List repositories: helm repo list",
                ]
            )
        elif "already exists" in stderr.lower():
            suggestions.extend(
                [
                    "Use --force flag to overwrite",
                    "Uninstall first: helm uninstall <release>",
                    "Use different release name",
                ]
            )
        elif "connection refused" in stderr.lower():
            suggestions.extend(
                [
                    "Check cluster is running: kubectl get nodes",
                    "Verify context: kubectl config current-context",
                    "Check cluster connectivity",
                ]
            )
        elif "forbidden" in stderr.lower() or "unauthorized" in stderr.lower():
            suggestions.extend(
                [
                    "Check RBAC permissions",
                    "Verify service account has required permissions",
                    "Check if cluster-admin role is needed",
                ]
            )
        else:
            suggestions.extend(
                [
                    "Check helm status: helm status <release>",
                    "Verify cluster connectivity: kubectl get nodes",
                    "Check helm version compatibility",
                ]
            )

        return suggestions

    def add_repository(self, name: str, url: str, force: bool = False) -> None:
        """
        Add a Helm repository.

        Args:
            name: Repository name
            url: Repository URL
            force: Force update if repository exists

        Raises:
            HelmError: If operation fails
        """
        args = ["repo", "add", name, url]
        if force:
            args.append("--force-update")

        self._run_helm_command(args)

    def update_repositories(self) -> None:
        """
        Update all Helm repositories.

        Raises:
            HelmError: If operation fails
        """
        self._run_helm_command(["repo", "update"])

    def install_chart(
        self,
        release_name: str,
        chart: str,
        namespace: str,
        values: Optional[Dict[str, Any]] = None,
        create_namespace: bool = True,
        wait: bool = True,
        timeout: int = 600,
    ) -> None:
        """
        Install a Helm chart.

        Args:
            release_name: Name for the release
            chart: Chart name (repo/chart or path)
            namespace: Target namespace
            values: Values to override
            create_namespace: Create namespace if it doesn't exist
            wait: Wait for installation to complete
            timeout: Installation timeout in seconds

        Raises:
            HelmError: If installation fails
        """
        args = ["install", release_name, chart, "--namespace", namespace]

        if create_namespace:
            args.append("--create-namespace")

        if wait:
            args.extend(["--wait", "--timeout", f"{timeout}s"])

        # Handle values
        if values:
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                yaml.safe_dump(values, f)
                values_file = f.name

            try:
                args.extend(["--values", values_file])
                self._run_helm_command(args, timeout=timeout + 60)
            finally:
                os.unlink(values_file)
        else:
            self._run_helm_command(args, timeout=timeout + 60)

    def uninstall_release(
        self, release_name: str, namespace: str, wait: bool = True
    ) -> None:
        """
        Uninstall a Helm release.

        Args:
            release_name: Name of the release
            namespace: Target namespace
            wait: Wait for uninstallation to complete

        Raises:
            HelmError: If uninstallation fails
        """
        args = ["uninstall", release_name, "--namespace", namespace]
        if wait:
            args.append("--wait")

        self._run_helm_command(args)

    def list_releases(self, namespace: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List Helm releases.

        Args:
            namespace: Namespace to list (all namespaces if None)

        Returns:
            List of release information dicts

        Raises:
            HelmError: If listing fails
        """
        args = ["list", "--output", "json"]
        if namespace:
            args.extend(["--namespace", namespace])
        else:
            args.append("--all-namespaces")

        try:
            output = self._run_helm_command(args)
            if not output.strip():
                return []
            return yaml.safe_load(output) or []
        except Exception:
            return []

    def get_release_status(self, release_name: str, namespace: str) -> Dict[str, Any]:
        """
        Get status of a Helm release.

        Args:
            release_name: Name of the release
            namespace: Target namespace

        Returns:
            Release status information

        Raises:
            HelmError: If status retrieval fails
        """
        args = ["status", release_name, "--namespace", namespace, "--output", "json"]
        output = self._run_helm_command(args)
        return yaml.safe_load(output)

    def release_exists(self, release_name: str, namespace: str) -> bool:
        """
        Check if a Helm release exists.

        Args:
            release_name: Name of the release
            namespace: Target namespace

        Returns:
            True if release exists, False otherwise
        """
        try:
            self.get_release_status(release_name, namespace)
            return True
        except HelmError:
            return False
