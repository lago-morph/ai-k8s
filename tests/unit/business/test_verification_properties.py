"""Property-based tests for VerificationManager."""

from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

from mk8.business.verification import VerificationManager
from mk8.business.verification_models import VerificationResult
from mk8.integrations.prerequisite_models import PrerequisiteResults, PrerequisiteStatus


class TestVerificationManagerProperties:
    """Property-based tests for VerificationManager."""

    @given(
        docker_missing=st.booleans(),
        kind_missing=st.booleans(),
        kubectl_missing=st.booleans(),
    )
    @settings(max_examples=100)
    def test_property_installation_instructions_provision(
        self, docker_missing, kind_missing, kubectl_missing
    ):
        """
        Feature: installer, Property 4: Installation instructions provision
        For any missing prerequisite, verify instructions are provided.
        """
        manager = VerificationManager()

        missing = []
        if docker_missing:
            missing.append("docker")
        if kind_missing:
            missing.append("kind")
        if kubectl_missing:
            missing.append("kubectl")

        instructions = manager.get_installation_instructions(missing)

        # Property: Instructions must be provided for each missing tool
        if missing:
            assert instructions != ""
            assert "Installation Instructions:" in instructions
            for tool in missing:
                # Each missing tool should have instructions
                assert tool in instructions.lower()
        else:
            assert instructions == ""

    @given(mk8_installed=st.booleans())
    @settings(max_examples=100)
    def test_property_mk8_installation_verification(self, mk8_installed):
        """
        Feature: installer, Property 5: mk8 installation verification
        For any verification invocation, verify mk8 PATH check is performed.
        """
        manager = VerificationManager()

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/mk8" if mk8_installed else None

            with patch(
                "mk8.business.verification.PrerequisiteChecker"
            ) as mock_checker_class:
                mock_checker = MagicMock()
                mock_checker.check_all.return_value = PrerequisiteResults(
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
                )
                mock_checker_class.return_value = mock_checker

                result = manager.verify()

        # Property: mk8 installation must be checked
        assert isinstance(result, VerificationResult)
        assert result.mk8_installed == mk8_installed
        mock_which.assert_called_with("mk8")

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
        manager = VerificationManager()

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/mk8" if mk8_installed else None

            with patch(
                "mk8.business.verification.PrerequisiteChecker"
            ) as mock_checker_class:
                mock_checker = MagicMock()
                mock_checker.check_all.return_value = PrerequisiteResults(
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
                )
                mock_checker_class.return_value = mock_checker

                result = manager.verify()

        # Property: Failed checks must be reported in messages
        all_satisfied = (
            mk8_installed and docker_installed and kind_installed and kubectl_installed
        )

        if not all_satisfied:
            # At least one failure message should be present
            assert any("✗" in msg for msg in result.messages)

            # If mk8 not installed, should be in messages
            if not mk8_installed:
                assert any("mk8" in msg.lower() for msg in result.messages)

            # If prerequisites not satisfied, should be in messages
            if not (docker_installed and kind_installed and kubectl_installed):
                assert any("prerequisite" in msg.lower() for msg in result.messages)

    @given(
        docker_missing=st.booleans(),
        kind_missing=st.booleans(),
        kubectl_missing=st.booleans(),
    )
    @settings(max_examples=100)
    def test_property_failed_checks_include_instructions(
        self, docker_missing, kind_missing, kubectl_missing
    ):
        """Feature: installer, Property 8: Failed checks include instructions.

        For any failed prerequisite check, verify installation instructions
        are included.
        """
        manager = VerificationManager()

        missing = []
        if docker_missing:
            missing.append("docker")
        if kind_missing:
            missing.append("kind")
        if kubectl_missing:
            missing.append("kubectl")

        if missing:
            instructions = manager.get_installation_instructions(missing)

            # Property: Failed checks must have installation instructions
            assert instructions != ""
            for tool in missing:
                assert tool in instructions.lower()
                # Should contain either a URL or command
                assert "http" in instructions or "curl" in instructions
