"""Tests for prerequisite status data models."""

import pytest
from mk8.integrations.prerequisite_models import PrerequisiteStatus


class TestPrerequisiteStatus:
    """Tests for PrerequisiteStatus dataclass."""

    def test_create_prerequisite_status_all_satisfied(self) -> None:
        """Test creating PrerequisiteStatus when all checks pass."""
        status = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )

        assert status.name == "docker"
        assert status.installed is True
        assert status.version == "24.0.5"
        assert status.version_ok is True
        assert status.daemon_running is True
        assert status.path == "/usr/bin/docker"
        assert status.error is None

    def test_create_prerequisite_status_not_installed(self) -> None:
        """Test creating PrerequisiteStatus when tool is not installed."""
        status = PrerequisiteStatus(
            name="kind",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="kind not found in PATH",
        )

        assert status.name == "kind"
        assert status.installed is False
        assert status.version is None
        assert status.version_ok is False
        assert status.daemon_running is None
        assert status.path is None
        assert status.error == "kind not found in PATH"

    def test_create_prerequisite_status_old_version(self) -> None:
        """Test creating PrerequisiteStatus when version is too old."""
        status = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.20.0",
            version_ok=False,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error="Version 1.20.0 is below minimum required 1.24.0",
        )

        assert status.name == "kubectl"
        assert status.installed is True
        assert status.version == "1.20.0"
        assert status.version_ok is False
        assert status.daemon_running is None
        assert status.path == "/usr/bin/kubectl"
        assert status.error == "Version 1.20.0 is below minimum required 1.24.0"

    def test_is_satisfied_returns_true_when_all_checks_pass(self) -> None:
        """Test is_satisfied() returns True when all checks pass."""
        status = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )

        assert status.is_satisfied() is True

    def test_is_satisfied_returns_false_when_not_installed(self) -> None:
        """Test is_satisfied() returns False when tool is not installed."""
        status = PrerequisiteStatus(
            name="kind",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="kind not found",
        )

        assert status.is_satisfied() is False

    def test_is_satisfied_returns_false_when_version_not_ok(self) -> None:
        """Test is_satisfied() returns False when version is not ok."""
        status = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.20.0",
            version_ok=False,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error="Version too old",
        )

        assert status.is_satisfied() is False

    def test_is_satisfied_returns_false_when_daemon_not_running(self) -> None:
        """Test is_satisfied() returns False when daemon is not running."""
        status = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=False,
            path="/usr/bin/docker",
            error="Docker daemon is not running",
        )

        assert status.is_satisfied() is False

    def test_is_satisfied_returns_true_when_daemon_running_is_none(
        self,
    ) -> None:
        """Test is_satisfied() when daemon_running is None."""
        status = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )

        assert status.is_satisfied() is True

    def test_is_satisfied_returns_true_when_daemon_running_is_true(self) -> None:
        """Test is_satisfied() returns True when daemon is running."""
        status = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )

        assert status.is_satisfied() is True

    def test_prerequisite_status_equality(self) -> None:
        """Test that two PrerequisiteStatus instances with same values are equal."""
        status1 = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        status2 = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )

        assert status1 == status2

    def test_prerequisite_status_inequality(self) -> None:
        """Test PrerequisiteStatus instances with different values."""
        status1 = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        status2 = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )

        assert status1 != status2
