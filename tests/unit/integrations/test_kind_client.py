"""Tests for KindClient integration layer."""

import pytest
import subprocess
from unittest.mock import Mock, patch, mock_open
from mk8.integrations.kind_client import (
    KindClient,
    KindError,
    ClusterExistsError,
    ClusterNotFoundError,
)


@pytest.fixture
def kind_client() -> KindClient:
    """Create KindClient instance."""
    return KindClient()


class TestKindClientInit:
    """Tests for KindClient initialization."""

    def test_init_creates_client(self) -> None:
        """Test KindClient initializes successfully."""
        client = KindClient()
        assert client.CLUSTER_NAME == "mk8-bootstrap"


class TestKindClientRunCommand:
    """Tests for KindClient._run_kind_command()."""

    @patch("mk8.integrations.kind_client.subprocess.run")
    def test_run_kind_command_success(
        self, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test _run_kind_command returns stdout on success."""
        mock_run.return_value = Mock(returncode=0, stdout="success output")

        result = kind_client._run_kind_command(["version"])

        assert result == "success output"
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["kind", "version"]

    @patch("mk8.integrations.kind_client.subprocess.run")
    def test_run_kind_command_failure(
        self, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test _run_kind_command raises KindError on failure."""
        mock_run.return_value = Mock(returncode=1, stderr="error message")

        with pytest.raises(KindError, match="kind command failed"):
            kind_client._run_kind_command(["create"])

    @patch("mk8.integrations.kind_client.subprocess.run")
    def test_run_kind_command_timeout(
        self, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test _run_kind_command raises KindError on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("kind", 300)

        with pytest.raises(KindError, match="timed out"):
            kind_client._run_kind_command(["create"])

    @patch("mk8.integrations.kind_client.subprocess.run")
    def test_run_kind_command_not_found(
        self, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test _run_kind_command raises KindError when kind not found."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(KindError, match="kind command not found"):
            kind_client._run_kind_command(["version"])


class TestKindClientParseError:
    """Tests for KindClient._parse_kind_error()."""

    def test_parse_error_already_exists(self, kind_client: KindClient) -> None:
        """Test _parse_kind_error suggests deletion for existing cluster."""
        stderr = "Error: cluster already exists"

        suggestions = kind_client._parse_kind_error(stderr)

        assert any("delete" in s.lower() for s in suggestions)

    def test_parse_error_port_conflict(self, kind_client: KindClient) -> None:
        """Test _parse_kind_error suggests port conflict resolution."""
        stderr = "Error: port 80 already in use"

        suggestions = kind_client._parse_kind_error(stderr)

        assert any("port" in s.lower() for s in suggestions)

    def test_parse_error_docker_issue(self, kind_client: KindClient) -> None:
        """Test _parse_kind_error suggests Docker checks."""
        stderr = "Error: docker daemon not running"

        suggestions = kind_client._parse_kind_error(stderr)

        assert any("docker" in s.lower() for s in suggestions)

    def test_parse_error_generic(self, kind_client: KindClient) -> None:
        """Test _parse_kind_error provides generic suggestions."""
        stderr = "Error: unknown error"

        suggestions = kind_client._parse_kind_error(stderr)

        assert len(suggestions) > 0


class TestKindClientClusterExists:
    """Tests for KindClient.cluster_exists()."""

    @patch("mk8.integrations.kind_client.subprocess.run")
    def test_cluster_exists_returns_true(
        self, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test cluster_exists returns True when cluster exists."""
        mock_run.return_value = Mock(
            returncode=0, stdout="mk8-bootstrap\nother-cluster"
        )

        result = kind_client.cluster_exists()

        assert result is True

    @patch("mk8.integrations.kind_client.subprocess.run")
    def test_cluster_exists_returns_false(
        self, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test cluster_exists returns False when cluster doesn't exist."""
        mock_run.return_value = Mock(returncode=0, stdout="other-cluster")

        result = kind_client.cluster_exists()

        assert result is False

    @patch("mk8.integrations.kind_client.subprocess.run")
    def test_cluster_exists_returns_false_on_error(
        self, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test cluster_exists returns False on error."""
        mock_run.return_value = Mock(returncode=1, stderr="error")

        result = kind_client.cluster_exists()

        assert result is False


class TestKindClientCreateCluster:
    """Tests for KindClient.create_cluster()."""

    @patch("os.unlink")
    @patch("mk8.integrations.kind_client.subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_create_cluster_basic(
        self,
        mock_exists: Mock,
        mock_tempfile: Mock,
        mock_run: Mock,
        mock_unlink: Mock,
        kind_client: KindClient,
    ) -> None:
        """Test create_cluster creates cluster successfully."""
        mock_exists.return_value = False
        mock_temp = Mock()
        mock_temp.name = "/tmp/config.yaml"
        mock_temp.__enter__ = Mock(return_value=mock_temp)
        mock_temp.__exit__ = Mock(return_value=False)
        mock_tempfile.return_value = mock_temp
        mock_run.return_value = Mock(returncode=0, stdout="")

        kind_client.create_cluster()

        call_args = mock_run.call_args[0][0]
        assert "create" in call_args
        assert "cluster" in call_args
        assert "--name" in call_args
        assert "mk8-bootstrap" in call_args

    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_create_cluster_raises_when_exists(
        self, mock_exists: Mock, kind_client: KindClient
    ) -> None:
        """Test create_cluster raises ClusterExistsError when cluster exists."""
        mock_exists.return_value = True

        with pytest.raises(ClusterExistsError, match="already exists"):
            kind_client.create_cluster()

    @patch("os.unlink")
    @patch("mk8.integrations.kind_client.subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_create_cluster_with_version(
        self,
        mock_exists: Mock,
        mock_tempfile: Mock,
        mock_run: Mock,
        mock_unlink: Mock,
        kind_client: KindClient,
    ) -> None:
        """Test create_cluster with specific Kubernetes version."""
        mock_exists.return_value = False
        mock_temp = Mock()
        mock_temp.name = "/tmp/config.yaml"
        mock_temp.__enter__ = Mock(return_value=mock_temp)
        mock_temp.__exit__ = Mock(return_value=False)
        mock_tempfile.return_value = mock_temp
        mock_run.return_value = Mock(returncode=0, stdout="")

        kind_client.create_cluster(kubernetes_version="v1.28.0")

        call_args = mock_run.call_args[0][0]
        assert "--image" in call_args
        assert "kindest/node:v1.28.0" in call_args

    @patch("os.unlink")
    @patch("mk8.integrations.kind_client.subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_create_cluster_with_custom_config(
        self,
        mock_exists: Mock,
        mock_tempfile: Mock,
        mock_run: Mock,
        mock_unlink: Mock,
        kind_client: KindClient,
    ) -> None:
        """Test create_cluster with custom configuration."""
        mock_exists.return_value = False
        mock_temp = Mock()
        mock_temp.name = "/tmp/config.yaml"
        mock_temp.__enter__ = Mock(return_value=mock_temp)
        mock_temp.__exit__ = Mock(return_value=False)
        mock_tempfile.return_value = mock_temp
        mock_run.return_value = Mock(returncode=0, stdout="")

        custom_config = {"kind": "Cluster", "nodes": [{"role": "control-plane"}]}
        kind_client.create_cluster(config=custom_config)

        call_args = mock_run.call_args[0][0]
        assert "--config" in call_args


class TestKindClientValidateVersion:
    """Tests for KindClient._validate_kubernetes_version()."""

    def test_validate_version_valid(self, kind_client: KindClient) -> None:
        """Test _validate_kubernetes_version accepts valid version."""
        # Should not raise
        kind_client._validate_kubernetes_version("v1.28.0")

    def test_validate_version_missing_v_prefix(self, kind_client: KindClient) -> None:
        """Test _validate_kubernetes_version rejects version without v prefix."""
        with pytest.raises(KindError, match="Invalid Kubernetes version"):
            kind_client._validate_kubernetes_version("1.28.0")

    def test_validate_version_invalid_format(self, kind_client: KindClient) -> None:
        """Test _validate_kubernetes_version rejects invalid format."""
        with pytest.raises(KindError, match="Invalid Kubernetes version format"):
            kind_client._validate_kubernetes_version("v1")


class TestKindClientGetDefaultConfig:
    """Tests for KindClient._get_default_config()."""

    def test_get_default_config_returns_dict(self, kind_client: KindClient) -> None:
        """Test _get_default_config returns valid configuration."""
        config = kind_client._get_default_config()

        assert config["kind"] == "Cluster"
        assert "nodes" in config
        assert len(config["nodes"]) > 0


class TestKindClientDeleteCluster:
    """Tests for KindClient.delete_cluster()."""

    @patch("mk8.integrations.kind_client.subprocess.run")
    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_delete_cluster_success(
        self, mock_exists: Mock, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test delete_cluster deletes cluster successfully."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0, stdout="")

        kind_client.delete_cluster()

        call_args = mock_run.call_args[0][0]
        assert "delete" in call_args
        assert "cluster" in call_args

    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_delete_cluster_raises_when_not_exists(
        self, mock_exists: Mock, kind_client: KindClient
    ) -> None:
        """Test delete_cluster raises when cluster doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(ClusterNotFoundError, match="does not exist"):
            kind_client.delete_cluster()


class TestKindClientGetClusterInfo:
    """Tests for KindClient.get_cluster_info()."""

    @patch("mk8.integrations.kind_client.subprocess.run")
    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_get_cluster_info_success(
        self, mock_exists: Mock, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test get_cluster_info returns cluster information."""
        mock_exists.return_value = True
        stdout_data = (
            '{"items": [{"metadata": {"name": "mk8-bootstrap-control-plane"}, '
            '"status": {"conditions": [{"type": "Ready", "status": "True"}], '
            '"nodeInfo": {"kubeletVersion": "v1.28.0"}}}]}'
        )
        mock_run.return_value = Mock(returncode=0, stdout=stdout_data)

        info = kind_client.get_cluster_info()

        assert info["name"] == "mk8-bootstrap"
        assert info["kubernetes_version"] == "v1.28.0"
        assert info["node_count"] == 1

    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_get_cluster_info_raises_when_not_exists(
        self, mock_exists: Mock, kind_client: KindClient
    ) -> None:
        """Test get_cluster_info raises when cluster doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(ClusterNotFoundError, match="does not exist"):
            kind_client.get_cluster_info()

    @patch("mk8.integrations.kind_client.subprocess.run")
    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_get_cluster_info_kubectl_not_found(
        self, mock_exists: Mock, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test get_cluster_info raises KindError when kubectl not found."""
        mock_exists.return_value = True
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(KindError, match="kubectl command not found"):
            kind_client.get_cluster_info()

    @patch("mk8.integrations.kind_client.subprocess.run")
    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_get_cluster_info_kubectl_failure(
        self, mock_exists: Mock, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test get_cluster_info raises KindError when kubectl fails."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=1, stderr="error")

        with pytest.raises(KindError, match="Failed to get cluster info"):
            kind_client.get_cluster_info()


class TestKindClientWaitForReady:
    """Tests for KindClient.wait_for_ready()."""

    @patch("mk8.integrations.kind_client.time.sleep")
    @patch("mk8.integrations.kind_client.subprocess.run")
    def test_wait_for_ready_success(
        self, mock_run: Mock, mock_sleep: Mock, kind_client: KindClient
    ) -> None:
        """Test wait_for_ready returns when cluster is ready."""
        mock_run.return_value = Mock(returncode=0, stdout="Ready")

        kind_client.wait_for_ready(timeout=10)

        mock_run.assert_called()

    @patch("mk8.integrations.kind_client.time.time")
    @patch("mk8.integrations.kind_client.time.sleep")
    @patch("mk8.integrations.kind_client.subprocess.run")
    def test_wait_for_ready_timeout(
        self,
        mock_run: Mock,
        mock_sleep: Mock,
        mock_time: Mock,
        kind_client: KindClient,
    ) -> None:
        """Test wait_for_ready raises KindError on timeout."""
        mock_time.side_effect = [0, 400]  # Simulate timeout
        mock_run.return_value = Mock(returncode=1, stdout="NotReady")

        with pytest.raises(KindError, match="did not become ready"):
            kind_client.wait_for_ready(timeout=300)


class TestKindClientGetKubeconfig:
    """Tests for KindClient.get_kubeconfig()."""

    @patch("mk8.integrations.kind_client.subprocess.run")
    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_get_kubeconfig_success(
        self, mock_exists: Mock, mock_run: Mock, kind_client: KindClient
    ) -> None:
        """Test get_kubeconfig returns kubeconfig."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0, stdout="kubeconfig content")

        result = kind_client.get_kubeconfig()

        assert result == "kubeconfig content"

    @patch("mk8.integrations.kind_client.KindClient.cluster_exists")
    def test_get_kubeconfig_raises_when_not_exists(
        self, mock_exists: Mock, kind_client: KindClient
    ) -> None:
        """Test get_kubeconfig raises when cluster doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(ClusterNotFoundError, match="does not exist"):
            kind_client.get_kubeconfig()
