"""Unit tests for VerificationError."""

import pytest

from mk8.core.errors import MK8Error, VerificationError


class TestVerificationError:
    """Test VerificationError class."""

    def test_inherits_from_mk8_error(self):
        """Test that VerificationError inherits from MK8Error."""
        error = VerificationError("Test error")

        assert isinstance(error, MK8Error)
        assert isinstance(error, Exception)

    def test_error_with_message_only(self):
        """Test VerificationError with message only."""
        message = "Verification failed"
        error = VerificationError(message)

        assert error.message == message
        assert error.suggestions == []
        assert str(error) == message

    def test_error_with_suggestions(self):
        """Test VerificationError with message and suggestions."""
        message = "Verification failed"
        suggestions = ["Install missing tools", "Check PATH configuration"]
        error = VerificationError(message, suggestions=suggestions)

        assert error.message == message
        assert error.suggestions == suggestions

    def test_format_error_without_suggestions(self):
        """Test format_error with no suggestions."""
        message = "Verification failed"
        error = VerificationError(message)

        formatted = error.format_error()

        assert "Error: Verification failed" in formatted
        assert "Suggestions:" not in formatted

    def test_format_error_with_suggestions(self):
        """Test format_error with suggestions."""
        message = "Verification failed"
        suggestions = ["Install missing tools", "Check PATH configuration"]
        error = VerificationError(message, suggestions=suggestions)

        formatted = error.format_error()

        assert "Error: Verification failed" in formatted
        assert "Suggestions:" in formatted
        assert "• Install missing tools" in formatted
        assert "• Check PATH configuration" in formatted

    def test_format_error_with_single_suggestion(self):
        """Test format_error with a single suggestion."""
        message = "Verification failed"
        suggestions = ["Run mk8 verify --verbose for details"]
        error = VerificationError(message, suggestions=suggestions)

        formatted = error.format_error()

        assert "Error: Verification failed" in formatted
        assert "Suggestions:" in formatted
        assert "• Run mk8 verify --verbose for details" in formatted

    def test_format_error_with_multiple_suggestions(self):
        """Test format_error with multiple suggestions."""
        message = "Prerequisites not met"
        suggestions = [
            "Install Docker from https://docker.com",
            "Install kind from https://kind.sigs.k8s.io",
            "Install kubectl from https://kubernetes.io",
        ]
        error = VerificationError(message, suggestions=suggestions)

        formatted = error.format_error()

        assert "Error: Prerequisites not met" in formatted
        assert "Suggestions:" in formatted
        for suggestion in suggestions:
            assert f"• {suggestion}" in formatted

    def test_can_be_raised_and_caught(self):
        """Test that VerificationError can be raised and caught."""
        with pytest.raises(VerificationError) as exc_info:
            raise VerificationError("Test error")

        assert exc_info.value.message == "Test error"

    def test_can_be_caught_as_mk8_error(self):
        """Test that VerificationError can be caught as MK8Error."""
        with pytest.raises(MK8Error) as exc_info:
            raise VerificationError("Test error")

        assert exc_info.value.message == "Test error"

    def test_can_be_caught_as_exception(self):
        """Test that VerificationError can be caught as generic Exception."""
        with pytest.raises(Exception) as exc_info:
            raise VerificationError("Test error")

        assert str(exc_info.value) == "Test error"
