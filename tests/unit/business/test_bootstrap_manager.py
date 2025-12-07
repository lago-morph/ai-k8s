"""Tests for BootstrapManager business logic."""

import pytest
from unittest.mock import Mock, patch
from mk8.business.bootstrap_manager import BootstrapManager, ClusterStatus
from mk8.integrations.kind_client import ClusterExistsError
from mk8.core.errors import MK8Error


@pytest.fixture
def mock_kind() -> Mock:
    """Create mock KindClient."""
    mock = Mock()
    mock.CLUSTER_NAME = "mk8-bootstrap"
    return mock


@pytest.fixture
def mock_kubeconfig() -> Mock:
    """Create mock KubeconfigManager."""
    return Mock()


@pytest.fixture
def mock_prereq() -> Mock:
    """Create mock PrerequisiteChecker."""
    mock = Mock()
    docker_result = Mock()
    docker_result.installed = True
    docker_result.daemon_running = True
    mock.check_docker.return_value = docker_result
    kind_result = Mock()
    kind_result.installed = True
    mock.check_kind.return_value = kind_result
    kubectl_result = Mock()
    kubectl_result.installed = True
    mock.check_kubectl.return_value = kubectl_result
    return mock


@pytest.fixture
def mock_output() -> Mock:
    """Create mock OutputFormatter."""
    mock = Mock()
    mock.verbose = False
    return mock


@pytest.fixture
def manager(
    mock_kind: Mock, mock_kubeconfig: Mock, mock_prereq: Mock, mock_output: Mock
) -> BootstrapManager:
    """Create BootstrapManager with mocked dependencies."""
    return BootstrapManager(
        kind_client=mock_kind,
        kubeconfig_manager=mock_kubeconfig,
        prerequisite_checker=mock_prereq,
        output=mock_output,
    )


class TestBootstrapManagerInit:
    """Tests for BootstrapManager initialization."""

    def test_init_with_dependencies(
        self,
        mock_kind: Mock,
        mock_kubeconfig: Mock,
        mock_prereq: Mock,
        mock_output: Mock,
    ) -> None:
        """Test initialization with provided dependencies."""
        manager = BootstrapManager(
            kind_client=mock_kind,
            kubeconfig_manager=mock_kubeconfig,
            prerequisite_checker=mock_prereq,
            output=mock_output,
        )
        assert manager.kind_client == mock_kind
        assert manager.kubeconfig_manager == mock_kubeconfig
        assert manager.prerequisite_checker == mock_prereq
        assert manager.output == mock_output

    def test_init_without_dependencies(self) -> None:
        """Test initialization creates default dependencies."""
        manager = BootstrapManager()
        assert manager.kind_client is not None
        assert manager.kubeconfig_manager is not None
        assert manager.prerequisite_checker is not None
        assert manager.output is not None


class TestBootstrapManagerCreateCluster:
    """Tests for BootstrapManager.create_cluster()."""

    @patch("yaml.safe_load")
    def test_create_cluster_success(
        self,
        mock_yaml_load: Mock,
        manager: BootstrapManager,
        mock_kind: Mock,
        mock_kubeconfig: Mock,
    ) -> None:
        """Test create_cluster creates cluster successfully."""
        mock_kind.cluster_exists.return_value = False
        mock_kind.get_kubeconfig.return_value = "kubeconfig yaml"
        mock_yaml_load.return_value = {
            "clusters": [
                {
                    "name": "kind-mk8-bootstrap",
                    "cluster": {"server": "https://127.0.0.1:6443"},
                }
            ]
        }
        manager.create_cluster()
        mock_kind.create_cluster.assert_called_once_with(kubernetes_version=None)
        mock_kind.wait_for_ready.assert_called_once_with(timeout=300)
        mock_kind.get_kubeconfig.assert_called_once()
        mock_kubeconfig.add_cluster.assert_called_once()

    def test_create_cluster_already_exists(
        self, manager: BootstrapManager, mock_kind: Mock
    ) -> None:
        """Test create_cluster raises when cluster exists."""
        mock_kind.cluster_exists.return_value = True
        with pytest.raises(ClusterExistsError):
            manager.create_cluster()

    @patch("yaml.safe_load")
    def test_create_cluster_force_recreate(
        self,
        mock_yaml_load: Mock,
        manager: BootstrapManager,
        mock_kind: Mock,
        mock_kubeconfig: Mock,
    ) -> None:
        """Test create_cluster with force_recreate deletes existing cluster."""
        # cluster_exists called: 1) initial check, 2) in delete_cluster, 3) after delete
        mock_kind.cluster_exists.side_effect = [True, True, False]
        mock_kubeconfig.cluster_exists.return_value = True
        mock_kind.get_kubeconfig.return_value = "kubeconfig yaml"
        mock_yaml_load.return_value = {
            "clusters": [
                {
                    "name": "kind-mk8-bootstrap",
                    "cluster": {"server": "https://127.0.0.1:6443"},
                }
            ]
        }
        manager.create_cluster(force_recreate=True)
        mock_kind.delete_cluster.assert_called_once()
        mock_kind.create_cluster.assert_called_once()

    @patch("yaml.safe_load")
    def test_create_cluster_with_version(
        self,
        mock_yaml_load: Mock,
        manager: BootstrapManager,
        mock_kind: Mock,
        mock_kubeconfig: Mock,
    ) -> None:
        """Test create_cluster with specific Kubernetes version."""
        mock_kind.cluster_exists.return_value = False
        mock_kind.get_kubeconfig.return_value = "kubeconfig yaml"
        mock_yaml_load.return_value = {
            "clusters": [
                {
                    "name": "kind-mk8-bootstrap",
                    "cluster": {"server": "https://127.0.0.1:6443"},
                }
            ]
        }
        manager.create_cluster(kubernetes_version="v1.28.0")
        mock_kind.create_cluster.assert_called_once_with(kubernetes_version="v1.28.0")

    def test_create_cluster_kubeconfig_error(
        self, manager: BootstrapManager, mock_kind: Mock, mock_kubeconfig: Mock
    ) -> None:
        """Test create_cluster handles kubeconfig errors gracefully."""
        mock_kind.cluster_exists.return_value = False
        mock_kind.get_kubeconfig.side_effect = RuntimeError("Failed")
        manager.create_cluster()
        mock_kind.create_cluster.assert_called_once()


