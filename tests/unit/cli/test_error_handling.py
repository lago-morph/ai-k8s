"""Tests for CLI error handling."""
import pytest
from click.testing import CliRunner
import click

from mk8.cli.main import cli, safe_command_execution
from mk8.core.errors import MK8Error, PrerequisiteError, ValidationError, CommandError, ExitCode


class TestSafeCommandExecution:
    """Tests for the safe_command_execution decorator."""

    def test_successful_command_execution(self) -> None:
        """Test that successful commands return normally."""

        @safe_command_execution
        def success_command():
            return 0

        result = success_command()
        assert result == 0

    def test_keyboard_interrupt_handling(self) -> None:
        """Test that KeyboardInterrupt is handled gracefully."""

        @safe_command_execution
        def interrupted_command():
            raise KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            interrupted_command()

        assert exc_info.value.code == ExitCode.KEYBOARD_INTERRUPT.value

    def test_mk8_error_handling(self) -> None:
        """Test that MK8Error is formatted and exits with correct code."""

        @safe_command_execution
        def error_command():
            raise CommandError("Test error", suggestions=["Try this"])

        with pytest.raises(SystemExit) as exc_info:
            error_command()

        assert exc_info.value.code == ExitCode.COMMAND_ERROR.value

    def test_click_exception_handling(self) -> None:
        """Test that Click exceptions are re-raised."""

        @safe_command_execution
        def click_error_command():
            raise click.ClickException("Click error")

        with pytest.raises(click.ClickException):
            click_error_command()

    def test_unexpected_exception_handling(self) -> None:
        """Test that unexpected exceptions exit with GENERAL_ERROR."""

        @safe_command_execution
        def unexpected_error_command():
            raise ValueError("Unexpected error")

        with pytest.raises(SystemExit) as exc_info:
            unexpected_error_command()

        assert exc_info.value.code == ExitCode.GENERAL_ERROR.value


class TestCLIErrorIntegration:
    """Integration tests for CLI error handling."""

    def test_invalid_command_error_message(self) -> None:
        """Test that invalid commands show helpful error messages."""
        runner = CliRunner()
        result = runner.invoke(cli, ["nonexistent"])

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "no such command" in result.output.lower()

    def test_invalid_option_error_message(self) -> None:
        """Test that invalid options show helpful error messages."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--nonexistent-option"])

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "no such option" in result.output.lower()
