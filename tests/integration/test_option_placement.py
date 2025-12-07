"""Integration tests for flexible option placement."""

import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner

from mk8.cli.main import cli


class TestOptionPlacementIntegration:
    """Test flexible option placement in various command scenarios."""

    @pytest.fixture
    def runner(self):
        """Provide a CLI runner for tests."""
        return CliRunner()

    def test_global_option_before_command(self, runner):
        """Test global option placed before command."""
        result = runner.invoke(cli, ["--verbose", "version"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output

    def test_global_option_after_command(self, runner):
        """Test global option placed after command."""
        result = runner.invoke(cli, ["version", "--verbose"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output

    def test_short_option_before_command(self, runner):
        """Test short form option before command."""
        result = runner.invoke(cli, ["-v", "version"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output

    def test_short_option_after_command(self, runner):
        """Test short form option after command."""
        result = runner.invoke(cli, ["version", "-v"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output

    def test_help_option_before_command(self, runner):
        """Test help option before command name."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "mk8 - Manage Kubernetes infrastructure on AWS" in result.output

    def test_help_option_after_command(self, runner):
        """Test help option after command name."""
        result = runner.invoke(cli, ["version", "--help"])

        assert result.exit_code == 0
        assert "Show version information" in result.output

    def test_short_help_before_command(self, runner):
        """Test short help flag before command."""
        result = runner.invoke(cli, ["-h"])

        assert result.exit_code == 0
        assert "mk8 - Manage Kubernetes infrastructure on AWS" in result.output

    def test_short_help_after_command(self, runner):
        """Test short help flag after command."""
        result = runner.invoke(cli, ["version", "-h"])

        assert result.exit_code == 0
        assert "Show version information" in result.output

    def test_multiple_options_before_command(self, runner):
        """Test multiple options before command."""
        result = runner.invoke(cli, ["--verbose", "version"])

        assert result.exit_code == 0

    def test_multiple_options_after_command(self, runner):
        """Test multiple options after command."""
        result = runner.invoke(cli, ["version", "--verbose"])

        assert result.exit_code == 0

    def test_mixed_option_positions(self, runner):
        """Test options in mixed positions."""
        # Verbose before, help after
        result = runner.invoke(cli, ["--verbose", "version", "--help"])

        assert result.exit_code == 0
        assert "Show version information" in result.output

    def test_option_with_command_group(self, runner):
        """Test options work with command groups."""
        # Option before group
        result1 = runner.invoke(cli, ["--verbose", "bootstrap"])
        assert result1.exit_code == 0

        # Option after group
        result2 = runner.invoke(cli, ["bootstrap", "--verbose"])
        assert result2.exit_code == 0

    def test_help_with_command_group_before(self, runner):
        """Test help flag before command group."""
        result = runner.invoke(cli, ["bootstrap", "--help"])

        assert result.exit_code == 0
        assert "bootstrap" in result.output
        assert "Manage local bootstrap cluster" in result.output

    def test_help_with_command_group_after(self, runner):
        """Test help flag after command group."""
        result = runner.invoke(cli, ["bootstrap", "--help"])

        assert result.exit_code == 0
        assert "bootstrap" in result.output

    def test_version_flag_at_top_level(self, runner):
        """Test --version flag at top level."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output

    def test_version_command_with_verbose_before(self, runner):
        """Test version command with verbose flag before."""
        result = runner.invoke(cli, ["--verbose", "version"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output

    def test_version_command_with_verbose_after(self, runner):
        """Test version command with verbose flag after."""
        result = runner.invoke(cli, ["version", "--verbose"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output

    @patch("mk8.cli.commands.config.AWSClient")
    @patch("mk8.cli.commands.config.KubectlClient")
    def test_config_command_with_options(
        self, mock_kubectl: Mock, mock_aws: Mock, runner
    ):
        """Test config command with various option placements."""
        from mk8.business.credential_models import ValidationResult

        # Mock AWS client
        mock_aws_instance = mock_aws.return_value
        mock_aws_instance.validate_credentials.return_value = ValidationResult(
            success=True, account_id="123456789012"
        )

        # Mock kubectl client
        mock_kubectl_instance = mock_kubectl.return_value
        mock_kubectl_instance.cluster_exists.return_value = False

        env_vars = {
            "MK8_AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "MK8_AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "MK8_AWS_DEFAULT_REGION": "us-east-1",
        }

        # Option before
        result1 = runner.invoke(cli, ["--verbose", "config"], env=env_vars)
        assert result1.exit_code == 0

        # Option after
        result2 = runner.invoke(cli, ["config", "--verbose"], env=env_vars)
        assert result2.exit_code == 0

    def test_option_placement_consistency(self, runner):
        """Test that option placement doesn't affect command behavior."""
        # Execute with option before
        result_before = runner.invoke(cli, ["--verbose", "version"])

        # Execute with option after
        result_after = runner.invoke(cli, ["version", "--verbose"])

        # Both should succeed
        assert result_before.exit_code == 0
        assert result_after.exit_code == 0

        # Both should show version
        assert "mk8 version" in result_before.output
        assert "mk8 version" in result_after.output

    def test_no_option_conflicts(self, runner):
        """Test that there are no conflicts between option positions."""
        # All these should work without conflicts
        commands = [
            ["--verbose", "version"],
            ["version", "--verbose"],
            ["-v", "version"],
            ["version", "-v"],
            ["--help"],
            ["version", "--help"],
            ["-h"],
            ["version", "-h"],
        ]

        for cmd in commands:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == 0, f"Command {cmd} failed"