class TestBootstrapManagerDeleteCluster:
    """Tests for BootstrapManager.delete_cluster()."""

    @patch("mk8.business.bootstrap_manager.click.confirm")
    def test_delete_cluster_with_confirmation(
        self,
        mock_confirm: Mock,
        manager: BootstrapManager,
        mock_kind: Mock,
        mock_kubeconfig: Mock,
    ) -> None:
        """Test delete_cluster with user confirmation."""
        mock_confirm.return_value = True
        mock_kind.cluster_exists.return_value = True
        mock_kubeconfig.cluster_exists.return_value = True
        manager.delete_cluster()
        mock_confirm.assert_called_once()
        mock_kind.delete_cluster.assert_called_once()
        mock_kubeconfig.remove_cluster.assert_called_once()

    @patch("mk8.business.bootstrap_manager.click.confirm")
    def test_delete_cluster_user_cancels(
        self, mock_confirm: Mock, manager: BootstrapManager, mock_kind: Mock
    ) -> None:
        """Test delete_cluster when user cancels."""
        mock_confirm.return_value = False
        mock_kind.cluster_exists.return_value = True
        manager.delete_cluster()
        mock_kind.delete_cluster.assert_not_called()

    def test_delete_cluster_skip_confirmation(
        self, manager: BootstrapManager, mock_kind: Mock, mock_kubeconfig: Mock
    ) -> None:
        """Test delete_cluster with skip_confirmation."""
        mock_kind.cluster_exists.return_value = True
        mock_kubeconfig.cluster_exists.return_value = True
        manager.delete_cluster(skip_confirmation=True)
        mock_kind.delete_cluster.assert_called_once()
        mock_kubeconfig.remove_cluster.assert_called_once()

    def test_delete_cluster_not_exists(
        self, manager: BootstrapManager, mock_kind: Mock
    ) -> None:
        """Test delete_cluster when cluster doesn't exist."""
        mock_kind.cluster_exists.return_value = False
        manager.delete_cluster(skip_confirmation=True)
        mock_kind.delete_cluster.assert_not_called()

    def test_delete_cluster_handles_errors(
        self, manager: BootstrapManager, mock_kind: Mock, mock_kubeconfig: Mock
    ) -> None:
        """Test delete_cluster handles errors gracefully."""
        mock_kind.cluster_exists.return_value = True
        mock_kind.delete_cluster.side_effect = RuntimeError("Failed")
        mock_kubeconfig.cluster_exists.return_value = True
        manager.delete_cluster(skip_confirmation=True)


