"""Integration tests for the hierarchical help system."""
import pytest
from click.testing import CliRunner

from mk8.cli.main import cli


class TestHierarchicalHelp:
    """Test the hierarchical help system at all command levels."""

    @pytest.fixture
    def runner(self):
        """Provide a CLI runner for tests."""
        return CliRunner()

    def test_top_level_help_with_long_flag(self, runner):
        """Test that mk8 --help shows all top-level commands."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "mk8 - Manage Kubernetes infrastructure on AWS" in result.output
        assert "Commands:" in result.output
        assert "bootstrap" in result.output
        assert "config" in result.output
        assert "version" in result.output
        assert "Manage local bootstrap cluster" in result.output
        assert "Configure AWS credentials" in result.output
        assert "Show version information" in result.output

    def test_top_level_help_with_short_flag(self, runner):
        """Test that mk8 -h shows the same help as --help."""
        result_long = runner.invoke(cli, ["--help"])
        result_short = runner.invoke(cli, ["-h"])

        assert result_short.exit_code == 0
        assert result_short.output == result_long.output

    def test_no_command_shows_help(self, runner):
        """Test that running mk8 without arguments shows help."""
        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        assert "mk8 - Manage Kubernetes infrastructure on AWS" in result.output
        assert "Commands:" in result.output

    def test_global_options_in_help(self, runner):
        """Test that global options are shown in top-level help."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Options:" in result.output
        assert "-v, --verbose" in result.output
        assert "Enable verbose output" in result.output
        assert "--version" in result.output
        assert "Show version information" in result.output
        assert "-h, --help" in result.output

    def test_bootstrap_group_help_with_long_flag(self, runner):
        """Test that mk8 bootstrap --help shows bootstrap subcommands."""
        result = runner.invoke(cli, ["bootstrap", "--help"])

        assert result.exit_code == 0
        assert "bootstrap" in result.output
        assert "Manage local bootstrap cluster" in result.output
        # Note: Bootstrap subcommands (create, delete, status) will be added
        # in the local-bootstrap-cluster spec, so we just verify the group help works

    def test_bootstrap_group_help_with_short_flag(self, runner):
        """Test that mk8 bootstrap -h shows the same help as --help."""
        result_long = runner.invoke(cli, ["bootstrap", "--help"])
        result_short = runner.invoke(cli, ["bootstrap", "-h"])

        assert result_short.exit_code == 0
        assert result_short.output == result_long.output

    def test_config_command_help_with_long_flag(self, runner):
        """Test that mk8 config --help shows config command help."""
        result = runner.invoke(cli, ["config", "--help"])

        assert result.exit_code == 0
        assert "config" in result.output
        assert "Configure AWS credentials" in result.output

    def test_config_command_help_with_short_flag(self, runner):
        """Test that mk8 config -h shows the same help as --help."""
        result_long = runner.invoke(cli, ["config", "--help"])
        result_short = runner.invoke(cli, ["config", "-h"])

        assert result_short.exit_code == 0
        assert result_short.output == result_long.output

    def test_version_command_help_with_long_flag(self, runner):
        """Test that mk8 version --help shows version command help."""
        result = runner.invoke(cli, ["version", "--help"])

        assert result.exit_code == 0
        assert "version" in result.output
        assert "Show version information" in result.output

    def test_version_command_help_with_short_flag(self, runner):
        """Test that mk8 version -h shows the same help as --help."""
        result_long = runner.invoke(cli, ["version", "--help"])
        result_short = runner.invoke(cli, ["version", "-h"])

        assert result_short.exit_code == 0
        assert result_short.output == result_long.output

    def test_help_is_contextual_at_each_level(self, runner):
        """Test that help output is different and contextual at each level."""
        top_level_help = runner.invoke(cli, ["--help"])
        bootstrap_help = runner.invoke(cli, ["bootstrap", "--help"])
        version_help = runner.invoke(cli, ["version", "--help"])

        # All should succeed
        assert top_level_help.exit_code == 0
        assert bootstrap_help.exit_code == 0
        assert version_help.exit_code == 0

        # Top level and version help should have different content
        assert top_level_help.output != version_help.output

        # Top level should list all commands
        assert "bootstrap" in top_level_help.output
        assert "config" in top_level_help.output
        assert "version" in top_level_help.output
        assert "Commands:" in top_level_help.output

        # Bootstrap help should include bootstrap description
        assert "bootstrap" in bootstrap_help.output
        assert "Manage local bootstrap cluster" in bootstrap_help.output

        # Version help should focus on version
        assert "version" in version_help.output
        assert "Show version information" in version_help.output
        # Version help should not show all commands list like top level
        assert "Usage: cli version" in version_help.output

    def test_invalid_command_suggests_help(self, runner):
        """Test that invalid commands suggest using --help."""
        result = runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0
        assert "Error" in result.output or "No such command" in result.output

    def test_help_with_verbose_flag_works(self, runner):
        """Test that help works when combined with verbose flag."""
        # Test verbose before help
        result1 = runner.invoke(cli, ["--verbose", "--help"])
        # Test help before verbose
        result2 = runner.invoke(cli, ["--help", "--verbose"])

        assert result1.exit_code == 0
        assert result2.exit_code == 0
        assert "mk8 - Manage Kubernetes infrastructure on AWS" in result1.output
        assert "mk8 - Manage Kubernetes infrastructure on AWS" in result2.output
