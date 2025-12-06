"""Tests for error handling module."""
import pytest
from mk8.core.errors import (
    ExitCode,
    MK8Error,
    PrerequisiteError,
    ValidationError,
    CommandError,
    ConfigurationError,
)


class TestExitCode:
    """Tests for ExitCode enum."""

    def test_exit_code_values(self) -> None:
        """Test that exit codes have expected values."""
        assert ExitCode.SUCCESS.value == 0
        assert ExitCode.GENERAL_ERROR.value == 1
        assert ExitCode.COMMAND_ERROR.value == 2
        assert ExitCode.VALIDATION_ERROR.value == 3
        assert ExitCode.PREREQUISITE_ERROR.value == 4
        assert ExitCode.CONFIGURATION_ERROR.value == 5
        assert ExitCode.KEYBOARD_INTERRUPT.value == 130


class TestMK8Error:
    """Tests for MK8Error base exception."""

    def test_create_error_with_message(self) -> None:
        """Test creating error with just a message."""
        error = MK8Error("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.suggestions == []
        assert str(error) == "Something went wrong"

    def test_create_error_with_suggestions(self) -> None:
        """Test creating error with message and suggestions."""
        suggestions = ["Try this", "Or try that"]
        error = MK8Error("Something went wrong", suggestions)
        assert error.message == "Something went wrong"
        assert error.suggestions == suggestions

    def test_format_error_without_suggestions(self) -> None:
        """Test formatting error message without suggestions."""
        error = MK8Error("Docker is not installed")
        formatted = error.format_error()

        assert "Error: Docker is not installed" in formatted
        assert "Suggestions:" not in formatted

    def test_format_error_with_suggestions(self) -> None:
        """Test formatting error message with suggestions."""
        suggestions = [
            "Install Docker from https://docker.com",
            "Check if Docker is in your PATH",
        ]
        error = MK8Error("Docker is not installed", suggestions)
        formatted = error.format_error()

        assert "Error: Docker is not installed" in formatted
        assert "Suggestions:" in formatted
        assert "• Install Docker from https://docker.com" in formatted
        assert "• Check if Docker is in your PATH" in formatted

    def test_format_error_with_single_suggestion(self) -> None:
        """Test formatting error with a single suggestion."""
        error = MK8Error("Invalid argument", ["Use --help for usage info"])
        formatted = error.format_error()

        assert "Error: Invalid argument" in formatted
        assert "Suggestions:" in formatted
        assert "• Use --help for usage info" in formatted


class TestPrerequisiteError:
    """Tests for PrerequisiteError."""

    def test_prerequisite_error_is_mk8_error(self) -> None:
        """Test that PrerequisiteError inherits from MK8Error."""
        error = PrerequisiteError("Missing prerequisite")
        assert isinstance(error, MK8Error)

    def test_prerequisite_error_format(self) -> None:
        """Test formatting prerequisite error."""
        error = PrerequisiteError(
            "kubectl is not installed", ["Install kubectl: apt install kubectl"]
        )
        formatted = error.format_error()

        assert "Error: kubectl is not installed" in formatted
        assert "• Install kubectl: apt install kubectl" in formatted


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error_is_mk8_error(self) -> None:
        """Test that ValidationError inherits from MK8Error."""
        error = ValidationError("Invalid input")
        assert isinstance(error, MK8Error)

    def test_validation_error_format(self) -> None:
        """Test formatting validation error."""
        error = ValidationError(
            "Invalid Kubernetes version", ["Use format: 1.28.0"]
        )
        formatted = error.format_error()

        assert "Error: Invalid Kubernetes version" in formatted
        assert "• Use format: 1.28.0" in formatted


class TestCommandError:
    """Tests for CommandError."""

    def test_command_error_is_mk8_error(self) -> None:
        """Test that CommandError inherits from MK8Error."""
        error = CommandError("Command failed")
        assert isinstance(error, MK8Error)

    def test_command_error_format(self) -> None:
        """Test formatting command error."""
        error = CommandError(
            "Failed to create cluster", ["Check Docker is running", "Check disk space"]
        )
        formatted = error.format_error()

        assert "Error: Failed to create cluster" in formatted
        assert "• Check Docker is running" in formatted
        assert "• Check disk space" in formatted


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_configuration_error_is_mk8_error(self) -> None:
        """Test that ConfigurationError inherits from MK8Error."""
        error = ConfigurationError("Invalid configuration")
        assert isinstance(error, MK8Error)

    def test_configuration_error_format(self) -> None:
        """Test formatting configuration error."""
        error = ConfigurationError(
            "AWS credentials not found", ["Run 'mk8 config' to configure credentials"]
        )
        formatted = error.format_error()

        assert "Error: AWS credentials not found" in formatted
        assert "• Run 'mk8 config' to configure credentials" in formatted
