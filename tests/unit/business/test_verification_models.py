"""Unit tests for VerificationResult."""

import pytest

from mk8.business.verification_models import VerificationResult
from mk8.integrations.prerequisite_models import PrerequisiteResults, PrerequisiteStatus


class TestVerificationResult:
    """Test VerificationResult class."""

    def test_is_verified_when_all_satisfied(self):
        """Test is_verified returns True when mk8 and prerequisites are satisfied."""
        result = VerificationResult(
            mk8_installed=True,
            prerequisites_ok=True,
            prerequisite_results=PrerequisiteResults(
                docker=PrerequisiteStatus(
                    name="docker",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=True,
                    path="/usr/bin/docker",
                    error=None,
                ),
                kind=PrerequisiteStatus(
                    name="kind",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/local/bin/kind",
                    error=None,
                ),
                kubectl=PrerequisiteStatus(
                    name="kubectl",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/bin/kubectl",
                    error=None,
                ),
            ),
            messages=["✓ mk8 is installed", "✓ All prerequisites satisfied"],
        )

        assert result.is_verified() is True

    def test_is_verified_when_mk8_not_installed(self):
        """Test is_verified returns False when mk8 is not installed."""
        result = VerificationResult(
            mk8_installed=False,
            prerequisites_ok=True,
            prerequisite_results=PrerequisiteResults(
                docker=PrerequisiteStatus(
                    name="docker",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=True,
                    path="/usr/bin/docker",
                    error=None,
                ),
                kind=PrerequisiteStatus(
                    name="kind",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/local/bin/kind",
                    error=None,
                ),
                kubectl=PrerequisiteStatus(
                    name="kubectl",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/bin/kubectl",
                    error=None,
                ),
            ),
            messages=["✗ mk8 is not in PATH", "✓ All prerequisites satisfied"],
        )

        assert result.is_verified() is False

    def test_is_verified_when_prerequisites_not_satisfied(self):
        """Test is_verified returns False when prerequisites are not satisfied."""
        result = VerificationResult(
            mk8_installed=True,
            prerequisites_ok=False,
            prerequisite_results=PrerequisiteResults(
                docker=PrerequisiteStatus(
                    name="docker",
                    installed=False,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path=None,
                    error="Not installed",
                ),
                kind=PrerequisiteStatus(
                    name="kind",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/local/bin/kind",
                    error=None,
                ),
                kubectl=PrerequisiteStatus(
                    name="kubectl",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/bin/kubectl",
                    error=None,
                ),
            ),
            messages=["✓ mk8 is installed", "✗ Missing prerequisites: docker"],
        )

        assert result.is_verified() is False

    def test_is_verified_when_nothing_satisfied(self):
        """Test is_verified returns False when neither mk8 nor prerequisites are satisfied."""
        result = VerificationResult(
            mk8_installed=False,
            prerequisites_ok=False,
            prerequisite_results=PrerequisiteResults(
                docker=PrerequisiteStatus(
                    name="docker",
                    installed=False,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path=None,
                    error="Not installed",
                ),
                kind=PrerequisiteStatus(
                    name="kind",
                    installed=False,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path=None,
                    error="Not installed",
                ),
                kubectl=PrerequisiteStatus(
                    name="kubectl",
                    installed=False,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path=None,
                    error="Not installed",
                ),
            ),
            messages=[
                "✗ mk8 is not in PATH",
                "✗ Missing prerequisites: docker, kind, kubectl",
            ],
        )

        assert result.is_verified() is False

    def test_messages_field(self):
        """Test that messages field stores verification messages."""
        messages = ["Message 1", "Message 2", "Message 3"]
        result = VerificationResult(
            mk8_installed=True,
            prerequisites_ok=True,
            prerequisite_results=PrerequisiteResults(
                docker=PrerequisiteStatus(
                    name="docker",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=True,
                    path="/usr/bin/docker",
                    error=None,
                ),
                kind=PrerequisiteStatus(
                    name="kind",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/local/bin/kind",
                    error=None,
                ),
                kubectl=PrerequisiteStatus(
                    name="kubectl",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/bin/kubectl",
                    error=None,
                ),
            ),
            messages=messages,
        )

        assert result.messages == messages
        assert len(result.messages) == 3
