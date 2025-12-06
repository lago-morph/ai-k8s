"""Kubectl client for Kubernetes operations."""

import subprocess
from typing import Optional

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
    ) -> bool:
        """
        Check if a Kubernetes resource exists.

        Args:
            resource_type: Type of resource (e.g., "secret", "providerconfig")
            resource_name: Name of the resource
            namespace: Kubernetes namespace (optional)

        Returns:
            True if resource exists, False otherwise
        """
        try:
            cmd = ["kubectl", "get", resource_type, resource_name]
            if namespace:
                cmd.extend(["-n", namespace])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            return result.returncode == 0
        except Exception:
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
