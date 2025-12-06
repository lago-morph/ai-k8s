"""Property-based tests for VerificationError."""

from hypothesis import given, settings
from hypothesis import strategies as st

from mk8.core.errors import VerificationError


class TestVerificationErrorProperties:
    """Property-based tests for VerificationError."""

    @given(
        message=st.text(min_size=1, max_size=200),
        suggestions=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5),
    )
    @settings(max_examples=100)
    def test_property_error_messages_include_suggestions(self, message, suggestions):
        """
        Feature: installer, Property 7: Error messages include suggestions
        For any error condition, verify suggestions are included.
        """
        error = VerificationError(message, suggestions=suggestions)

        # Property: Error must have suggestions
        assert error.suggestions == suggestions
        assert len(error.suggestions) > 0

        # Property: Formatted error must include all suggestions
        formatted = error.format_error()
        assert "Suggestions:" in formatted
        for suggestion in suggestions:
            assert suggestion in formatted

    @given(message=st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_property_error_without_suggestions_has_empty_list(self, message):
        """
        Verify that errors without suggestions have an empty suggestions list.
        """
        error = VerificationError(message)

        # Property: Error without suggestions should have empty list
        assert error.suggestions == []

        # Property: Formatted error should not include Suggestions section
        formatted = error.format_error()
        assert "Suggestions:" not in formatted
