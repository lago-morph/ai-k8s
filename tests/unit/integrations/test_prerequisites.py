"""Unit tests for PrerequisiteChecker."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mk8.integrations.prerequisites import PrerequisiteChecker
from mk8.integrations.prerequisite_models import PrerequisiteResults, PrerequisiteStatus


class TestPrerequisiteChecker:
    """Test PrerequisiteChecker class."""

    def test_check_docker_installed_daemon_running(self):
        """Test Docker check when installed and daemon running."""
        checker = PrerequisiteChecker()

        with patch("shutil.which", return_value="/usr/bin/docker"):
            with patch.object(checker, "is_docker_daemon_running", return_value=True):
                result = checker.check_docker()

        assert result.name == "docker"
        assert result.installed is True
        assert result.daemon_running is True
        assert result.error is None
        assert result.is_satisfied() is True

    def test_check_docker_installed_daemon_not_running(self):
        """Test Docker check when installed but daemon not running."""
        checker = PrerequisiteChecker()

        with patch("shutil.which", return_value="/usr/bin/docker"):
            with patch.object(checker, "is_docker_daemon_running", return_value=False):
                result = checker.check_docker()

        assert result.name == "docker"
        assert result.installed is True
        assert result.daemon_running is False
        assert result.error is not None
        assert "daemon" in result.error.lower()
        assert result.is_satisfied() is False

    def test_check_docker_not_installed(self):
        """Test Docker check when not installed."""
        checker = PrerequisiteChecker()

        with patch("shutil.which", return_value=None):
            result = checker.check_docker()

        assert result.name == "docker"
        assert result.installed is False
        assert result.daemon_running is None
        assert result.error is not None
        assert result.is_satisfied() is False

    def test_check_kind_installed(self):
        """Test kind check when installed."""
        checker = PrerequisiteChecker()

        with patch("shutil.which", return_value="/usr/local/bin/kind"):
            result = checker.check_kind()

        assert result.name == "kind"
        assert result.installed is True
        assert result.daemon_running is None
        assert result.error is None
        assert result.is_satisfied() is True

    def test_check_kind_not_installed(self):
        """Test kind check when not installed."""
        checker = PrerequisiteChecker()

        with patch("shutil.which", return_value=None):
            result = checker.check_kind()

        assert result.name == "kind"
        assert result.installed is False
        assert result.daemon_running is None
        assert result.error is not None
        assert result.is_satisfied() is False

    def test_check_kubectl_installed(self):
        """Test kubectl check when installed."""
        checker = PrerequisiteChecker()

        with patch("shutil.which", return_value="/usr/bin/kubectl"):
            result = checker.check_kubectl()

        assert result.name == "kubectl"
        assert result.installed is True
        assert result.daemon_running is None
        assert result.error is None
        assert result.is_satisfied() is True

    def test_check_kubectl_not_installed(self):
        """Test kubectl check when not installed."""
        checker = PrerequisiteChecker()

        with patch("shutil.which", return_value=None):
            result = checker.check_kubectl()

        assert result.name == "kubectl"
        assert result.installed is False
        assert result.daemon_running is None
        assert result.error is not None
        assert result.is_satisfied() is False

    def test_is_docker_daemon_running_success(self):
        """Test Docker daemon check when running."""
        checker = PrerequisiteChecker()
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = checker.is_docker_daemon_running()

        assert result is True
        mock_run.assert_called_once_with(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
            check=False,
        )

    def test_is_docker_daemon_running_failure(self):
        """Test Docker daemon check when not running."""
        checker = PrerequisiteChecker()
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            result = checker.is_docker_daemon_running()

        assert result is False

    def test_is_docker_daemon_running_timeout(self):
        """Test Docker daemon check with timeout."""
        checker = PrerequisiteChecker()

        with patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("docker", 5)
        ):
            result = checker.is_docker_daemon_running()

        assert result is False

    def test_is_docker_daemon_running_exception(self):
        """Test Docker daemon check with general exception."""
        checker = PrerequisiteChecker()

        with patch("subprocess.run", side_effect=Exception("Connection error")):
            result = checker.is_docker_daemon_running()

        assert result is False

    def test_check_all_all_satisfied(self):
        """Test check_all when all prerequisites satisfied."""
        checker = PrerequisiteChecker()

        with patch.object(
            checker,
            "check_docker",
            return_value=PrerequisiteStatus(
                name="docker",
                installed=True,
                version=None,
                version_ok=True,
                daemon_running=True,
                path="/usr/bin/docker",
                error=None,
            ),
        ):
            with patch.object(
                checker,
                "check_kind",
                return_value=PrerequisiteStatus(
                    name="kind",
                    installed=True,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path="/usr/local/bin/kind",
                    error=None,
                ),
            ):
                with patch.object(
                    checker,
                    "check_kubectl",
                    return_value=PrerequisiteStatus(
                        name="kubectl",
                        installed=True,
                        version=None,
                        version_ok=True,
                        daemon_running=None,
                        path="/usr/bin/kubectl",
                        error=None,
                    ),
                ):
                    result = checker.check_all()

        assert isinstance(result, PrerequisiteResults)
        assert result.all_satisfied() is True
        assert result.get_missing() == []

    def test_check_all_some_missing(self):
        """Test check_all when some prerequisites missing."""
        checker = PrerequisiteChecker()

        with patch.object(
            checker,
            "check_docker",
            return_value=PrerequisiteStatus(
                name="docker",
                installed=True,
                version=None,
                version_ok=True,
                daemon_running=True,
                path="/usr/bin/docker",
                error=None,
            ),
        ):
            with patch.object(
                checker,
                "check_kind",
                return_value=PrerequisiteStatus(
                    name="kind",
                    installed=False,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path=None,
                    error="Not found",
                ),
            ):
                with patch.object(
                    checker,
                    "check_kubectl",
                    return_value=PrerequisiteStatus(
                        name="kubectl",
                        installed=True,
                        version=None,
                        version_ok=True,
                        daemon_running=None,
                        path="/usr/bin/kubectl",
                        error=None,
                    ),
                ):
                    result = checker.check_all()

        assert isinstance(result, PrerequisiteResults)
        assert result.all_satisfied() is False
        assert result.get_missing() == ["kind"]

    def test_check_all_all_missing(self):
        """Test check_all when all prerequisites missing."""
        checker = PrerequisiteChecker()

        with patch.object(
            checker,
            "check_docker",
            return_value=PrerequisiteStatus(
                name="docker",
                installed=False,
                version=None,
                version_ok=True,
                daemon_running=None,
                path=None,
                error="Not found",
            ),
        ):
            with patch.object(
                checker,
                "check_kind",
                return_value=PrerequisiteStatus(
                    name="kind",
                    installed=False,
                    version=None,
                    version_ok=True,
                    daemon_running=None,
                    path=None,
                    error="Not found",
                ),
            ):
                with patch.object(
                    checker,
                    "check_kubectl",
                    return_value=PrerequisiteStatus(
                        name="kubectl",
                        installed=False,
                        version=None,
                        version_ok=True,
                        daemon_running=None,
                        path=None,
                        error="Not found",
                    ),
                ):
                    result = checker.check_all()

        assert isinstance(result, PrerequisiteResults)
        assert result.all_satisfied() is False
        assert result.get_missing() == ["docker", "kind", "kubectl"]
