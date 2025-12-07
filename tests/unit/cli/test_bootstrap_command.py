"""Tests for bootstrap CLI commands."""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from mk8.cli.commands.bootstrap import bootstrap, create, delete, status
from mk8.business.bootstrap_manager import ClusterStatus
from mk8.core.errors import MK8Error, ExitCode


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_manager() -> Mock:
    """Create mock BootstrapManager."""
    return Mock()


class TestBootstrapGroup:
    """Tests for bootstrap command group."""

    def test_bootstrap_no_subcommand_shows_help(self, runner: CliRunner) -> None:
        """Test bootstrap without subcommand shows help."""
        result = runner.invoke(bootstrap)
        assert result.exit_code == 0
        assert "Manage local bootstrap cluster" in result.output

    def test_bootstrap_with_subcommand(self, runner: CliRunner) -> None:
        """Test bootstrap with subcommand doesn't show help."""
        with patch("mk8.cli.commands.bootstrap.BootstrapManager"):
            result = runner.invoke(bootstrap, ["status"])
            assert (
                "Manage local bootstrap cluster" not in result.output
                or result.exit_code != 0
            )


class TestCreateCommand:
    """Tests for bootstrap create command."""

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_create_success(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test create command succeeds."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        result = runner.invoke(create)
        assert result.exit_code == ExitCode.SUCCESS.value
        mock_manager.create_cluster.assert_called_once_with(
            kubernetes_version=None, force_recreate=False
        )

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_create_with_version(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test create with Kubernetes version."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        result = runner.invoke(create, ["--kubernetes-version", "v1.28.0"])
        assert result.exit_code == ExitCode.SUCCESS.value
        mock_manager.create_cluster.assert_called_once_with(
            kubernetes_version="v1.28.0", force_recreate=False
        )

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_create_with_force_recreate(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test create with force recreate flag."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        result = runner.invoke(create, ["--force-recreate"])
        assert result.exit_code == ExitCode.SUCCESS.value
        mock_manager.create_cluster.assert_called_once_with(
            kubernetes_version=None, force_recreate=True
        )

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_create_with_verbose(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test create with verbose flag."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        result = runner.invoke(create, ["--verbose"])
        assert result.exit_code == ExitCode.SUCCESS.value

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_create_mk8_error(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test create handles MK8Error."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.create_cluster.side_effect = MK8Error(
            "Test error", suggestions=["Fix it"]
        )
        result = runner.invoke(create)
        assert result.exit_code == ExitCode.COMMAND_ERROR.value
        assert "Test error" in result.output
        assert "Fix it" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_create_keyboard_interrupt(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test create handles KeyboardInterrupt."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.create_cluster.side_effect = KeyboardInterrupt()
        result = runner.invoke(create)
        assert result.exit_code == ExitCode.KEYBOARD_INTERRUPT.value
        assert "cancelled" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_create_unexpected_error(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test create handles unexpected errors."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.create_cluster.side_effect = RuntimeError("Unexpected")
        result = runner.invoke(create)
        assert result.exit_code == ExitCode.GENERAL_ERROR.value
        assert "Unexpected error" in result.output


class TestDeleteCommand:
    """Tests for bootstrap delete command."""

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_delete_success(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test delete command succeeds."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        result = runner.invoke(delete, ["--yes"])
        assert result.exit_code == ExitCode.SUCCESS.value
        mock_manager.delete_cluster.assert_called_once_with(skip_confirmation=True)

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_delete_without_yes(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test delete without --yes flag."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        result = runner.invoke(delete)
        assert result.exit_code == ExitCode.SUCCESS.value
        mock_manager.delete_cluster.assert_called_once_with(skip_confirmation=False)

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_delete_with_verbose(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test delete with verbose flag."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        result = runner.invoke(delete, ["--yes", "--verbose"])
        assert result.exit_code == ExitCode.SUCCESS.value

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_delete_mk8_error(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test delete handles MK8Error."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.delete_cluster.side_effect = MK8Error(
            "Delete failed", suggestions=["Try again"]
        )
        result = runner.invoke(delete, ["--yes"])
        assert result.exit_code == ExitCode.COMMAND_ERROR.value
        assert "Delete failed" in result.output
        assert "Try again" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_delete_keyboard_interrupt(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test delete handles KeyboardInterrupt."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.delete_cluster.side_effect = KeyboardInterrupt()
        result = runner.invoke(delete, ["--yes"])
        assert result.exit_code == ExitCode.KEYBOARD_INTERRUPT.value
        assert "cancelled" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_delete_unexpected_error(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test delete handles unexpected errors."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.delete_cluster.side_effect = RuntimeError("Unexpected")
        result = runner.invoke(delete, ["--yes"])
        assert result.exit_code == ExitCode.GENERAL_ERROR.value
        assert "Unexpected error" in result.output


class TestStatusCommand:
    """Tests for bootstrap status command."""

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_status_cluster_not_found(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test status when cluster doesn't exist."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.get_status.return_value = ClusterStatus(exists=False)
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.SUCCESS.value
        assert "Not found" in result.output
        assert "mk8 bootstrap create" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_status_cluster_ready(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test status when cluster is ready."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.get_status.return_value = ClusterStatus(
            exists=True,
            ready=True,
            name="mk8-bootstrap",
            kubernetes_version="v1.28.0",
            context_name="kind-mk8-bootstrap",
            node_count=1,
            nodes=[{"name": "node1", "status": "Ready"}],
        )
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.SUCCESS.value
        assert "mk8-bootstrap" in result.output
        assert "Ready" in result.output
        assert "v1.28.0" in result.output
        assert "kind-mk8-bootstrap" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_status_cluster_not_ready(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test status when cluster is not ready."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.get_status.return_value = ClusterStatus(
            exists=True,
            ready=False,
            name="mk8-bootstrap",
            node_count=1,
            issues=["Node not ready"],
        )
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.SUCCESS.value
        assert "Not Ready" in result.output
        assert "Node not ready" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_status_with_verbose(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test status with verbose flag shows node details."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.get_status.return_value = ClusterStatus(
            exists=True,
            ready=True,
            name="mk8-bootstrap",
            node_count=2,
            nodes=[
                {"name": "node1", "status": "Ready"},
                {"name": "node2", "status": "Ready"},
            ],
        )
        result = runner.invoke(status, ["--verbose"])
        assert result.exit_code == ExitCode.SUCCESS.value
        assert "node1" in result.output
        assert "node2" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_status_mk8_error(self, mock_mgr_class: Mock, runner: CliRunner) -> None:
        """Test status handles MK8Error."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.get_status.side_effect = MK8Error("Status failed")
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.COMMAND_ERROR.value
        assert "Status failed" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_status_keyboard_interrupt(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test status handles KeyboardInterrupt."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.get_status.side_effect = KeyboardInterrupt()
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.KEYBOARD_INTERRUPT.value
        assert "cancelled" in result.output

    @patch("mk8.cli.commands.bootstrap.BootstrapManager")
    def test_status_unexpected_error(
        self, mock_mgr_class: Mock, runner: CliRunner
    ) -> None:
        """Test status handles unexpected errors."""
        mock_manager = Mock()
        mock_mgr_class.return_value = mock_manager
        mock_manager.get_status.side_effect = RuntimeError("Unexpected")
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.GENERAL_ERROR.value
        assert "Unexpected error" in result.output
