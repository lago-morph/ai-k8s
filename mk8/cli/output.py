"""Output formatting for the CLI."""
import sys
from typing import List, Optional


class OutputFormatter:
    """Handles formatted output to the console."""

    def __init__(self, verbose: bool = False):
        """
        Initialize the output formatter.

        Args:
            verbose: Enable verbose output mode
        """
        self.verbose = verbose

    def info(self, message: str) -> None:
        """
        Print informational message.

        Args:
            message: Message to print
        """
        print(message)

    def success(self, message: str) -> None:
        """
        Print success message.

        Args:
            message: Success message to print
        """
        print(message)

    def warning(self, message: str) -> None:
        """
        Print warning message.

        Args:
            message: Warning message to print
        """
        print(message, file=sys.stderr)

    def error(self, message: str, suggestions: Optional[List[str]] = None) -> None:
        """
        Print error message with optional suggestions.

        Args:
            message: Error message to print
            suggestions: Optional list of suggestions for resolving the error
        """
        print(message, file=sys.stderr)

        if suggestions:
            print("", file=sys.stderr)
            print("Suggestions:", file=sys.stderr)
            for suggestion in suggestions:
                print(f"  • {suggestion}", file=sys.stderr)

    def progress(self, message: str) -> None:
        """
        Print progress message (only in verbose mode).

        Args:
            message: Progress message to print
        """
        if self.verbose:
            print(message)

    def debug(self, message: str) -> None:
        """
        Print debug message (only in verbose mode).

        Args:
            message: Debug message to print
        """
        if self.verbose:
            print(message)
