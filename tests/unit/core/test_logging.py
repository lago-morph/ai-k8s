"""Tests for logging module."""

import pytest
import logging
from mk8.core.logging import setup_logging, VerboseFormatter


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_returns_logger(self) -> None:
        """Test that setup_logging returns a logger instance."""
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "mk8"

    def test_setup_logging_normal_mode(self) -> None:
        """Test logging setup in normal (non-verbose) mode."""
        logger = setup_logging(verbose=False)
        assert logger.level == logging.INFO

    def test_setup_logging_verbose_mode(self) -> None:
        """Test logging setup in verbose mode."""
        logger = setup_logging(verbose=True)
        assert logger.level == logging.DEBUG

    def test_setup_logging_has_handler(self) -> None:
        """Test that logger has at least one handler."""
        logger = setup_logging()
        assert len(logger.handlers) > 0


class TestVerboseFormatter:
    """Tests for VerboseFormatter."""

    def test_verbose_formatter_includes_timestamp(self) -> None:
        """Test that verbose formatter includes timestamp."""
        formatter = VerboseFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)

        # Should include timestamp pattern like [YYYY-MM-DD HH:MM:SS]
        assert "[" in formatted
        assert "]" in formatted
        assert "Test message" in formatted

    def test_verbose_formatter_format(self) -> None:
        """Test verbose formatter output format."""
        formatter = VerboseFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="Debug message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)

        # Should be: [timestamp] LEVEL: message
        assert "DEBUG" in formatted
        assert "Debug message" in formatted
