"""Logging configuration for mk8."""
import logging
import sys
from datetime import datetime


class VerboseFormatter(logging.Formatter):
    """Custom formatter that includes timestamps for verbose mode."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with timestamp.

        Args:
            record: Log record to format

        Returns:
            Formatted log message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        message = record.getMessage()
        return f"[{timestamp}] {level}: {message}"


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        verbose: Enable verbose logging with timestamps and DEBUG level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("mk8")

    # Remove any existing handlers to avoid duplicates
    logger.handlers = []

    # Set logging level
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Set formatter based on verbose flag
    if verbose:
        formatter = VerboseFormatter()
    else:
        formatter = logging.Formatter("%(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
