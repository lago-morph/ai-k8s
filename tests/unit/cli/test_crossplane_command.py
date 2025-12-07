"""Tests for crossplane CLI commands."""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from mk8.cli.commands.crossplane import crossplane, install, uninstall, status
from mk8.business.crossplane_installer import CrossplaneStatus
from mk8.business.credential_models import AWSCredentials, ValidationResult
from mk8.core.errors import MK8Error, ExitCode


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_credentials() -> AWSCredentials:
    """Create mock AWS credentials."""
    return AWSCredentials(
        access_key_id="AKIATEST",
        secret_access_key="secret",
        region="us-east-1",
    )


class TestCrossplaneGroup:
    """Tests for crossplane command group."""

    def test_crossplane_no_subcommand_shows_help(self, runner: CliRunner) -> None:
        """Test crossplane without subcommand shows help."""
        result = runner.invoke(crossplane)
        assert result.exit_code == 0
        assert "Manage Crossplane on bootstrap cluster" in result.output


class TestInstallCommand:
    """Tests for crossplane install command."""

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    @patch("mk8.cli.commands.crossplane.CredentialManager")
    def test_install_success(
        self,
        mock_cred_mgr_class: Mock,
        mock_installer_class: Mock,
        runner: CliRunner,
        mock_credentials: AWSCredentials,
    ) -> None:
        """Test install command succeeds."""
        mock_cred_mgr = Mock()
        mock_cred_mgr_class.return_value = mock_cred_mgr
        mock_cred_mgr.get_credentials.return_value = mock_credentials
        mock_cred_mgr.validate_credentials.return_value = ValidationResult(
            success=True, account_id="123456789012"
        )
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        result = runner.invoke(install)
        assert result.exit_code == ExitCode.SUCCESS.value
        mock_installer.install_crossplane.assert_called_once_with(version=None)
        mock_installer.install_aws_provider.assert_called_once()
        mock_installer.configure_aws_provider.assert_called_once_with(mock_credentials)

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    @patch("mk8.cli.commands.crossplane.CredentialManager")
    def test_install_with_version(
        self,
        mock_cred_mgr_class: Mock,
        mock_installer_class: Mock,
        runner: CliRunner,
        mock_credentials: AWSCredentials,
    ) -> None:
        """Test install with specific version."""
        mock_cred_mgr = Mock()
        mock_cred_mgr_class.return_value = mock_cred_mgr
        mock_cred_mgr.get_credentials.return_value = mock_credentials
        mock_cred_mgr.validate_credentials.return_value = ValidationResult(
            success=True, account_id="123456789012"
        )
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        result = runner.invoke(install, ["--version", "1.14.0"])
        assert result.exit_code == ExitCode.SUCCESS.value
        mock_installer.install_crossplane.assert_called_once_with(version="1.14.0")

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    @patch("mk8.cli.commands.crossplane.CredentialManager")
    def test_install_credential_validation_fails(
        self,
        mock_cred_mgr_class: Mock,
        mock_installer_class: Mock,
        runner: CliRunner,
        mock_credentials: AWSCredentials,
    ) -> None:
        """Test install fails when credential validation fails."""
        mock_cred_mgr = Mock()
        mock_cred_mgr_class.return_value = mock_cred_mgr
        mock_cred_mgr.get_credentials.return_value = mock_credentials
        mock_cred_mgr.validate_credentials.return_value = ValidationResult(
            success=False,
            error_code="InvalidClientTokenId",
            error_message="Invalid credentials",
        )
        result = runner.invoke(install)
        assert result.exit_code == ExitCode.COMMAND_ERROR.value
        assert "validation failed" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    @patch("mk8.cli.commands.crossplane.CredentialManager")
    def test_install_mk8_error(
        self,
        mock_cred_mgr_class: Mock,
        mock_installer_class: Mock,
        runner: CliRunner,
        mock_credentials: AWSCredentials,
    ) -> None:
        """Test install handles MK8Error."""
        mock_cred_mgr = Mock()
        mock_cred_mgr_class.return_value = mock_cred_mgr
        mock_cred_mgr.get_credentials.return_value = mock_credentials
        mock_cred_mgr.validate_credentials.return_value = ValidationResult(
            success=True, account_id="123456789012"
        )
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.install_crossplane.side_effect = MK8Error(
            "Install failed", suggestions=["Try again"]
        )
        result = runner.invoke(install)
        assert result.exit_code == ExitCode.COMMAND_ERROR.value
        assert "Install failed" in result.output
        assert "Try again" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    @patch("mk8.cli.commands.crossplane.CredentialManager")
    def test_install_keyboard_interrupt(
        self,
        mock_cred_mgr_class: Mock,
        mock_installer_class: Mock,
        runner: CliRunner,
        mock_credentials: AWSCredentials,
    ) -> None:
        """Test install handles KeyboardInterrupt."""
        mock_cred_mgr = Mock()
        mock_cred_mgr_class.return_value = mock_cred_mgr
        mock_cred_mgr.get_credentials.side_effect = KeyboardInterrupt()
        result = runner.invoke(install)
        assert result.exit_code == ExitCode.KEYBOARD_INTERRUPT.value
        assert "cancelled" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    @patch("mk8.cli.commands.crossplane.CredentialManager")
    def test_install_unexpected_error(
        self,
        mock_cred_mgr_class: Mock,
        mock_installer_class: Mock,
        runner: CliRunner,
        mock_credentials: AWSCredentials,
    ) -> None:
        """Test install handles unexpected errors."""
        mock_cred_mgr = Mock()
        mock_cred_mgr_class.return_value = mock_cred_mgr
        mock_cred_mgr.get_credentials.side_effect = RuntimeError("Unexpected")
        result = runner.invoke(install)
        assert result.exit_code == ExitCode.GENERAL_ERROR.value
        assert "Unexpected error" in result.output


