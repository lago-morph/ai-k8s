"""Unit tests for VerificationManager."""

from unittest.mock import MagicMock, patch

import pytest

from mk8.business.verification import VerificationManager
from mk8.business.verification_models import VerificationResult
from mk8.integrations.prerequisite_models import PrerequisiteResults, PrerequisiteStatus


class TestVerificationManager:
    """Test VerificationManager class."""

    def test_verify_mk8_installed(self):
        """Test mk8 installation check when installed."""
        manager = VerificationManager()

        with patch("shutil.which", return_value="/usr/local/bin/mk8"):
            result = manager.verify_mk8_installed()

        assert result is True

    def test_verify_mk8_not_installed(self):
        """Test mk8 installation check when not installed."""
        manager = VerificationManager()

        with patch("shutil.which", return_value=None):
            result = manager.verify_mk8_installed()

        assert result is False

    def test_get_installation_instructions_docker(self):
        """Test installation instructions for Docker."""
        manager = VerificationManager()

        instructions = manager.get_installation_instructions(["docker"])

        assert "docker" in instructions.lower()
        assert "https://docs.docker.com" in instructions

    def test_get_installation_instructions_kind(self):
        """Test installation instructions for kind."""
        manager = VerificationManager()

        instructions = manager.get_installation_instructions(["kind"])

        assert "kind" in instructions.lower()
        assert "curl" in instructions or "https://" in instructions

    def test_get_installation_instructions_kubectl(self):
        """Test installation instructions for kubectl."""
        manager = VerificationManager()

        instructions = manager.get_installation_instructions(["kubectl"])

        assert "kubectl" in instructions.lower()
        assert "https://" in instructions

    def test_get_installation_instructions_multiple(self):
        """Test installation instructions for multiple tools."""
        manager = VerificationManager()

        instructions = manager.get_installation_instructions(
            ["docker", "kind", "kubectl"]
        )

        assert "docker" in instructions.lower()
        assert "kind" in instructions.lower()
        assert "kubectl" in instructions.lower()

    def test_verify_all_satisfied(self):
        """Test verify when all checks pass."""
        manager = VerificationManager()

        mock_results = PrerequisiteResults(
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

        with patch.object(manager, "verify_mk8_installed", return_value=True):
            with patch(
                "mk8.business.verification.PrerequisiteChecker"
            ) as mock_checker_class:
                mock_checker = MagicMock()
                mock_checker.check_all.return_value = mock_results
                mock_checker_class.return_value = mock_checker

                result = manager.verify()

        assert isinstance(result, VerificationResult)
        assert result.mk8_installed is True
        assert result.prerequisites_ok is True
        assert result.is_verified() is True
        assert len(result.messages) > 0

    def test_verify_missing_prerequisites(self):
        """Test verify when prerequisites are missing."""
        manager = VerificationManager()

        mock_results = PrerequisiteResults(
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
        )

        with patch.object(manager, "verify_mk8_installed", return_value=True):
            with patch(
                "mk8.business.verification.PrerequisiteChecker"
            ) as mock_checker_class:
                mock_checker = MagicMock()
                mock_checker.check_all.return_value = mock_results
                mock_checker_class.return_value = mock_checker

                result = manager.verify()

        assert isinstance(result, VerificationResult)
        assert result.mk8_installed is True
        assert result.prerequisites_ok is False
        assert result.is_verified() is False
        assert len(result.messages) > 0

    def test_verify_when_mk8_not_installed(self):
        """Test verify when mk8 is not installed."""
        manager = VerificationManager()

        mock_results = PrerequisiteResults(
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

        with patch.object(manager, "verify_mk8_installed", return_value=False):
            with patch(
                "mk8.business.verification.PrerequisiteChecker"
            ) as mock_checker_class:
                mock_checker = MagicMock()
                mock_checker.check_all.return_value = mock_results
                mock_checker_class.return_value = mock_checker

                result = manager.verify()

        assert isinstance(result, VerificationResult)
        assert result.mk8_installed is False
        assert result.prerequisites_ok is True
        assert result.is_verified() is False
        assert len(result.messages) > 0
