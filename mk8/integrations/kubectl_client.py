"""Kubectl client for Kubernetes operations."""

import subprocess
import json
from typing import Optional, Dict, Any, List

from mk8.business.credential_models import AWSCredentials
from mk8.core.errors import CommandError


class KubectlClient:
    """Client for kubectl operations."""

    def __init__(self) -> None:
        """Initialize kubectl client."""
        pass

    def cluster_exists(self) -> bool:
        """
        Check if a Kubernetes cluster is accessible.

        Returns:
            True if cluster exists and is accessible, False otherwise
        """
        try:
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def apply_secret(
        self,
        credentials: AWSCredentials,
        namespace: str = "crossplane-system",
        secret_name: str = "aws-credentials",
    ) -> None:
        """
        Create or update AWS credentials Kubernetes secret.

        Args:
            credentials: AWS credentials to store in secret
            namespace: Kubernetes namespace for the secret
            secret_name: Name of the secret

        Raises:
            CommandError: If kubectl command fails
        """
        yaml_content = self._build_secret_yaml(credentials, namespace, secret_name)

        try:
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=yaml_content,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise CommandError(
                    f"Failed to apply secret: {result.stderr}",
                    suggestions=[
                        "Verify kubectl is configured correctly",
                        "Check if you have permissions to create secrets in the cluster",
                        "Ensure the cluster is running: kubectl cluster-info",
                    ],
                )
        except subprocess.TimeoutExpired:
            raise CommandError(
                "kubectl apply command timed out",
                suggestions=[
                    "Check cluster connectivity",
                    "Verify kubectl is responding",
                ],
            )
        except FileNotFoundError:
            raise CommandError(
                "kubectl command not found",
                suggestions=[
                    "Install kubectl",
                    "Ensure kubectl is in your PATH",
                ],
            )

    def get_resource(
        self,
        resource_type: str,
        resource_name: str,
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a Kubernetes resource.

        Args:
            resource_type: Type of resource (e.g., "secret", "providerconfig")
            resource_name: Name of the resource
            namespace: Kubernetes namespace (optional)

        Returns:
            Resource data as dict

        Raises:
            CommandError: If resource doesn't exist or get fails
        """
        try:
            cmd = ["kubectl", "get", resource_type, resource_name, "-o", "json"]
            if namespace:
                cmd.extend(["-n", namespace])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                raise CommandError(
                    f"Resource {resource_type}/{resource_name} not found"
                )

            return json.loads(result.stdout)
        except json.JSONDecodeError:
            raise CommandError(f"Failed to parse resource data")
        except subprocess.TimeoutExpired:
            raise CommandError("kubectl get timed out")
        except FileNotFoundError:
            raise CommandError("kubectl not found")

    def create_secret(
        self,
        name: str,
        namespace: str,
        data: Dict[str, str],
        secret_type: str = "Opaque",
    ) -> None:
        """
        Create or update a Kubernetes secret.

        Args:
            name: Secret name
            namespace: Kubernetes namespace
            data: Secret data as key-value pairs
            secret_type: Secret type

        Raises:
            CommandError: If creation fails
        """
        yaml_content = f"""apiVersion: v1
kind: Secret
metadata:
  name: {name}
  namespace: {namespace}
type: {secret_type}
stringData:
"""
        for key, value in data.items():
            # Indent the value properly for YAML
            yaml_content += f"  {key}: |\n"
            for line in value.split("\n"):
                yaml_content += f"    {line}\n"

        self.apply_yaml(yaml_content)

    def apply_yaml(self, yaml_content: str) -> None:
        """
        Apply YAML content via kubectl.

        Args:
            yaml_content: YAML manifest content

        Raises:
            CommandError: If apply fails
        """
        try:
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=yaml_content,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise CommandError(
                    f"Failed to apply resource: {result.stderr}",
                    suggestions=[
                        "Check YAML syntax",
                        "Verify cluster connectivity: kubectl cluster-info",
                        "Check permissions",
                    ],
                )
        except subprocess.TimeoutExpired:
            raise CommandError(
                "kubectl apply timed out",
                suggestions=["Check cluster connectivity"],
            )
        except FileNotFoundError:
            raise CommandError(
                "kubectl not found",
                suggestions=["Install kubectl", "Add kubectl to PATH"],
            )

    def delete_resource(self, resource_type: str, name: str, namespace: str) -> None:
        """
        Delete a Kubernetes resource.

        Args:
            resource_type: Resource type (e.g., "secret", "provider")
            name: Resource name
            namespace: Kubernetes namespace

        Raises:
            CommandError: If deletion fails
        """
        try:
            cmd = ["kubectl", "delete", resource_type, name, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CommandError(
                    f"Failed to delete {resource_type}/{name}: {result.stderr}"
                )
        except subprocess.TimeoutExpired:
            raise CommandError(f"Timeout deleting {resource_type}/{name}")
        except FileNotFoundError:
            raise CommandError("kubectl not found")

    def resource_exists(self, resource_type: str, name: str, namespace: str) -> bool:
        """
        Check if a resource exists.

        Args:
            resource_type: Resource type
            name: Resource name
            namespace: Kubernetes namespace

        Returns:
            True if resource exists
        """
        try:
            cmd = ["kubectl", "get", resource_type, name, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def get_pods(self, namespace: str) -> List[Dict[str, Any]]:
        """
        Get pods in a namespace.

        Args:
            namespace: Kubernetes namespace

        Returns:
            List of pod information dicts
        """
        try:
            cmd = [
                "kubectl",
                "get",
                "pods",
                "-n",
                namespace,
                "-o",
                "json",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return []

            data = json.loads(result.stdout)
            pods = []
            for item in data.get("items", []):
                pod_info = {
                    "name": item["metadata"]["name"],
                    "ready": self._is_pod_ready(item),
                }
                pods.append(pod_info)
            return pods
        except Exception:
            return []

    def delete_namespace(self, namespace: str) -> None:
        """
        Delete a namespace.

        Args:
            namespace: Namespace to delete

        Raises:
            CommandError: If deletion fails
        """
        try:
            cmd = ["kubectl", "delete", "namespace", namespace, "--wait=false"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CommandError(
                    f"Failed to delete namespace {namespace}: {result.stderr}"
                )
        except subprocess.TimeoutExpired:
            raise CommandError(f"Timeout deleting namespace {namespace}")
        except FileNotFoundError:
            raise CommandError("kubectl not found")

    def _is_pod_ready(self, pod: Dict[str, Any]) -> bool:
        """Check if a pod is ready."""
        conditions = pod.get("status", {}).get("conditions", [])
        for condition in conditions:
            if condition.get("type") == "Ready":
                return condition.get("status") == "True"
        return False

    def _build_secret_yaml(
        self,
        credentials: AWSCredentials,
        namespace: str = "crossplane-system",
        secret_name: str = "aws-credentials",
    ) -> str:
        """
        Build Kubernetes secret YAML manifest.

        Args:
            credentials: AWS credentials
            namespace: Kubernetes namespace
            secret_name: Name of the secret

        Returns:
            YAML manifest as string
        """
        return f"""apiVersion: v1
kind: Secret
metadata:
  name: {secret_name}
  namespace: {namespace}
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: {credentials.access_key_id}
  AWS_SECRET_ACCESS_KEY: {credentials.secret_access_key}
  AWS_DEFAULT_REGION: {credentials.region}
"""