class TestUninstallCommand:
    """Tests for crossplane uninstall command."""

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_uninstall_success(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test uninstall command succeeds."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        result = runner.invoke(uninstall, ["--yes"])
        assert result.exit_code == ExitCode.SUCCESS.value
        mock_installer.uninstall_crossplane.assert_called_once()

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    @patch("mk8.cli.commands.crossplane.click.confirm")
    def test_uninstall_with_confirmation(
        self, mock_confirm: Mock, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test uninstall with user confirmation."""
        mock_confirm.return_value = True
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        result = runner.invoke(uninstall)
        assert result.exit_code == ExitCode.SUCCESS.value
        mock_confirm.assert_called_once()
        mock_installer.uninstall_crossplane.assert_called_once()

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    @patch("mk8.cli.commands.crossplane.click.confirm")
    def test_uninstall_user_cancels(
        self, mock_confirm: Mock, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test uninstall when user cancels."""
        mock_confirm.return_value = False
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        result = runner.invoke(uninstall)
        assert result.exit_code == ExitCode.SUCCESS.value
        assert "cancelled" in result.output
        mock_installer.uninstall_crossplane.assert_not_called()

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_uninstall_mk8_error(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test uninstall handles MK8Error."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.uninstall_crossplane.side_effect = MK8Error("Uninstall failed")
        result = runner.invoke(uninstall, ["--yes"])
        assert result.exit_code == ExitCode.COMMAND_ERROR.value
        assert "Uninstall failed" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_uninstall_keyboard_interrupt(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test uninstall handles KeyboardInterrupt."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.uninstall_crossplane.side_effect = KeyboardInterrupt()
        result = runner.invoke(uninstall, ["--yes"])
        assert result.exit_code == ExitCode.KEYBOARD_INTERRUPT.value
        assert "cancelled" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_uninstall_unexpected_error(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test uninstall handles unexpected errors."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.uninstall_crossplane.side_effect = RuntimeError("Unexpected")
        result = runner.invoke(uninstall, ["--yes"])
        assert result.exit_code == ExitCode.GENERAL_ERROR.value
        assert "Unexpected error" in result.output


class TestStatusCommand:
    """Tests for crossplane status command."""

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_status_not_installed(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test status when Crossplane not installed."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.get_status.return_value = CrossplaneStatus(installed=False)
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.SUCCESS.value
        assert "Not installed" in result.output
        assert "mk8 crossplane install" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_status_installed_ready(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test status when Crossplane is installed and ready."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.get_status.return_value = CrossplaneStatus(
            installed=True,
            ready=True,
            version="1.14.0",
            namespace="crossplane-system",
            pod_count=3,
            ready_pods=3,
            aws_provider_installed=True,
            aws_provider_ready=True,
            provider_config_exists=True,
        )
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.SUCCESS.value
        assert "Installed" in result.output
        assert "1.14.0" in result.output
        assert "Ready" in result.output
        assert "3/3 ready" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_status_installed_not_ready(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test status when Crossplane is installed but not ready."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.get_status.return_value = CrossplaneStatus(
            installed=True,
            ready=False,
            namespace="crossplane-system",
            pod_count=3,
            ready_pods=1,
            aws_provider_installed=False,
            provider_config_exists=False,
            issues=["Pods not ready", "Provider not installed"],
        )
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.SUCCESS.value
        assert "Not Ready" in result.output
        assert "1/3 ready" in result.output
        assert "Pods not ready" in result.output
        assert "Provider not installed" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_status_mk8_error(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test status handles MK8Error."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.get_status.side_effect = MK8Error("Status failed")
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.COMMAND_ERROR.value
        assert "Status failed" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_status_keyboard_interrupt(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test status handles KeyboardInterrupt."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.get_status.side_effect = KeyboardInterrupt()
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.KEYBOARD_INTERRUPT.value
        assert "cancelled" in result.output

    @patch("mk8.cli.commands.crossplane.CrossplaneInstaller")
    def test_status_unexpected_error(
        self, mock_installer_class: Mock, runner: CliRunner
    ) -> None:
        """Test status handles unexpected errors."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.get_status.side_effect = RuntimeError("Unexpected")
        result = runner.invoke(status)
        assert result.exit_code == ExitCode.GENERAL_ERROR.value
        assert "Unexpected error" in result.output
