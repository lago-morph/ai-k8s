"""Tests for KubectlClient integration layer."""

import json
import pytest
from unittest.mock import Mock, patch, call
from hypothesis import given, strategies as st

from mk8.integrations.kubectl_client import KubectlClient
from mk8.business.credential_models import AWSCredentials
from mk8.core.errors import CommandError


@pytest.fixture
def kubectl_client() -> KubectlClient:
    """Create KubectlClient instance."""
    return KubectlClient()


class TestKubectlClientClusterExists:
    """Tests for KubectlClient.cluster_exists()."""

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_cluster_exists_returns_true_when_cluster_active(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test cluster_exists returns True when cluster is active."""
        mock_run.return_value = Mock(returncode=0, stdout="kubernetes\n")

        result = kubectl_client.cluster_exists()

        assert result is True
        mock_run.assert_called_once()

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_cluster_exists_returns_false_when_no_cluster(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test cluster_exists returns False when no cluster configured."""
        mock_run.return_value = Mock(returncode=1, stderr="no context")

        result = kubectl_client.cluster_exists()

        assert result is False

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_cluster_exists_returns_false_on_error(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test cluster_exists returns False on kubectl error."""
        mock_run.side_effect = Exception("kubectl not found")

        result = kubectl_client.cluster_exists()

        assert result is False


class TestKubectlClientApplySecret:
    """Tests for KubectlClient.apply_secret()."""

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_apply_secret_creates_secret(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test apply_secret creates Kubernetes secret."""
        mock_run.return_value = Mock(
            returncode=0, stdout="secret/aws-credentials created"
        )

        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        kubectl_client.apply_secret(creds)

        mock_run.assert_called_once()
        # Check that kubectl apply was called
        call_args = mock_run.call_args[0][0]
        assert "kubectl" in call_args
        assert "apply" in call_args

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_apply_secret_uses_correct_namespace(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test apply_secret uses crossplane-system namespace."""
        mock_run.return_value = Mock(returncode=0)

        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        kubectl_client.apply_secret(creds, namespace="crossplane-system")

        # Check the YAML input contains the namespace
        yaml_input = mock_run.call_args[1]["input"]
        assert "namespace: crossplane-system" in yaml_input

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_apply_secret_raises_error_on_failure(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test apply_secret raises CommandError on kubectl failure."""
        mock_run.return_value = Mock(
            returncode=1, stderr="error: unable to create secret"
        )

        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        with pytest.raises(CommandError) as exc_info:
            kubectl_client.apply_secret(creds)

        assert "secret" in str(exc_info.value).lower()


class TestKubectlClientGetResource:
    """Tests for KubectlClient.get_resource()."""

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_get_resource_returns_dict_when_exists(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test get_resource returns dict when resource exists."""
        mock_data = {"kind": "ProviderConfig", "metadata": {"name": "default"}}
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps(mock_data))

        result = kubectl_client.get_resource("providerconfig", "default")

        assert result == mock_data

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_get_resource_raises_when_not_found(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test get_resource raises CommandError when resource not found."""
        mock_run.return_value = Mock(returncode=1, stderr="not found")

        with pytest.raises(CommandError, match="not found"):
            kubectl_client.get_resource("providerconfig", "default")

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_get_resource_uses_correct_namespace(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test get_resource uses specified namespace."""
        mock_data = {"kind": "Secret", "metadata": {"name": "aws-credentials"}}
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps(mock_data))

        kubectl_client.get_resource(
            "secret", "aws-credentials", namespace="crossplane-system"
        )

        call_args = mock_run.call_args[0][0]
        assert "-n" in call_args or "--namespace" in call_args


class TestKubectlClientBuildSecretYaml:
    """Tests for KubectlClient._build_secret_yaml()."""

    def test_build_secret_yaml_contains_all_credentials(
        self, kubectl_client: KubectlClient
    ) -> None:
        """Test _build_secret_yaml includes all three credentials."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        yaml_content = kubectl_client._build_secret_yaml(creds)

        assert "AWS_ACCESS_KEY_ID" in yaml_content
        assert "AWS_SECRET_ACCESS_KEY" in yaml_content
        assert "AWS_DEFAULT_REGION" in yaml_content
        assert "AKIAIOSFODNN7EXAMPLE" in yaml_content
        assert "secret" in yaml_content
        assert "us-east-1" in yaml_content

    def test_build_secret_yaml_has_correct_structure(
        self, kubectl_client: KubectlClient
    ) -> None:
        """Test _build_secret_yaml produces valid Kubernetes secret structure."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        yaml_content = kubectl_client._build_secret_yaml(creds)

        assert "apiVersion: v1" in yaml_content
        assert "kind: Secret" in yaml_content
        assert "metadata:" in yaml_content
        assert "name: aws-credentials" in yaml_content
        assert "type: Opaque" in yaml_content
        assert "stringData:" in yaml_content

    def test_build_secret_yaml_uses_correct_namespace(
        self, kubectl_client: KubectlClient
    ) -> None:
        """Test _build_secret_yaml uses specified namespace."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        yaml_content = kubectl_client._build_secret_yaml(
            creds, namespace="crossplane-system"
        )

        assert "namespace: crossplane-system" in yaml_content


class TestKubectlClientProperties:
    """Property-based tests for KubectlClient."""

    @given(
        access_key=st.text(min_size=1, max_size=50),
        secret_key=st.text(min_size=1, max_size=100),
        region=st.text(min_size=1, max_size=20),
    )
    def test_property_secret_yaml_always_contains_credentials(
        self, access_key: str, secret_key: str, region: str
    ) -> None:
        """Property: Secret YAML should always contain all credential fields."""
        kubectl_client = KubectlClient()
        creds = AWSCredentials(
            access_key_id=access_key,
            secret_access_key=secret_key,
            region=region,
        )

        yaml_content = kubectl_client._build_secret_yaml(creds)

        assert "AWS_ACCESS_KEY_ID" in yaml_content
        assert "AWS_SECRET_ACCESS_KEY" in yaml_content
        assert "AWS_DEFAULT_REGION" in yaml_content

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_property_cluster_exists_never_raises_exception(
        self, mock_run: Mock
    ) -> None:
        """Property: cluster_exists should never raise exceptions."""
        kubectl_client = KubectlClient()
        # Simulate various error conditions
        mock_run.side_effect = Exception("Any error")

        # Should return False, not raise
        result = kubectl_client.cluster_exists()
        assert result is False

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_property_apply_secret_raises_on_failure(self, mock_run: Mock) -> None:
        """Property: apply_secret should raise CommandError on kubectl failure."""
        kubectl_client = KubectlClient()
        mock_run.return_value = Mock(returncode=1, stderr="error")

        creds = AWSCredentials(
            access_key_id="key",
            secret_access_key="secret",
            region="us-east-1",
        )

        with pytest.raises(CommandError):
            kubectl_client.apply_secret(creds)
