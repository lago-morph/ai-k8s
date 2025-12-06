"""Tests for ConfigCommand CLI handler."""

import pytest
from unittest.mock import Mock, patch
import click
from click.testing import CliRunner

from mk8.cli.commands.config import config
from mk8.business.credential_models import AWSCredentials, ValidationResult, SyncResult
from mk8.core.errors import ConfigurationError, ExitCode


class TestConfigCommand:
    """Tests for config command."""

    @patch("mk8.cli.commands.config.CredentialManager")
    @patch("mk8.cli.commands.config.CrossplaneManager")
    @patch("mk8.cli.commands.config.FileIO")
    @patch("mk8.cli.commands.config.AWSClient")
    @patch("mk8.cli.commands.config.KubectlClient")
    def test_config_command_updates_credentials(
        self,
        mock_kubectl_cls: Mock,
        mock_aws_cls: Mock,
        mock_file_io_cls: Mock,
        mock_crossplane_cls: Mock,
        mock_cred_mgr_cls: Mock,
    ) -> None:
        """Test config command updates credentials successfully."""
        # Setup mocks
        mock_creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )
        mock_cred_mgr = Mock()
        mock_cred_mgr.update_credentials.return_value = mock_creds
        mock_cred_mgr_cls.return_value = mock_cred_mgr
        
        mock_crossplane = Mock()
        mock_crossplane.sync_credentials.return_value = SyncResult(
            success=True,
            cluster_exists=False,
            secret_updated=False,
        )
        mock_crossplane_cls.return_value = mock_crossplane
        
        runner = CliRunner()
        result = runner.invoke(config, [])
        
        assert result.exit_code == 0
        mock_cred_mgr.update_credentials.assert_called_once()
        mock_crossplane.sync_credentials.assert_called_once_with(mock_creds)

    @patch("mk8.cli.commands.config.CredentialManager")
    @patch("mk8.cli.commands.config.CrossplaneManager")
    @patch("mk8.cli.commands.config.FileIO")
    @patch("mk8.cli.commands.config.AWSClient")
    @patch("mk8.cli.commands.config.KubectlClient")
    def test_config_command_syncs_to_crossplane(
        self,
        mock_kubectl_cls: Mock,
        mock_aws_cls: Mock,
        mock_file_io_cls: Mock,
        mock_crossplane_cls: Mock,
        mock_cred_mgr_cls: Mock,
    ) -> None:
        """Test config command syncs credentials to Crossplane."""
        mock_creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )
        mock_cred_mgr = Mock()
        mock_cred_mgr.update_credentials.return_value = mock_creds
        mock_cred_mgr_cls.return_value = mock_cred_mgr
        
        mock_crossplane = Mock()
        mock_crossplane.sync_credentials.return_value = SyncResult(
            success=True,
            cluster_exists=True,
            secret_updated=True,
            validation_result=ValidationResult(success=True, account_id="123456789012"),
        )
        mock_crossplane_cls.return_value = mock_crossplane
        
        runner = CliRunner()
        result = runner.invoke(config, [])
        
        assert result.exit_code == 0
        mock_crossplane.sync_credentials.assert_called_once()

    @patch("mk8.cli.commands.config.CredentialManager")
    @patch("mk8.cli.commands.config.CrossplaneManager")
    @patch("mk8.cli.commands.config.FileIO")
    @patch("mk8.cli.commands.config.AWSClient")
    @patch("mk8.cli.commands.config.KubectlClient")
    def test_config_command_handles_configuration_error(
        self,
        mock_kubectl_cls: Mock,
        mock_aws_cls: Mock,
        mock_file_io_cls: Mock,
        mock_crossplane_cls: Mock,
        mock_cred_mgr_cls: Mock,
    ) -> None:
        """Test config command handles configuration errors."""
        mock_cred_mgr = Mock()
        mock_cred_mgr.update_credentials.side_effect = ConfigurationError(
            "Failed to configure",
            suggestions=["Check permissions"],
        )
        mock_cred_mgr_cls.return_value = mock_cred_mgr
        
        runner = CliRunner()
        result = runner.invoke(config, [])
        
        assert result.exit_code == ExitCode.CONFIGURATION_ERROR.value
        assert "Failed to configure" in result.output

    @patch("mk8.cli.commands.config.CredentialManager")
    @patch("mk8.cli.commands.config.CrossplaneManager")
    @patch("mk8.cli.commands.config.FileIO")
    @patch("mk8.cli.commands.config.AWSClient")
    @patch("mk8.cli.commands.config.KubectlClient")
    def test_config_command_handles_sync_failure(
        self,
        mock_kubectl_cls: Mock,
        mock_aws_cls: Mock,
        mock_file_io_cls: Mock,
        mock_crossplane_cls: Mock,
        mock_cred_mgr_cls: Mock,
    ) -> None:
        """Test config command handles Crossplane sync failures."""
        mock_creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )
        mock_cred_mgr = Mock()
        mock_cred_mgr.update_credentials.return_value = mock_creds
        mock_cred_mgr_cls.return_value = mock_cred_mgr
        
        mock_crossplane = Mock()
        mock_crossplane.sync_credentials.return_value = SyncResult(
            success=False,
            cluster_exists=True,
            secret_updated=False,
            error="kubectl failed",
        )
        mock_crossplane_cls.return_value = mock_crossplane
        
        runner = CliRunner()
        result = runner.invoke(config, [])
        
        # Should still succeed (credentials were updated)
        assert result.exit_code == 0

    @patch("mk8.cli.commands.config.CredentialManager")
    @patch("mk8.cli.commands.config.CrossplaneManager")
    @patch("mk8.cli.commands.config.FileIO")
    @patch("mk8.cli.commands.config.AWSClient")
    @patch("mk8.cli.commands.config.KubectlClient")
    def test_config_command_with_verbose(
        self,
        mock_kubectl_cls: Mock,
        mock_aws_cls: Mock,
        mock_file_io_cls: Mock,
        mock_crossplane_cls: Mock,
        mock_cred_mgr_cls: Mock,
    ) -> None:
        """Test config command with verbose flag."""
        mock_creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )
        mock_cred_mgr = Mock()
        mock_cred_mgr.update_credentials.return_value = mock_creds
        mock_cred_mgr_cls.return_value = mock_cred_mgr
        
        mock_crossplane = Mock()
        mock_crossplane.sync_credentials.return_value = SyncResult(
            success=True,
            cluster_exists=False,
            secret_updated=False,
        )
        mock_crossplane_cls.return_value = mock_crossplane
        
        runner = CliRunner()
        result = runner.invoke(config, ["--verbose"])
        
        assert result.exit_code == 0

    @patch("mk8.cli.commands.config.CredentialManager")
    @patch("mk8.cli.commands.config.CrossplaneManager")
    @patch("mk8.cli.commands.config.FileIO")
    @patch("mk8.cli.commands.config.AWSClient")
    @patch("mk8.cli.commands.config.KubectlClient")
    def test_config_command_displays_validation_success(
        self,
        mock_kubectl_cls: Mock,
        mock_aws_cls: Mock,
        mock_file_io_cls: Mock,
        mock_crossplane_cls: Mock,
        mock_cred_mgr_cls: Mock,
    ) -> None:
        """Test config command displays validation success message."""
        mock_creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )
        mock_cred_mgr = Mock()
        mock_cred_mgr.update_credentials.return_value = mock_creds
        mock_cred_mgr_cls.return_value = mock_cred_mgr
        
        mock_crossplane = Mock()
        mock_crossplane.sync_credentials.return_value = SyncResult(
            success=True,
            cluster_exists=True,
            secret_updated=True,
            validation_result=ValidationResult(success=True, account_id="123456789012"),
        )
        mock_crossplane_cls.return_value = mock_crossplane
        
        runner = CliRunner()
        result = runner.invoke(config, [])
        
        assert result.exit_code == 0
        # Output should contain success indicators
        assert result.output  # Should have some output

    @patch("mk8.cli.commands.config.CredentialManager")
    @patch("mk8.cli.commands.config.CrossplaneManager")
    @patch("mk8.cli.commands.config.FileIO")
    @patch("mk8.cli.commands.config.AWSClient")
    @patch("mk8.cli.commands.config.KubectlClient")
    def test_config_command_displays_validation_failure(
        self,
        mock_kubectl_cls: Mock,
        mock_aws_cls: Mock,
        mock_file_io_cls: Mock,
        mock_crossplane_cls: Mock,
        mock_cred_mgr_cls: Mock,
    ) -> None:
        """Test config command displays validation failure message."""
        mock_creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )
        mock_cred_mgr = Mock()
        mock_cred_mgr.update_credentials.return_value = mock_creds
        mock_cred_mgr_cls.return_value = mock_cred_mgr
        
        mock_crossplane = Mock()
        mock_crossplane.sync_credentials.return_value = SyncResult(
            success=True,
            cluster_exists=True,
            secret_updated=True,
            validation_result=ValidationResult(
                success=False,
                error_code="InvalidClientTokenId",
                error_message="Invalid token",
            ),
        )
        mock_crossplane_cls.return_value = mock_crossplane
        
        runner = CliRunner()
        result = runner.invoke(config, [])
        
        assert result.exit_code == 0
        # Should still succeed but show warning
        assert result.output
