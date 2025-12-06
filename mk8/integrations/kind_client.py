"""Kind client for local Kubernetes cluster management."""

import subprocess
import time
import yaml
from typing import Dict, Any, List, Optional

from mk8.core.errors import MK8Error


class BootstrapError(MK8Error):
    """Base exception for bootstrap operations."""

    pass


class KindError(BootstrapError):
    """kind CLI operation failed."""

    pass


class ClusterExistsError(BootstrapError):
    """Cluster already exists."""

    pass


class ClusterNotFoundError(BootstrapError):
    """Cluster does not exist."""

    pass


class KindClient:
    """
    Client for kind cluster operations.

    Provides a Python interface to kind CLI commands with
    error handling and output parsing.
    """

    CLUSTER_NAME = "mk8-bootstrap"

    def __init__(self):
        """Initialize the kind client."""
        pass

    def _run_kind_command(self, args: List[str], timeout: int = 300) -> str:
        """
        Run a kind command and return output.

        Args:
            args: Command arguments
            timeout: Command timeout in seconds

        Returns:
            Command stdout

        Raises:
            KindError: If command fails
        """
        cmd = ["kind"] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode != 0:
                raise KindError(
                    f"kind command failed: {result.stderr}",
                    suggestions=self._parse_kind_error(result.stderr),
                )
            return result.stdout
        except subprocess.TimeoutExpired:
            raise KindError(
                f"kind command timed out after {timeout} seconds",
                suggestions=[
                    "Check Docker daemon status",
                    "Check system resources (memory, disk)",
                    "Try increasing timeout",
                ],
            )
        except FileNotFoundError:
            raise KindError(
                "kind command not found",
                suggestions=[
                    "Install kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation",
                    "Ensure kind is in your PATH",
                    "Verify installation: kind version",
                ],
            )

    def _parse_kind_error(self, stderr: str) -> List[str]:
        """
        Parse kind error output and provide suggestions.

        Args:
            stderr: Error output from kind

        Returns:
            List of suggestions
        """
        suggestions = []

        if "already exists" in stderr.lower():
            suggestions.extend([
                "Use 'mk8 bootstrap delete' to remove the existing cluster",
                "Use --force-recreate flag to automatically recreate",
            ])
        elif "port" in stderr.lower() and "already" in stderr.lower():
            suggestions.extend([
                "Check for other services using the port",
                "Stop conflicting services",
                "Modify kind configuration to use different ports",
            ])
        elif "docker" in stderr.lower():
            suggestions.extend([
                "Ensure Docker daemon is running",
                "Check Docker status: docker ps",
                "Restart Docker if needed",
            ])
        else:
            suggestions.extend([
                "Check kind logs for more details",
                "Verify Docker is running: docker ps",
                "Check system resources (memory, disk)",
            ])

        return suggestions

    def cluster_exists(self) -> bool:
        """
        Check if the cluster exists.

        Returns:
            True if cluster exists, False otherwise
        """
        try:
            output = self._run_kind_command(["get", "clusters"])
            return self.CLUSTER_NAME in output.split()
        except KindError:
            return False

    def create_cluster(
        self,
        kubernetes_version: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create a kind cluster.

        Args:
            kubernetes_version: Kubernetes version to use
            config: Optional kind configuration dict

        Raises:
            KindError: If cluster creation fails
            ClusterExistsError: If cluster already exists
        """
        # Check if cluster already exists
        if self.cluster_exists():
            raise ClusterExistsError(
                f"Bootstrap cluster '{self.CLUSTER_NAME}' already exists",
                suggestions=[
                    "Use 'mk8 bootstrap delete' to remove the existing cluster",
                    "Use --force-recreate flag to automatically recreate",
                    "Use 'mk8 bootstrap status' to check cluster state",
                ],
            )

        # Validate kubernetes version if provided
        if kubernetes_version:
            self._validate_kubernetes_version(kubernetes_version)

        # Use default config if not provided
        if config is None:
            config = self._get_default_config()

        # Build command
        cmd_args = ["create", "cluster", "--name", self.CLUSTER_NAME]

        if kubernetes_version:
            cmd_args.extend(["--image", f"kindest/node:{kubernetes_version}"])

        # Write config to temp file and use it
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.safe_dump(config, f)
            config_path = f.name

        try:
            cmd_args.extend(["--config", config_path])
            self._run_kind_command(cmd_args, timeout=600)
        finally:
            import os

            os.unlink(config_path)

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default kind configuration.

        Returns:
            Default kind configuration dict
        """
        return {
            "kind": "Cluster",
            "apiVersion": "kind.x-k8s.io/v1alpha4",
            "nodes": [
                {
                    "role": "control-plane",
                    "extraPortMappings": [
                        {"containerPort": 80, "hostPort": 80, "protocol": "TCP"},
                        {"containerPort": 443, "hostPort": 443, "protocol": "TCP"},
                    ],
                }
            ],
        }

    def _validate_kubernetes_version(self, version: str) -> None:
        """
        Validate Kubernetes version format.

        Args:
            version: Kubernetes version string

        Raises:
            KindError: If version is invalid
        """
        # Basic validation - should start with v and have format like v1.28.0
        if not version.startswith("v"):
            raise KindError(
                f"Invalid Kubernetes version: {version}",
                suggestions=[
                    "Version should start with 'v' (e.g., v1.28.0)",
                    "Check available versions: https://github.com/kubernetes-sigs/kind/releases",
                ],
            )

        # Check format
        parts = version[1:].split(".")
        if len(parts) < 2:
            raise KindError(
                f"Invalid Kubernetes version format: {version}",
                suggestions=[
                    "Use format: v<major>.<minor>.<patch> (e.g., v1.28.0)",
                    "Check available versions: https://github.com/kubernetes-sigs/kind/releases",
                ],
            )

    def delete_cluster(self) -> None:
        """
        Delete the kind cluster.

        Raises:
            KindError: If deletion fails
            ClusterNotFoundError: If cluster doesn't exist
        """
        if not self.cluster_exists():
            raise ClusterNotFoundError(
                f"Bootstrap cluster '{self.CLUSTER_NAME}' does not exist",
                suggestions=[
                    "Use 'mk8 bootstrap status' to check cluster state",
                    "Use 'mk8 bootstrap create' to create a new cluster",
                ],
            )

        self._run_kind_command(["delete", "cluster", "--name", self.CLUSTER_NAME])

    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get cluster information.

        Returns:
            Dict with cluster details (nodes, version, etc.)

        Raises:
            KindError: If cluster doesn't exist or info retrieval fails
        """
        if not self.cluster_exists():
            raise ClusterNotFoundError(
                f"Bootstrap cluster '{self.CLUSTER_NAME}' does not exist",
                suggestions=["Use 'mk8 bootstrap create' to create a cluster"],
            )

        # Get node information using kubectl
        context = f"kind-{self.CLUSTER_NAME}"
        try:
            result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "nodes",
                    "-o",
                    "json",
                    "--context",
                    context,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise KindError(
                    "Failed to get cluster info",
                    suggestions=[
                        "Ensure kubectl is installed",
                        "Check cluster is running: kind get clusters",
                    ],
                )

            nodes_data = yaml.safe_load(result.stdout)
            nodes = []
            kubernetes_version = None

            for node in nodes_data.get("items", []):
                node_info = {
                    "name": node["metadata"]["name"],
                    "status": "Ready"
                    if any(
                        c["type"] == "Ready" and c["status"] == "True"
                        for c in node["status"].get("conditions", [])
                    )
                    else "NotReady",
                }
                nodes.append(node_info)

                if kubernetes_version is None:
                    kubernetes_version = node["status"]["nodeInfo"]["kubeletVersion"]

            return {
                "name": self.CLUSTER_NAME,
                "context": context,
                "kubernetes_version": kubernetes_version,
                "node_count": len(nodes),
                "nodes": nodes,
            }

        except FileNotFoundError:
            raise KindError(
                "kubectl command not found",
                suggestions=[
                    "Install kubectl",
                    "Ensure kubectl is in your PATH",
                ],
            )

    def wait_for_ready(self, timeout: int = 300) -> None:
        """
        Wait for cluster to be ready.

        Args:
            timeout: Maximum seconds to wait

        Raises:
            KindError: If cluster doesn't become ready in time
        """
        context = f"kind-{self.CLUSTER_NAME}"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    [
                        "kubectl",
                        "get",
                        "nodes",
                        "--context",
                        context,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0 and "Ready" in result.stdout:
                    return

            except Exception:
                pass

            time.sleep(5)

        raise KindError(
            f"Cluster did not become ready within {timeout} seconds",
            suggestions=[
                "Check Docker daemon status",
                "Check system resources (memory, disk)",
                "View cluster logs: kind export logs",
            ],
        )

    def get_kubeconfig(self) -> str:
        """
        Get kubeconfig for the cluster.

        Returns:
            Kubeconfig YAML as string

        Raises:
            KindError: If kubeconfig retrieval fails
        """
        if not self.cluster_exists():
            raise ClusterNotFoundError(
                f"Bootstrap cluster '{self.CLUSTER_NAME}' does not exist",
                suggestions=["Use 'mk8 bootstrap create' to create a cluster"],
            )

        return self._run_kind_command(
            ["get", "kubeconfig", "--name", self.CLUSTER_NAME]
        )