class TestBootstrapManagerGetStatus:
    """Tests for BootstrapManager.get_status()."""

    def test_get_status_cluster_exists(
        self, manager: BootstrapManager, mock_kind: Mock
    ) -> None:
        """Test get_status when cluster exists."""
        mock_kind.cluster_exists.return_value = True
        mock_kind.get_cluster_info.return_value = {
            "name": "mk8-bootstrap",
            "context": "kind-mk8-bootstrap",
            "kubernetes_version": "v1.28.0",
            "node_count": 1,
            "nodes": [{"name": "node1", "status": "Ready"}],
        }
        status = manager.get_status()
        assert status.exists is True
        assert status.ready is True
        assert status.kubernetes_version == "v1.28.0"
        assert status.node_count == 1

    def test_get_status_cluster_not_exists(
        self, manager: BootstrapManager, mock_kind: Mock
    ) -> None:
        """Test get_status when cluster doesn't exist."""
        mock_kind.cluster_exists.return_value = False
        status = manager.get_status()
        assert status.exists is False
        assert status.ready is False

    def test_get_status_handles_error(
        self, manager: BootstrapManager, mock_kind: Mock
    ) -> None:
        """Test get_status handles errors gracefully."""
        mock_kind.cluster_exists.return_value = True
        mock_kind.get_cluster_info.side_effect = RuntimeError("Failed")
        status = manager.get_status()
        assert status.exists is True
        assert len(status.issues) > 0

    def test_get_status_nodes_not_ready(
        self, manager: BootstrapManager, mock_kind: Mock
    ) -> None:
        """Test get_status when nodes are not ready."""
        mock_kind.cluster_exists.return_value = True
        mock_kind.get_cluster_info.return_value = {
            "name": "mk8-bootstrap",
            "context": "kind-mk8-bootstrap",
            "kubernetes_version": "v1.28.0",
            "node_count": 2,
            "nodes": [
                {"name": "node1", "status": "Ready"},
                {"name": "node2", "status": "NotReady"},
            ],
        }
        status = manager.get_status()
        assert status.exists is True
        assert status.ready is False
        assert len(status.issues) > 0


class TestBootstrapManagerHelpers:
    """Tests for helper methods."""

    def test_cluster_exists(self, manager: BootstrapManager, mock_kind: Mock) -> None:
        """Test cluster_exists delegates to kind_client."""
        mock_kind.cluster_exists.return_value = True
        result = manager.cluster_exists()
        assert result is True
        mock_kind.cluster_exists.assert_called_once()

    def test_validate_prerequisites_success(
        self, manager: BootstrapManager, mock_prereq: Mock
    ) -> None:
        """Test _validate_prerequisites succeeds when all pass."""
        manager._validate_prerequisites()

    def test_validate_prerequisites_docker_not_installed(
        self, manager: BootstrapManager, mock_prereq: Mock
    ) -> None:
        """Test _validate_prerequisites raises when Docker not installed."""
        docker_result = Mock()
        docker_result.installed = False
        mock_prereq.check_docker.return_value = docker_result
        with pytest.raises(MK8Error, match="Docker is not installed"):
            manager._validate_prerequisites()

    def test_validate_prerequisites_docker_not_running(
        self, manager: BootstrapManager, mock_prereq: Mock
    ) -> None:
        """Test _validate_prerequisites raises when Docker not running."""
        docker_result = Mock()
        docker_result.installed = True
        docker_result.daemon_running = False
        mock_prereq.check_docker.return_value = docker_result
        with pytest.raises(MK8Error, match="Docker daemon is not running"):
            manager._validate_prerequisites()

    def test_validate_prerequisites_kind_not_installed(
        self, manager: BootstrapManager, mock_prereq: Mock
    ) -> None:
        """Test _validate_prerequisites raises when kind not installed."""
        kind_result = Mock()
        kind_result.installed = False
        mock_prereq.check_kind.return_value = kind_result
        with pytest.raises(MK8Error, match="kind is not installed"):
            manager._validate_prerequisites()

    def test_validate_prerequisites_kubectl_not_installed(
        self, manager: BootstrapManager, mock_prereq: Mock
    ) -> None:
        """Test _validate_prerequisites raises when kubectl not installed."""
        kubectl_result = Mock()
        kubectl_result.installed = False
        mock_prereq.check_kubectl.return_value = kubectl_result
        with pytest.raises(MK8Error, match="kubectl is not installed"):
            manager._validate_prerequisites()


class TestClusterStatus:
    """Tests for ClusterStatus dataclass."""

    def test_cluster_status_defaults(self) -> None:
        """Test ClusterStatus has correct defaults."""
        status = ClusterStatus(exists=False)
        assert status.exists is False
        assert status.ready is False
        assert status.node_count == 0
        assert status.issues == []

    def test_cluster_status_with_values(self) -> None:
        """Test ClusterStatus with custom values."""
        status = ClusterStatus(
            exists=True, ready=True, kubernetes_version="v1.28.0", node_count=1
        )
        assert status.exists is True
        assert status.ready is True
        assert status.kubernetes_version == "v1.28.0"
