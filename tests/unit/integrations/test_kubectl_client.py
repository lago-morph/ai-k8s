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


class TestKubectlClientApplySecretErrors:
    """Tests for KubectlClient.apply_secret() error handling."""

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_apply_secret_timeout(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test apply_secret raises CommandError on timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("kubectl", 30)
        credentials = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )

        with pytest.raises(CommandError, match="timed out"):
            kubectl_client.apply_secret(credentials)

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_apply_secret_kubectl_not_found(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test apply_secret raises CommandError when kubectl not found."""
        mock_run.side_effect = FileNotFoundError()
        credentials = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )

        with pytest.raises(CommandError, match="kubectl command not found"):
            kubectl_client.apply_secret(credentials)


class TestKubectlClientCreateSecret:
    """Tests for KubectlClient.create_secret()."""

    @patch("mk8.integrations.kubectl_client.KubectlClient.apply_yaml")
    def test_create_secret_success(
        self, mock_apply: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test create_secret creates secret successfully."""
        kubectl_client.create_secret(
            name="test-secret",
            namespace="default",
            data={"key1": "value1", "key2": "value2"},
        )

        mock_apply.assert_called_once()
        yaml_content = mock_apply.call_args[0][0]
        assert "test-secret" in yaml_content
        assert "default" in yaml_content
        assert "key1" in yaml_content
        assert "key2" in yaml_content


class TestKubectlClientApplyYaml:
    """Tests for KubectlClient.apply_yaml()."""

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_apply_yaml_success(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test apply_yaml applies YAML successfully."""
        mock_run.return_value = Mock(returncode=0)
        yaml_content = "apiVersion: v1\nkind: Pod"

        kubectl_client.apply_yaml(yaml_content)

        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["kubectl", "apply", "-f", "-"]

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_apply_yaml_failure(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test apply_yaml raises CommandError on failure."""
        mock_run.return_value = Mock(returncode=1, stderr="invalid yaml")

        with pytest.raises(CommandError, match="Failed to apply resource"):
            kubectl_client.apply_yaml("invalid yaml")

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_apply_yaml_timeout(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test apply_yaml raises CommandError on timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("kubectl", 30)

        with pytest.raises(CommandError, match="timed out"):
            kubectl_client.apply_yaml("apiVersion: v1")

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_apply_yaml_kubectl_not_found(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test apply_yaml raises CommandError when kubectl not found."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(CommandError, match="kubectl not found"):
            kubectl_client.apply_yaml("apiVersion: v1")


class TestKubectlClientDeleteResource:
    """Tests for KubectlClient.delete_resource()."""

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_delete_resource_success(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test delete_resource deletes successfully."""
        mock_run.return_value = Mock(returncode=0)

        kubectl_client.delete_resource("secret", "test-secret", "default")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd == ["kubectl", "delete", "secret", "test-secret", "-n", "default"]

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_delete_resource_failure(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test delete_resource raises CommandError on failure."""
        mock_run.return_value = Mock(returncode=1, stderr="not found")

        with pytest.raises(CommandError, match="Failed to delete"):
            kubectl_client.delete_resource("secret", "test-secret", "default")

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_delete_resource_timeout(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test delete_resource raises CommandError on timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("kubectl", 30)

        with pytest.raises(CommandError, match="Timeout deleting"):
            kubectl_client.delete_resource("secret", "test-secret", "default")

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_delete_resource_kubectl_not_found(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test delete_resource raises CommandError when kubectl not found."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(CommandError, match="kubectl not found"):
            kubectl_client.delete_resource("secret", "test-secret", "default")


class TestKubectlClientResourceExists:
    """Tests for KubectlClient.resource_exists()."""

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_resource_exists_returns_true(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test resource_exists returns True when resource exists."""
        mock_run.return_value = Mock(returncode=0)

        result = kubectl_client.resource_exists("secret", "test-secret", "default")

        assert result is True

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_resource_exists_returns_false(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test resource_exists returns False when resource not found."""
        mock_run.return_value = Mock(returncode=1)

        result = kubectl_client.resource_exists("secret", "test-secret", "default")

        assert result is False

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_resource_exists_returns_false_on_exception(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test resource_exists returns False on exception."""
        mock_run.side_effect = Exception("error")

        result = kubectl_client.resource_exists("secret", "test-secret", "default")

        assert result is False


class TestKubectlClientGetPods:
    """Tests for KubectlClient.get_pods()."""

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_get_pods_success(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test get_pods returns pod information."""
        pod_data = {
            "items": [
                {
                    "metadata": {"name": "pod1"},
                    "status": {"conditions": [{"type": "Ready", "status": "True"}]},
                },
                {
                    "metadata": {"name": "pod2"},
                    "status": {"conditions": [{"type": "Ready", "status": "False"}]},
                },
            ]
        }
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps(pod_data))

        result = kubectl_client.get_pods("default")

        assert len(result) == 2
        assert result[0]["name"] == "pod1"
        assert result[0]["ready"] is True
        assert result[1]["name"] == "pod2"
        assert result[1]["ready"] is False

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_get_pods_returns_empty_on_error(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test get_pods returns empty list on error."""
        mock_run.return_value = Mock(returncode=1)

        result = kubectl_client.get_pods("default")

        assert result == []

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_get_pods_returns_empty_on_exception(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test get_pods returns empty list on exception."""
        mock_run.side_effect = Exception("error")

        result = kubectl_client.get_pods("default")

        assert result == []


class TestKubectlClientDeleteNamespace:
    """Tests for KubectlClient.delete_namespace()."""

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_delete_namespace_success(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test delete_namespace deletes successfully."""
        mock_run.return_value = Mock(returncode=0)

        kubectl_client.delete_namespace("test-namespace")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd == [
            "kubectl",
            "delete",
            "namespace",
            "test-namespace",
            "--wait=false",
        ]

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_delete_namespace_failure(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test delete_namespace raises CommandError on failure."""
        mock_run.return_value = Mock(returncode=1, stderr="not found")

        with pytest.raises(CommandError, match="Failed to delete namespace"):
            kubectl_client.delete_namespace("test-namespace")

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_delete_namespace_timeout(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test delete_namespace raises CommandError on timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("kubectl", 30)

        with pytest.raises(CommandError, match="Timeout deleting namespace"):
            kubectl_client.delete_namespace("test-namespace")

    @patch("mk8.integrations.kubectl_client.subprocess.run")
    def test_delete_namespace_kubectl_not_found(
        self, mock_run: Mock, kubectl_client: KubectlClient
    ) -> None:
        """Test delete_namespace raises CommandError when kubectl not found."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(CommandError, match="kubectl not found"):
            kubectl_client.delete_namespace("test-namespace")


class TestKubectlClientIsPodReady:
    """Tests for KubectlClient._is_pod_ready()."""

    def test_is_pod_ready_returns_true(self, kubectl_client: KubectlClient) -> None:
        """Test _is_pod_ready returns True when pod is ready."""
        pod = {"status": {"conditions": [{"type": "Ready", "status": "True"}]}}

        result = kubectl_client._is_pod_ready(pod)

        assert result is True

    def test_is_pod_ready_returns_false(self, kubectl_client: KubectlClient) -> None:
        """Test _is_pod_ready returns False when pod not ready."""
        pod = {"status": {"conditions": [{"type": "Ready", "status": "False"}]}}

        result = kubectl_client._is_pod_ready(pod)

        assert result is False

    def test_is_pod_ready_returns_false_no_conditions(
        self, kubectl_client: KubectlClient
    ) -> None:
        """Test _is_pod_ready returns False when no conditions."""
        pod = {"status": {}}

        result = kubectl_client._is_pod_ready(pod)

        assert result is False


class TestKubectlClientBuildSecretYamlAdvanced:
    """Tests for KubectlClient._build_secret_yaml() advanced scenarios."""

    def test_build_secret_yaml_creates_valid_yaml(
        self, kubectl_client: KubectlClient
    ) -> None:
        """Test _build_secret_yaml creates valid YAML."""
        credentials = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )

        yaml_content = kubectl_client._build_secret_yaml(credentials)

        assert "apiVersion: v1" in yaml_content
        assert "kind: Secret" in yaml_content
        assert "aws-credentials" in yaml_content
        assert "crossplane-system" in yaml_content
        assert "AKIATEST" in yaml_content
        assert "secret" in yaml_content
        assert "us-east-1" in yaml_content

    def test_build_secret_yaml_custom_namespace(
        self, kubectl_client: KubectlClient
    ) -> None:
        """Test _build_secret_yaml with custom namespace."""
        credentials = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-west-2",
        )

        yaml_content = kubectl_client._build_secret_yaml(
            credentials, namespace="custom-ns", secret_name="custom-secret"
        )

        assert "custom-ns" in yaml_content
        assert "custom-secret" in yaml_content
