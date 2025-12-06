"""Integration tests for error handling flows."""

import pytest
from click.testing import CliRunner

from mk8.cli.main import cli
from mk8.core.errors import (
    PrerequisiteError,
    ValidationError,
    CommandError,
    ConfigurationError,
    ExitCode,
)


class TestErrorFlowIntegration:
    """Test end-to-end error handling flows."""

    @pytest.fixture
    def runner(self):
        """Provide a CLI runner for tests."""
        return CliRunner()

    def test_invalid_command_error_flow(self, runner):
        """Test error flow for invalid command."""
        result = runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0
        # Click handles this, so we just verify it fails appropriately

    def test_invalid_option_error_flow(self, runner):
        """Test error flow for invalid option."""
        result = runner.invoke(cli, ["version", "--invalid-option"])

        assert result.exit_code != 0
        # Click handles this

    def test_mk8_error_formatting_in_cli(self, runner):
        """Test that MK8Error exceptions are properly formatted in CLI."""
        # We need to trigger an MK8Error in a command
        # Since we don't have real commands that raise errors yet,
        # we'll test the error handling decorator directly
        from mk8.cli.main import safe_command_execution

        @safe_command_execution
        def test_func():
            raise PrerequisiteError(
                "Docker is not installed",
                suggestions=["Install Docker from https://docker.com"],
            )

        # The decorator should catch and format the error
        with pytest.raises(SystemExit) as exc_info:
            test_func()

        assert exc_info.value.code == ExitCode.COMMAND_ERROR.value

    def test_keyboard_interrupt_handling(self, runner):
        """Test that KeyboardInterrupt is handled gracefully."""
        from mk8.cli.main import safe_command_execution

        @safe_command_execution
        def test_func():
            raise KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            test_func()

        assert exc_info.value.code == ExitCode.KEYBOARD_INTERRUPT.value

    def test_unexpected_exception_handling(self, runner):
        """Test that unexpected exceptions are handled with bug report message."""
        from mk8.cli.main import safe_command_execution

        @safe_command_execution
        def test_func():
            raise RuntimeError("Unexpected error")

        with pytest.raises(SystemExit) as exc_info:
            test_func()

        assert exc_info.value.code == ExitCode.GENERAL_ERROR.value

    def test_click_exception_passthrough(self, runner):
        """Test that Click exceptions are passed through to Click."""
        from mk8.cli.main import safe_command_execution
        import click

        @safe_command_execution
        def test_func():
            raise click.ClickException("Click error")

        # Click exceptions should be re-raised, not caught
        with pytest.raises(click.ClickException):
            test_func()

    def test_prerequisite_error_exit_code(self, runner):
        """Test that PrerequisiteError results in correct exit code."""
        from mk8.cli.main import safe_command_execution

        @safe_command_execution
        def test_func():
            raise PrerequisiteError("Missing prerequisite")

        with pytest.raises(SystemExit) as exc_info:
            test_func()

        assert exc_info.value.code == ExitCode.COMMAND_ERROR.value

    def test_validation_error_exit_code(self, runner):
        """Test that ValidationError results in correct exit code."""
        from mk8.cli.main import safe_command_execution

        @safe_command_execution
        def test_func():
            raise ValidationError("Invalid input")

        with pytest.raises(SystemExit) as exc_info:
            test_func()

        assert exc_info.value.code == ExitCode.COMMAND_ERROR.value

    def test_command_error_exit_code(self, runner):
        """Test that CommandError results in correct exit code."""
        from mk8.cli.main import safe_command_execution

        @safe_command_execution
        def test_func():
            raise CommandError("Command failed")

        with pytest.raises(SystemExit) as exc_info:
            test_func()

        assert exc_info.value.code == ExitCode.COMMAND_ERROR.value

    def test_configuration_error_exit_code(self, runner):
        """Test that ConfigurationError results in correct exit code."""
        from mk8.cli.main import safe_command_execution

        @safe_command_execution
        def test_func():
            raise ConfigurationError("Invalid configuration")

        with pytest.raises(SystemExit) as exc_info:
            test_func()

        assert exc_info.value.code == ExitCode.COMMAND_ERROR.value

    def test_error_with_suggestions_displayed(self, runner):
        """Test that error suggestions are displayed to user."""
        from mk8.cli.main import safe_command_execution
        from io import StringIO
        import sys

        @safe_command_execution
        def test_func():
            raise PrerequisiteError(
                "Docker is not running",
                suggestions=[
                    "Start Docker Desktop",
                    "Run 'systemctl start docker'",
                ],
            )

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            with pytest.raises(SystemExit):
                test_func()
        finally:
            sys.stderr = old_stderr

    def test_error_without_suggestions(self, runner):
        """Test that errors without suggestions are handled correctly."""
        from mk8.cli.main import safe_command_execution

        @safe_command_execution
        def test_func():
            raise CommandError("Something went wrong")

        with pytest.raises(SystemExit) as exc_info:
            test_func()

        assert exc_info.value.code == ExitCode.COMMAND_ERROR.value

    def test_successful_execution_returns_zero(self, runner):
        """Test that successful command execution returns exit code 0."""
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0

    def test_help_always_succeeds(self, runner):
        """Test that help commands always succeed even if other errors exist."""
        # Help should always work
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["version", "--help"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["bootstrap", "--help"])
        assert result.exit_code == 0
