"""Tests for CrossplaneManager business logic."""

import pytest
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st

from mk8.business.crossplane_manager import CrossplaneManager
from mk8.business.credential_models import AWSCredentials, ValidationResult, SyncResult
from mk8.core.errors import CommandError


@pytest.fixture
def mock_kubectl_client() -> Mock:
    """Create mock KubectlClient."""
    return Mock()


@pytest.fixture
def mock_aws_client() -> Mock:
    """Create mock AWSClient."""
    return Mock()


@pytest.fixture
def mock_output() -> Mock:
    """Create mock OutputFormatter."""
    return Mock()


@pytest.fixture
def crossplane_manager(
    mock_kubectl_client: Mock, mock_aws_client: Mock, mock_output: Mock
) -> CrossplaneManager:
    """Create CrossplaneManager with mocked dependencies."""
    return CrossplaneManager(mock_kubectl_client, mock_aws_client, mock_output)


class TestCrossplaneManagerSyncCredentials:
    """Tests for CrossplaneManager.sync_credentials()."""

    def test_sync_skips_when_no_cluster(
        self, crossplane_manager: CrossplaneManager, mock_kubectl_client: Mock
    ) -> None:
        """Test sync_credentials skips when no cluster exists."""
        mock_kubectl_client.cluster_exists.return_value = False

        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = crossplane_manager.sync_credentials(creds)

        assert result.success is True
        assert result.cluster_exists is False
        assert result.secret_updated is False
        mock_kubectl_client.apply_secret.assert_not_called()

    def test_sync_creates_secret_when_cluster_exists(
        self,
        crossplane_manager: CrossplaneManager,
        mock_kubectl_client: Mock,
        mock_aws_client: Mock,
    ) -> None:
        """Test sync_credentials creates secret when cluster exists."""
        mock_kubectl_client.cluster_exists.return_value = True
        mock_aws_client.validate_credentials.return_value = ValidationResult(
            success=True,
            account_id="123456789012",
        )

        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = crossplane_manager.sync_credentials(creds)

        assert result.success is True
        assert result.cluster_exists is True
        assert result.secret_updated is True
        mock_kubectl_client.apply_secret.assert_called_once_with(
            creds, "crossplane-system", "aws-credentials"
        )

    def test_sync_validates_credentials_after_update(
        self,
        crossplane_manager: CrossplaneManager,
        mock_kubectl_client: Mock,
        mock_aws_client: Mock,
    ) -> None:
        """Test sync_credentials validates credentials after updating secret."""
        mock_kubectl_client.cluster_exists.return_value = True
        mock_aws_client.validate_credentials.return_value = ValidationResult(
            success=True,
            account_id="123456789012",
        )

        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = crossplane_manager.sync_credentials(creds)

        assert result.validation_result is not None
        assert result.validation_result.success is True
        assert result.validation_result.account_id == "123456789012"
        mock_aws_client.validate_credentials.assert_called_once()

    def test_sync_handles_kubectl_failure(
        self, crossplane_manager: CrossplaneManager, mock_kubectl_client: Mock
    ) -> None:
        """Test sync_credentials handles kubectl failures gracefully."""
        mock_kubectl_client.cluster_exists.return_value = True
        mock_kubectl_client.apply_secret.side_effect = CommandError(
            "kubectl failed",
            suggestions=["Check cluster"],
        )

        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = crossplane_manager.sync_credentials(creds)

        assert result.success is False
        assert result.cluster_exists is True
        assert result.secret_updated is False
        assert result.error is not None
        assert "kubectl" in result.error.lower()

    def test_sync_reports_validation_failure(
        self,
        crossplane_manager: CrossplaneManager,
        mock_kubectl_client: Mock,
        mock_aws_client: Mock,
    ) -> None:
        """Test sync_credentials reports validation failures."""
        mock_kubectl_client.cluster_exists.return_value = True
        mock_aws_client.validate_credentials.return_value = ValidationResult(
            success=False,
            error_code="InvalidClientTokenId",
            error_message="Invalid token",
        )

        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = crossplane_manager.sync_credentials(creds)

        assert result.success is True  # Sync succeeded even though validation failed
        assert result.secret_updated is True
        assert result.validation_result is not None
        assert result.validation_result.success is False


class TestCrossplaneManagerClusterExists:
    """Tests for CrossplaneManager.cluster_exists()."""

    def test_cluster_exists_delegates_to_kubectl(
        self, crossplane_manager: CrossplaneManager, mock_kubectl_client: Mock
    ) -> None:
        """Test cluster_exists delegates to kubectl client."""
        mock_kubectl_client.cluster_exists.return_value = True

        result = crossplane_manager.cluster_exists()

        assert result is True
        mock_kubectl_client.cluster_exists.assert_called_once()

    def test_cluster_exists_returns_false_when_no_cluster(
        self, crossplane_manager: CrossplaneManager, mock_kubectl_client: Mock
    ) -> None:
        """Test cluster_exists returns False when no cluster."""
        mock_kubectl_client.cluster_exists.return_value = False

        result = crossplane_manager.cluster_exists()

        assert result is False


