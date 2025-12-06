"""Tests for CLI main entry point."""
import pytest
from click.testing import CliRunner
from mk8.cli.main import cli


class TestCLIMain:
    """Tests for main CLI entry point."""

    def test_cli_without_arguments_shows_help(self) -> None:
        """Test that CLI without arguments shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        assert "mk8" in result.output.lower()

    def test_cli_help_flag(self) -> None:
        """Test --help flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "help" in result.output.lower() or "usage" in result.output.lower()

    def test_cli_h_flag(self) -> None:
        """Test -h flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["-h"])

        assert result.exit_code == 0

    def test_cli_version_flag(self) -> None:
        """Test --version flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_verbose_flag(self) -> None:
        """Test --verbose flag is accepted."""
        runner = CliRunner()
        # Just test that verbose flag is accepted, actual behavior tested elsewhere
        result = runner.invoke(cli, ["--verbose", "--help"])

        assert result.exit_code == 0

    def test_cli_v_flag(self) -> None:
        """Test -v shorthand for verbose."""
        runner = CliRunner()
        result = runner.invoke(cli, ["-v", "--help"])

        assert result.exit_code == 0


class TestCLICommands:
    """Tests for CLI command registration."""

    def test_version_command_exists(self) -> None:
        """Test that version command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "mk8 version" in result.output

    def test_bootstrap_command_group_exists(self) -> None:
        """Test that bootstrap command group is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["bootstrap", "--help"])

        assert result.exit_code == 0
        assert "bootstrap" in result.output.lower()

    def test_config_command_exists(self) -> None:
        """Test that config command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--help"])

        assert result.exit_code == 0
        assert "config" in result.output.lower()


class TestCommandRouting:
    """Tests for command routing infrastructure."""

    def test_commands_properly_registered(self) -> None:
        """Test that all commands are properly registered in the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        # Verify all expected commands are listed
        assert "version" in result.output
        assert "bootstrap" in result.output
        assert "config" in result.output

    def test_version_command_routes_correctly(self) -> None:
        """Test that version command routes to version handler."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "mk8 version 0.1.0" in result.output

    def test_config_command_routes_correctly(self) -> None:
        """Test that config command routes to config handler."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config"])

        assert result.exit_code == 0
        # Config is a placeholder, just verify it runs
        assert "placeholder" in result.output.lower() or "config" in result.output.lower()

    def test_bootstrap_group_routes_correctly(self) -> None:
        """Test that bootstrap group routes correctly."""
        runner = CliRunner()
        result = runner.invoke(cli, ["bootstrap"])

        # Bootstrap group without subcommand should show help
        assert result.exit_code == 0
        assert "bootstrap" in result.output.lower()

    def test_invalid_command_shows_error(self) -> None:
        """Test that invalid command shows appropriate error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "no such command" in result.output.lower()

    def test_invalid_option_shows_error(self) -> None:
        """Test that invalid option shows appropriate error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--invalid-option"])

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "no such option" in result.output.lower()

    def test_command_with_invalid_option_shows_error(self) -> None:
        """Test that command with invalid option shows error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version", "--invalid-option"])

        assert result.exit_code != 0


class TestFlexibleOptionPlacement:
    """Tests for flexible option placement."""

    def test_verbose_before_command(self) -> None:
        """Test verbose flag before command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "version"])

        assert result.exit_code == 0

    def test_verbose_after_command(self) -> None:
        """Test verbose flag after command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version", "--verbose"])

        assert result.exit_code == 0
