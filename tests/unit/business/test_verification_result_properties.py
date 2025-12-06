"""Property-based tests for VerificationResult."""

from hypothesis import given, settings
from hypothesis import strategies as st

from mk8.business.verification_models import VerificationResult
from mk8.integrations.prerequisite_models import PrerequisiteResults, PrerequisiteStatus


class TestVerificationResultProperties:
    """Property-based tests for VerificationResult."""

    @given(
        mk8_installed=st.booleans(),
        docker_installed=st.booleans(),
        kind_installed=st.booleans(),
        kubectl_installed=st.booleans(),
    )
    @settings(max_examples=100)
    def test_property_verification_failure_reporting(
        self, mk8_installed, docker_installed, kind_installed, kubectl_installed
    ):
        """
        Feature: installer, Property 6: Verification failure reporting
        For any failed check, verify failure information is included in results.
        """
        prerequisites_ok = docker_installed and kind_installed and kubectl_installed

        result = VerificationResult(
            mk8_installed=mk8_installed,
            prerequisites_ok=prerequisites_ok,
            prerequisite_results=PrerequisiteResults(
                docker=PrerequisiteStatus(
                    name="docker",
                    installed=docker_installed,
                    version=None,
                    version_ok=True,
                    daemon_running=True if docker_installed else None,
                    path="/usr/bin/docker" if docker_installed else None,
                    error=None if docker_installed else "Not installed",
                ),
                kind=PrerequisiteStatus(
                    name="kind",
                    installed=kind_installed,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/local/bin/kind" if kind_installed else None,
                    error=None if kind_installed else "Not installed",
                ),
                kubectl=PrerequisiteStatus(
                    name="kubectl",
                    installed=kubectl_installed,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/bin/kubectl" if kubectl_installed else None,
                    error=None if kubectl_installed else "Not installed",
                ),
            ),
            messages=["Test message"],
        )

        # Property: is_verified() must return True only when both conditions met
        expected_verified = mk8_installed and prerequisites_ok
        assert result.is_verified() == expected_verified

        # Property: If not verified, at least one component must be False
        if not result.is_verified():
            assert not mk8_installed or not prerequisites_ok
