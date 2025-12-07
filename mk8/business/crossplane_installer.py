"""Crossplane installer for bootstrap cluster."""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from mk8.integrations.helm_client import HelmClient, HelmError
from mk8.integrations.kubectl_client import KubectlClient
from mk8.business.credential_manager import CredentialManager
from mk8.business.credential_models import AWSCredentials
from mk8.cli.output import OutputFormatter
from mk8.core.errors import CommandError


@dataclass
class CrossplaneStatus:
    """Status of Crossplane installation."""

    installed: bool = False
    version: Optional[str] = None
    namespace: str = "crossplane-system"
    release_name: str = "crossplane"
    ready: bool = False
    pod_count: int = 0
    ready_pods: int = 0
    aws_provider_installed: bool = False
    aws_provider_ready: bool = False
    provider_config_exists: bool = False
    issues: List[str] = field(default_factory=list)


class CrossplaneInstaller:
    """Manages Crossplane installation and configuration."""

    CROSSPLANE_REPO_NAME = "crossplane-stable"
    CROSSPLANE_REPO_URL = "https://charts.crossplane.io/stable"
    CROSSPLANE_NAMESPACE = "crossplane-system"
    CROSSPLANE_RELEASE = "crossplane"
    AWS_PROVIDER_NAME = "provider-aws"
    AWS_SECRET_NAME = "aws-credentials"
    PROVIDER_CONFIG_NAME = "default"

    def __init__(
        self,
        helm_client: Optional[HelmClient] = None,
        kubectl_client: Optional[KubectlClient] = None,
        credential_manager: Optional[CredentialManager] = None,
        output: Optional[OutputFormatter] = None,
    ):
        """
        Initialize Crossplane installer.

        Args:
            helm_client: HelmClient instance
            kubectl_client: KubectlClient instance
            credential_manager: CredentialManager instance
            output: OutputFormatter instance
        """
        self.helm = helm_client or HelmClient()
        self.kubectl = kubectl_client or KubectlClient()
        self.credential_manager = credential_manager or CredentialManager()
        self.output = output or OutputFormatter(verbose=False)

    def install_crossplane(
        self, version: Optional[str] = None, timeout: int = 600
    ) -> None:
        """
        Install Crossplane via Helm.

        Args:
            version: Crossplane version (e.g., "1.14.0")
            timeout: Installation timeout in seconds

        Raises:
            CommandError: If installation fails
        """
        self.output.info("Installing Crossplane...")

        try:
            # Add Crossplane repository
            self.output.verbose("Adding Crossplane Helm repository...")
            self.helm.add_repository(
                self.CROSSPLANE_REPO_NAME, self.CROSSPLANE_REPO_URL, force=True
            )

            # Update repositories
            self.output.verbose("Updating Helm repositories...")
            self.helm.update_repositories()

            # Prepare chart name
            chart = f"{self.CROSSPLANE_REPO_NAME}/crossplane"
            if version:
                chart = f"{chart} --version {version}"

            # Get Helm values
            values = self._get_crossplane_values()

            # Install chart
            self.output.info(f"Installing Crossplane chart (timeout: {timeout}s)...")
            self.helm.install_chart(
                release_name=self.CROSSPLANE_RELEASE,
                chart=chart,
                namespace=self.CROSSPLANE_NAMESPACE,
                values=values,
                create_namespace=True,
                wait=True,
                timeout=timeout,
            )

            # Wait for pods to be ready
            self.output.info("Waiting for Crossplane pods to be ready...")
            self._wait_for_crossplane_ready(timeout=120)

            self.output.success("Crossplane installed successfully")

        except HelmError as e:
            raise CommandError(
                f"Failed to install Crossplane: {e}",
                suggestions=e.suggestions if hasattr(e, "suggestions") else [],
            )
        except Exception as e:
            raise CommandError(
                f"Failed to install Crossplane: {e}",
                suggestions=[
                    "Check cluster is running: mk8 bootstrap status",
                    "Check Helm is installed: helm version",
                    "Try with verbose mode: --verbose",
                ],
            )

    def install_aws_provider(self, timeout: int = 300) -> None:
        """
        Install AWS provider.

        Args:
            timeout: Installation timeout in seconds

        Raises:
            CommandError: If installation fails
        """
        self.output.info("Installing AWS provider...")

        try:
            # Create Provider resource
            provider_yaml = self._get_aws_provider_yaml()
            self.output.verbose("Creating Provider resource...")
            self._apply_yaml_resource(provider_yaml)

            # Wait for provider to be ready
            self.output.info("Waiting for AWS provider to be ready...")
            self._wait_for_provider_ready(timeout=timeout)

            self.output.success("AWS provider installed successfully")

        except Exception as e:
            raise CommandError(
                f"Failed to install AWS provider: {e}",
                suggestions=[
                    "Check Crossplane is installed: mk8 crossplane status",
                    "Check provider logs: kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=provider-aws",
                    "Try with verbose mode: --verbose",
                ],
            )

    def configure_aws_provider(
        self, credentials: Optional[AWSCredentials] = None
    ) -> None:
        """
        Configure AWS provider with credentials.

        Args:
            credentials: AWS credentials (retrieved if not provided)

        Raises:
            CommandError: If configuration fails
        """
        self.output.info("Configuring AWS provider...")

        try:
            # Get credentials if not provided
            if not credentials:
                self.output.verbose("Retrieving AWS credentials...")
                credentials = self.credential_manager.get_credentials()

            # Create AWS secret
            self.output.verbose("Creating AWS credentials secret...")
            self._create_aws_secret(credentials)

            # Create ProviderConfig
            self.output.verbose("Creating ProviderConfig...")
            provider_config_yaml = self._get_provider_config_yaml()
            self._apply_yaml_resource(provider_config_yaml)

            # Wait for ProviderConfig to be ready
            self.output.info("Waiting for ProviderConfig to be ready...")
            self._wait_for_provider_config_ready(timeout=60)

            self.output.success("AWS provider configured successfully")

        except Exception as e:
            raise CommandError(
                f"Failed to configure AWS provider: {e}",
                suggestions=[
                    "Check AWS credentials: mk8 config validate",
                    "Check provider is ready: mk8 crossplane status",
                    "Try with verbose mode: --verbose",
                ],
            )

    def uninstall_crossplane(self) -> None:
        """
        Uninstall Crossplane and cleanup resources.

        Performs resilient cleanup, continuing even if individual steps fail.
        """
        self.output.info("Uninstalling Crossplane...")
        errors = []

        # Delete ProviderConfig
        try:
            self.output.verbose("Deleting ProviderConfig...")
            self._delete_resource(
                "providerconfig.aws.upbound.io",
                self.PROVIDER_CONFIG_NAME,
                self.CROSSPLANE_NAMESPACE,
            )
        except Exception as e:
            errors.append(f"ProviderConfig deletion: {e}")
            self.output.warning(f"Failed to delete ProviderConfig: {e}")

        # Delete Provider
        try:
            self.output.verbose("Deleting Provider...")
            self._delete_resource(
                "provider.pkg.crossplane.io",
                self.AWS_PROVIDER_NAME,
                self.CROSSPLANE_NAMESPACE,
            )
        except Exception as e:
            errors.append(f"Provider deletion: {e}")
            self.output.warning(f"Failed to delete Provider: {e}")

        # Uninstall Helm release
        try:
            self.output.verbose("Uninstalling Helm release...")
            self.helm.uninstall_release(
                self.CROSSPLANE_RELEASE, self.CROSSPLANE_NAMESPACE, wait=True
            )
        except Exception as e:
            errors.append(f"Helm uninstall: {e}")
            self.output.warning(f"Failed to uninstall Helm release: {e}")

        # Delete namespace
        try:
            self.output.verbose("Deleting namespace...")
            self.kubectl.delete_namespace(self.CROSSPLANE_NAMESPACE)
        except Exception as e:
            errors.append(f"Namespace deletion: {e}")
            self.output.warning(f"Failed to delete namespace: {e}")

        if errors:
            self.output.warning(f"Uninstallation completed with {len(errors)} error(s)")
        else:
            self.output.success("Crossplane uninstalled successfully")

    def get_status(self) -> CrossplaneStatus:
        """
        Get Crossplane installation status.

        Returns:
            CrossplaneStatus object
        """
        status = CrossplaneStatus()

        try:
            # Check Helm release
            if self.helm.release_exists(
                self.CROSSPLANE_RELEASE, self.CROSSPLANE_NAMESPACE
            ):
                status.installed = True
                release_status = self.helm.get_release_status(
                    self.CROSSPLANE_RELEASE, self.CROSSPLANE_NAMESPACE
                )
                status.version = release_status.get("version")

            # Check pods
            pods = self._get_pods_in_namespace(self.CROSSPLANE_NAMESPACE)
            status.pod_count = len(pods)
            status.ready_pods = sum(1 for p in pods if p.get("ready"))
            status.ready = (
                status.pod_count > 0 and status.pod_count == status.ready_pods
            )

            # Check AWS provider
            status.aws_provider_installed = self._resource_exists(
                "provider.pkg.crossplane.io",
                self.AWS_PROVIDER_NAME,
                self.CROSSPLANE_NAMESPACE,
            )

            if status.aws_provider_installed:
                provider_status = self._get_resource_status(
                    "provider.pkg.crossplane.io",
                    self.AWS_PROVIDER_NAME,
                    self.CROSSPLANE_NAMESPACE,
                )
                status.aws_provider_ready = (
                    provider_status.get("status", {})
                    .get("conditions", [{}])[0]
                    .get("status")
                    == "True"
                )

            # Check ProviderConfig
            status.provider_config_exists = self._resource_exists(
                "providerconfig.aws.upbound.io",
                self.PROVIDER_CONFIG_NAME,
                self.CROSSPLANE_NAMESPACE,
            )

            # Detect issues
            if status.installed and not status.ready:
                status.issues.append("Crossplane pods are not ready")
            if status.aws_provider_installed and not status.aws_provider_ready:
                status.issues.append("AWS provider is not ready")
            if not status.provider_config_exists and status.aws_provider_installed:
                status.issues.append("ProviderConfig not found")

        except Exception as e:
            status.issues.append(f"Failed to get status: {e}")

        return status

    # Helper methods

    def _get_crossplane_values(self) -> Dict[str, Any]:
        """Get Helm values for Crossplane installation."""
        return {
            "args": ["--enable-composition-revisions"],
            "resourcesCrossplane": {
                "limits": {"cpu": "1", "memory": "2Gi"},
                "requests": {"cpu": "100m", "memory": "256Mi"},
            },
        }

    def _get_aws_provider_yaml(self) -> str:
        """Get Provider YAML for AWS provider."""
        return f"""apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: {self.AWS_PROVIDER_NAME}
spec:
  package: xpkg.upbound.io/upbound/provider-aws:v0.40.0
"""

    def _get_provider_config_yaml(self) -> str:
        """Get ProviderConfig YAML."""
        return f"""apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: {self.PROVIDER_CONFIG_NAME}
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: {self.CROSSPLANE_NAMESPACE}
      name: {self.AWS_SECRET_NAME}
      key: credentials
"""

    def _create_aws_secret(self, credentials: AWSCredentials) -> None:
        """Create Kubernetes secret with AWS credentials."""
        credentials_content = f"""[default]
aws_access_key_id = {credentials.access_key_id}
aws_secret_access_key = {credentials.secret_access_key}
"""
        if credentials.session_token:
            credentials_content += f"aws_session_token = {credentials.session_token}\n"

        self.kubectl.create_secret(
            name=self.AWS_SECRET_NAME,
            namespace=self.CROSSPLANE_NAMESPACE,
            data={"credentials": credentials_content},
            secret_type="Opaque",
        )

    def _apply_yaml_resource(self, yaml_content: str) -> None:
        """Apply YAML resource via kubectl."""
        self.kubectl.apply_yaml(yaml_content)

    def _delete_resource(self, resource_type: str, name: str, namespace: str) -> None:
        """Delete a Kubernetes resource."""
        self.kubectl.delete_resource(resource_type, name, namespace)

    def _resource_exists(self, resource_type: str, name: str, namespace: str) -> bool:
        """Check if a resource exists."""
        return self.kubectl.resource_exists(resource_type, name, namespace)

    def _get_resource_status(
        self, resource_type: str, name: str, namespace: str
    ) -> Dict[str, Any]:
        """Get resource status."""
        return self.kubectl.get_resource(resource_type, name, namespace)

    def _get_pods_in_namespace(self, namespace: str) -> List[Dict[str, Any]]:
        """Get pods in namespace."""
        return self.kubectl.get_pods(namespace)

    def _wait_for_crossplane_ready(self, timeout: int = 120) -> None:
        """Wait for Crossplane pods to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            pods = self._get_pods_in_namespace(self.CROSSPLANE_NAMESPACE)
            if pods and all(p.get("ready") for p in pods):
                return
            time.sleep(5)
        raise CommandError("Timeout waiting for Crossplane pods to be ready")

    def _wait_for_provider_ready(self, timeout: int = 300) -> None:
        """Wait for AWS provider to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._resource_exists(
                "provider.pkg.crossplane.io",
                self.AWS_PROVIDER_NAME,
                self.CROSSPLANE_NAMESPACE,
            ):
                status = self._get_resource_status(
                    "provider.pkg.crossplane.io",
                    self.AWS_PROVIDER_NAME,
                    self.CROSSPLANE_NAMESPACE,
                )
                conditions = status.get("status", {}).get("conditions", [])
                if conditions and conditions[0].get("status") == "True":
                    return
            time.sleep(10)
        raise CommandError("Timeout waiting for AWS provider to be ready")

    def _wait_for_provider_config_ready(self, timeout: int = 60) -> None:
        """Wait for ProviderConfig to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._resource_exists(
                "providerconfig.aws.upbound.io",
                self.PROVIDER_CONFIG_NAME,
                self.CROSSPLANE_NAMESPACE,
            ):
                return
            time.sleep(5)
        raise CommandError("Timeout waiting for ProviderConfig to be ready")
