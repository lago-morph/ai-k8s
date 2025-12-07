"""Crossplane manager for credential synchronization."""

from mk8.business.credential_models import AWSCredentials, SyncResult
from mk8.integrations.kubectl_client import KubectlClient
from mk8.integrations.aws_client import AWSClient
from mk8.cli.output import OutputFormatter
from mk8.core.errors import CommandError


class CrossplaneManager:
    """Manages Crossplane credential synchronization."""

    def __init__(
        self,
        kubectl_client: KubectlClient,
        aws_client: AWSClient,
        output: OutputFormatter,
    ):
        """
        Initialize Crossplane manager with dependencies.

        Args:
            kubectl_client: KubectlClient instance for Kubernetes operations
            aws_client: AWSClient instance for credential validation
            output: OutputFormatter instance for user feedback
        """
        self.kubectl_client = kubectl_client
        self.aws_client = aws_client
        self.output = output

    def sync_credentials(
        self,
        credentials: AWSCredentials,
        namespace: str = "crossplane-system",
        secret_name: str = "aws-credentials",
    ) -> SyncResult:
        """
        Synchronize credentials to Crossplane.

        Args:
            credentials: AWS credentials to sync
            namespace: Kubernetes namespace for the secret
            secret_name: Name of the secret

        Returns:
            SyncResult with success status
        """
        # Check if cluster exists
        if not self.cluster_exists():
            self.output.info("No Kubernetes cluster detected, skipping Crossplane sync")
            return SyncResult(
                success=True,
                cluster_exists=False,
                secret_updated=False,
            )

        # Update secret
        try:
            self.create_or_update_secret(credentials, namespace, secret_name)
            self.output.info(
                f"Updated Crossplane credentials in {namespace}/{secret_name}"
            )
        except CommandError as e:
            self.output.error(f"Failed to update Crossplane credentials: {e}")
            return SyncResult(
                success=False,
                cluster_exists=True,
                secret_updated=False,
                error=str(e),
            )

        # Validate credentials
        validation_result = self.aws_client.validate_credentials(
            credentials.access_key_id,
            credentials.secret_access_key,
            credentials.region,
        )

        if validation_result.success:
            self.output.success(
                f"Credentials validated successfully "
                f"(Account: {validation_result.account_id})"
            )
        else:
            self.output.warning(
                f"Credential validation failed: {validation_result.error_message}"
            )
            suggestions = validation_result.get_suggestions()
            for suggestion in suggestions:
                self.output.info(f"  • {suggestion}")

        return SyncResult(
            success=True,
            cluster_exists=True,
            secret_updated=True,
            validation_result=validation_result,
        )

    def cluster_exists(self) -> bool:
        """
        Check if a Crossplane-enabled cluster exists.

        Returns:
            True if cluster exists and is accessible, False otherwise
        """
        return self.kubectl_client.cluster_exists()

    def create_or_update_secret(
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
            CommandError: If kubectl operations fail
        """
        self.kubectl_client.apply_secret(credentials, namespace, secret_name)

    def verify_provider_config(self, name: str = "default") -> bool:
        """
        Verify ProviderConfig references the credentials secret.

        Args:
            name: Name of the ProviderConfig to check

        Returns:
            True if ProviderConfig exists, False otherwise
        """
        return self.kubectl_client.resource_exists(
            "providerconfig", name, "crossplane-system"
        )
