"""Error handling and exception definitions for mk8."""
from enum import Enum
from typing import List, Optional


class ExitCode(Enum):
    """Standard exit codes for the CLI."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    COMMAND_ERROR = 2
    VALIDATION_ERROR = 3
    PREREQUISITE_ERROR = 4
    CONFIGURATION_ERROR = 5
    KEYBOARD_INTERRUPT = 130


class MK8Error(Exception):
    """Base exception for all mk8 errors."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        """
        Initialize MK8Error.

        Args:
            message: Error message describing what went wrong
            suggestions: List of suggestions for resolving the error
        """
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(self.message)

    def format_error(self) -> str:
        """
        Format error message with suggestions.

        Returns:
            Formatted error message string
        """
        lines = [f"Error: {self.message}"]

        if self.suggestions:
            lines.append("")
            lines.append("Suggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  • {suggestion}")

        return "\n".join(lines)


class PrerequisiteError(MK8Error):
    """Raised when prerequisites are not met."""

    pass


class ValidationError(MK8Error):
    """Raised when input validation fails."""

    pass


class CommandError(MK8Error):
    """Raised when a command execution fails."""

    pass


class ConfigurationError(MK8Error):
    """Raised when configuration is invalid."""

    pass