class TestCrossplaneManagerCreateOrUpdateSecret:
    """Tests for CrossplaneManager.create_or_update_secret()."""

    def test_create_or_update_secret_calls_kubectl(
        self, crossplane_manager: CrossplaneManager, mock_kubectl_client: Mock
    ) -> None:
        """Test create_or_update_secret calls kubectl client."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        crossplane_manager.create_or_update_secret(creds)

        mock_kubectl_client.apply_secret.assert_called_once_with(
            creds, "crossplane-system", "aws-credentials"
        )

    def test_create_or_update_secret_uses_custom_namespace(
        self, crossplane_manager: CrossplaneManager, mock_kubectl_client: Mock
    ) -> None:
        """Test create_or_update_secret uses custom namespace."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        crossplane_manager.create_or_update_secret(creds, namespace="custom-ns")

        mock_kubectl_client.apply_secret.assert_called_once_with(
            creds, "custom-ns", "aws-credentials"
        )


class TestCrossplaneManagerVerifyProviderConfig:
    """Tests for CrossplaneManager.verify_provider_config()."""

    def test_verify_provider_config_checks_for_default(
        self, crossplane_manager: CrossplaneManager, mock_kubectl_client: Mock
    ) -> None:
        """Test verify_provider_config checks for default ProviderConfig."""
        mock_kubectl_client.resource_exists.return_value = True

        result = crossplane_manager.verify_provider_config()

        assert result is True
        mock_kubectl_client.resource_exists.assert_called_once_with(
            "providerconfig", "default", "crossplane-system"
        )

    def test_verify_provider_config_returns_false_when_not_found(
        self, crossplane_manager: CrossplaneManager, mock_kubectl_client: Mock
    ) -> None:
        """Test verify_provider_config returns False when not found."""
        mock_kubectl_client.resource_exists.return_value = False

        result = crossplane_manager.verify_provider_config()

        assert result is False


class TestCrossplaneManagerProperties:
    """Property-based tests for CrossplaneManager."""

    def test_property_sync_result_always_has_cluster_status(
        self,
        crossplane_manager: CrossplaneManager,
        mock_kubectl_client: Mock,
        mock_aws_client: Mock,
    ) -> None:
        """Property: Sync result should always indicate cluster existence."""
        mock_kubectl_client.cluster_exists.return_value = True
        mock_aws_client.validate_credentials.return_value = ValidationResult(
            success=True,
            account_id="123456789012",
        )

        creds = AWSCredentials(
            access_key_id="key",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = crossplane_manager.sync_credentials(creds)

        assert isinstance(result.cluster_exists, bool)

    def test_property_secret_contains_all_credentials(
        self,
        crossplane_manager: CrossplaneManager,
        mock_kubectl_client: Mock,
        mock_aws_client: Mock,
    ) -> None:
        """Property: Secret should contain all three credential fields."""
        mock_kubectl_client.cluster_exists.return_value = True
        mock_aws_client.validate_credentials.return_value = ValidationResult(
            success=True,
            account_id="123456789012",
        )

        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        crossplane_manager.sync_credentials(creds)

        # Verify the credentials passed to kubectl contain all fields
        call_args = mock_kubectl_client.apply_secret.call_args[0][0]
        assert call_args.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert call_args.secret_access_key == "secret"
        assert call_args.region == "us-east-1"

    def test_property_sync_updates_secret_and_validates(
        self,
        crossplane_manager: CrossplaneManager,
        mock_kubectl_client: Mock,
        mock_aws_client: Mock,
    ) -> None:
        """Property: Sync should update secret and validate credentials."""
        mock_kubectl_client.cluster_exists.return_value = True
        mock_aws_client.validate_credentials.return_value = ValidationResult(
            success=True,
            account_id="123456789012",
        )

        creds = AWSCredentials(
            access_key_id="key",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = crossplane_manager.sync_credentials(creds)

        # Both operations should have been called
        mock_kubectl_client.apply_secret.assert_called_once()
        mock_aws_client.validate_credentials.assert_called_once()
        assert result.secret_updated is True
        assert result.validation_result is not None

    def test_property_failed_sync_includes_error_message(
        self, crossplane_manager: CrossplaneManager, mock_kubectl_client: Mock
    ) -> None:
        """Property: Failed sync should include error message."""
        mock_kubectl_client.cluster_exists.return_value = True
        mock_kubectl_client.apply_secret.side_effect = CommandError(
            "kubectl failed",
            suggestions=["Check cluster"],
        )

        creds = AWSCredentials(
            access_key_id="key",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = crossplane_manager.sync_credentials(creds)

        assert result.success is False
        assert result.error is not None
        assert len(result.error) > 0
