"""Unit tests for verify command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mk8.business.verification_models import VerificationResult
from mk8.cli.main import cli
from mk8.integrations.prerequisite_models import PrerequisiteResults, PrerequisiteStatus


class TestVerifyCommand:
    """Test verify command."""

    def test_verify_command_all_satisfied(self):
        """Test verify command when all checks pass."""
        runner = CliRunner()

        mock_result = VerificationResult(
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

        with patch("mk8.cli.commands.verify.VerificationManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.verify.return_value = mock_result
            mock_manager_class.return_value = mock_manager

            result = runner.invoke(cli, ["verify"])

        assert result.exit_code == 0
        assert "mk8 is installed" in result.output
        assert "prerequisites satisfied" in result.output.lower()

    def test_verify_command_missing_prerequisites(self):
        """Test verify command when prerequisites are missing."""
        runner = CliRunner()

        mock_result = VerificationResult(
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

        with patch(
            "mk8.cli.commands.verify.VerificationManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.verify.return_value = mock_result
            mock_manager.get_installation_instructions.return_value = (
                "Installation Instructions:\n\n"
                "Docker:\n  Install Docker: "
                "https://docs.docker.com/engine/install/"
            )
            mock_manager_class.return_value = mock_manager

            result = runner.invoke(cli, ["verify"])

        assert result.exit_code == 4  # PREREQUISITE_ERROR
        assert "Missing prerequisites" in result.output
        assert "Installation Instructions" in result.output

    def test_verify_command_mk8_not_installed(self):
        """Test verify command when mk8 is not installed."""
        runner = CliRunner()

        mock_result = VerificationResult(
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

        with patch("mk8.cli.commands.verify.VerificationManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.verify.return_value = mock_result
            mock_manager_class.return_value = mock_manager

            result = runner.invoke(cli, ["verify"])

        assert result.exit_code == 1  # GENERAL_ERROR
        assert "mk8 is not in PATH" in result.output

    def test_verify_command_verbose(self):
        """Test verify command with verbose flag."""
        runner = CliRunner()

        mock_result = VerificationResult(
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

        with patch("mk8.cli.commands.verify.VerificationManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.verify.return_value = mock_result
            mock_manager_class.return_value = mock_manager

            result = runner.invoke(cli, ["verify", "--verbose"])

        assert result.exit_code == 0
        # Verbose output should include detailed status section
        assert "Detailed Status" in result.output or "docker" in result.output.lower()
