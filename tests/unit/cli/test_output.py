"""Tests for output formatter."""
import pytest
from io import StringIO
from unittest.mock import patch
from mk8.cli.output import OutputFormatter


class TestOutputFormatter:
    """Tests for OutputFormatter class."""

    def test_init_without_verbose(self) -> None:
        """Test OutputFormatter initialization without verbose flag."""
        formatter = OutputFormatter(verbose=False)
        assert formatter.verbose is False

    def test_init_with_verbose(self) -> None:
        """Test OutputFormatter initialization with verbose flag."""
        formatter = OutputFormatter(verbose=True)
        assert formatter.verbose is True

    def test_info(self) -> None:
        """Test info output method."""
        formatter = OutputFormatter()
        with patch("sys.stdout", new=StringIO()) as fake_out:
            formatter.info("Information message")
            output = fake_out.getvalue()
            assert "Information message" in output

    def test_success(self) -> None:
        """Test success output method."""
        formatter = OutputFormatter()
        with patch("sys.stdout", new=StringIO()) as fake_out:
            formatter.success("Operation successful")
            output = fake_out.getvalue()
            assert "Operation successful" in output

    def test_warning(self) -> None:
        """Test warning output method."""
        formatter = OutputFormatter()
        with patch("sys.stderr", new=StringIO()) as fake_err:
            formatter.warning("Warning message")
            output = fake_err.getvalue()
            assert "Warning message" in output

    def test_error_without_suggestions(self) -> None:
        """Test error output without suggestions."""
        formatter = OutputFormatter()
        with patch("sys.stderr", new=StringIO()) as fake_err:
            formatter.error("Error occurred")
            output = fake_err.getvalue()
            assert "Error occurred" in output
            assert "Suggestions:" not in output

    def test_error_with_suggestions(self) -> None:
        """Test error output with suggestions."""
        formatter = OutputFormatter()
        suggestions = ["Try this", "Or that"]
        with patch("sys.stderr", new=StringIO()) as fake_err:
            formatter.error("Error occurred", suggestions)
            output = fake_err.getvalue()
            assert "Error occurred" in output
            assert "Suggestions:" in output
            assert "Try this" in output
            assert "Or that" in output

    def test_progress_in_normal_mode(self) -> None:
        """Test progress output is suppressed in normal mode."""
        formatter = OutputFormatter(verbose=False)
        with patch("sys.stdout", new=StringIO()) as fake_out:
            formatter.progress("Processing...")
            output = fake_out.getvalue()
            # Should not output in normal mode
            assert output == ""

    def test_progress_in_verbose_mode(self) -> None:
        """Test progress output is shown in verbose mode."""
        formatter = OutputFormatter(verbose=True)
        with patch("sys.stdout", new=StringIO()) as fake_out:
            formatter.progress("Processing...")
            output = fake_out.getvalue()
            assert "Processing..." in output

    def test_debug_in_normal_mode(self) -> None:
        """Test debug output is suppressed in normal mode."""
        formatter = OutputFormatter(verbose=False)
        with patch("sys.stdout", new=StringIO()) as fake_out:
            formatter.debug("Debug info")
            output = fake_out.getvalue()
            # Should not output in normal mode
            assert output == ""

    def test_debug_in_verbose_mode(self) -> None:
        """Test debug output is shown in verbose mode."""
        formatter = OutputFormatter(verbose=True)
        with patch("sys.stdout", new=StringIO()) as fake_out:
            formatter.debug("Debug info")
            output = fake_out.getvalue()
            assert "Debug info" in output
