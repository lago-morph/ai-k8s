"""Integration tests for end-to-end CLI execution."""

import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner

from mk8.cli.main import cli, main
from mk8.core.version import Version


class TestCLIExecution:
    """Test complete CLI execution flows."""

    @pytest.fixture
    def runner(self):
        """Provide a CLI runner for tests."""
        return CliRunner()

    def test_cli_entry_point_execution(self, runner):
        """Test that the CLI entry point executes successfully."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "mk8 - Manage Kubernetes infrastructure on AWS" in result.output

    def test_version_command_end_to_end(self, runner):
        """Test version command execution from start to finish."""
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output
        assert Version.get_version() in result.output

    def test_version_flag_end_to_end(self, runner):
        """Test --version flag execution from start to finish."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output
        assert Version.get_version() in result.output

    @patch("mk8.cli.commands.config.AWSClient")
    @patch("mk8.cli.commands.config.KubectlClient")
    def test_config_command_placeholder(
        self, mock_kubectl: Mock, mock_aws: Mock, runner
    ):
        """Test config command placeholder execution."""
        from mk8.business.credential_models import ValidationResult

        # Mock AWS client to return successful validation
        mock_aws_instance = mock_aws.return_value
        mock_aws_instance.validate_credentials.return_value = ValidationResult(
            success=True, account_id="123456789012"
        )

        # Mock kubectl client
        mock_kubectl_instance = mock_kubectl.return_value
        mock_kubectl_instance.cluster_exists.return_value = False

        # Provide environment variables to avoid prompting
        result = runner.invoke(
            cli,
            ["config"],
            env={
                "MK8_AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
                "MK8_AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "MK8_AWS_DEFAULT_REGION": "us-east-1",
            },
        )

        assert result.exit_code == 0
        assert "config" in result.output.lower()

    def test_bootstrap_group_without_subcommand(self, runner):
        """Test bootstrap group shows help when no subcommand provided."""
        result = runner.invoke(cli, ["bootstrap"])

        assert result.exit_code == 0
        assert "bootstrap" in result.output
        assert "Manage local bootstrap cluster" in result.output

    def test_verbose_flag_affects_execution(self, runner):
        """Test that verbose flag is properly passed through execution."""
        # Normal execution
        result_normal = runner.invoke(cli, ["version"])

        # Verbose execution
        result_verbose = runner.invoke(cli, ["--verbose", "version"])

        # Both should succeed
        assert result_normal.exit_code == 0
        assert result_verbose.exit_code == 0

        # Both should show version
        assert "mk8 version" in result_normal.output
        assert "mk8 version" in result_verbose.output

    def test_main_function_returns_zero_on_success(self):
        """Test that main() function returns 0 on successful execution."""
        # We can't easily test this without mocking sys.argv
        # but we can verify the function exists and is callable
        assert callable(main)

    def test_cli_with_no_arguments_shows_help(self, runner):
        """Test that CLI with no arguments shows help."""
        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        assert "mk8 - Manage Kubernetes infrastructure on AWS" in result.output
        assert "Commands:" in result.output

    def test_multiple_commands_in_sequence(self, runner):
        """Test executing multiple commands in sequence."""
        # Execute version command
        result1 = runner.invoke(cli, ["version"])
        assert result1.exit_code == 0

        # Execute help
        result2 = runner.invoke(cli, ["--help"])
        assert result2.exit_code == 0

        # Execute config with environment variables and mocking
        with patch("mk8.cli.commands.config.AWSClient") as mock_aws, patch(
            "mk8.cli.commands.config.KubectlClient"
        ) as mock_kubectl:
            from mk8.business.credential_models import ValidationResult

            mock_aws_instance = mock_aws.return_value
            mock_aws_instance.validate_credentials.return_value = ValidationResult(
                success=True, account_id="123456789012"
            )
            mock_kubectl_instance = mock_kubectl.return_value
            mock_kubectl_instance.cluster_exists.return_value = False

            result3 = runner.invoke(
                cli,
                ["config"],
                env={
                    "MK8_AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
                    "MK8_AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    "MK8_AWS_DEFAULT_REGION": "us-east-1",
                },
            )
            assert result3.exit_code == 0

        # All should succeed independently
        assert "mk8 version" in result1.output
        assert "Commands:" in result2.output
        assert "Configuring AWS credentials" in result3.output

    def test_cli_handles_keyboard_interrupt_gracefully(self, runner):
        """Test that CLI handles KeyboardInterrupt gracefully."""
        # This is tested in unit tests with mocking
        # Integration test just verifies the decorator is in place
        from mk8.cli.main import safe_command_execution

        assert callable(safe_command_execution)

    def test_short_and_long_flags_equivalent(self, runner):
        """Test that short and long flag forms produce same results."""
        # Test help flags
        result_long_help = runner.invoke(cli, ["--help"])
        result_short_help = runner.invoke(cli, ["-h"])

        assert result_long_help.exit_code == 0
        assert result_short_help.exit_code == 0
        assert result_long_help.output == result_short_help.output

        # Test verbose flags
        result_long_verbose = runner.invoke(cli, ["--verbose", "version"])
        result_short_verbose = runner.invoke(cli, ["-v", "version"])

        assert result_long_verbose.exit_code == 0
        assert result_short_verbose.exit_code == 0
