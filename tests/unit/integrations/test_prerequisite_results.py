"""Tests for prerequisite results aggregate model."""

import pytest
from mk8.integrations.prerequisite_models import PrerequisiteStatus, PrerequisiteResults


class TestPrerequisiteResults:
    """Tests for PrerequisiteResults dataclass."""

    def test_create_prerequisite_results_all_satisfied(self) -> None:
        """Test creating PrerequisiteResults when all prerequisites are satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.28.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error=None,
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.docker == docker
        assert results.kind == kind
        assert results.kubectl == kubectl

    def test_all_satisfied_returns_true_when_all_satisfied(self) -> None:
        """Test all_satisfied() returns True when all prerequisites are satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.28.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error=None,
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.all_satisfied() is True

    def test_all_satisfied_returns_false_when_docker_not_satisfied(self) -> None:
        """Test all_satisfied() returns False when Docker is not satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="docker not found",
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.28.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error=None,
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.all_satisfied() is False

    def test_all_satisfied_returns_false_when_kind_not_satisfied(self) -> None:
        """Test all_satisfied() returns False when kind is not satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="kind not found",
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.28.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error=None,
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.all_satisfied() is False

    def test_all_satisfied_returns_false_when_kubectl_not_satisfied(self) -> None:
        """Test all_satisfied() returns False when kubectl is not satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.20.0",
            version_ok=False,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error="Version too old",
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.all_satisfied() is False

    def test_all_satisfied_returns_false_when_docker_daemon_not_running(self) -> None:
        """Test all_satisfied() returns False when Docker daemon is not running."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=False,
            path="/usr/bin/docker",
            error="Docker daemon not running",
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.28.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error=None,
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.all_satisfied() is False

    def test_get_missing_returns_empty_list_when_all_satisfied(self) -> None:
        """Test get_missing() returns empty list when all prerequisites satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.28.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error=None,
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.get_missing() == []

    def test_get_missing_returns_docker_when_not_satisfied(self) -> None:
        """Test get_missing() returns ['docker'] when Docker is not satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="docker not found",
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.28.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error=None,
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.get_missing() == ["docker"]

    def test_get_missing_returns_kind_when_not_satisfied(self) -> None:
        """Test get_missing() returns ['kind'] when kind is not satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="kind not found",
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.28.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error=None,
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.get_missing() == ["kind"]

    def test_get_missing_returns_kubectl_when_not_satisfied(self) -> None:
        """Test get_missing() returns ['kubectl'] when kubectl is not satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="kubectl not found",
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.get_missing() == ["kubectl"]

    def test_get_missing_returns_all_when_all_not_satisfied(self) -> None:
        """Test get_missing() returns all tools when all are not satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="docker not found",
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="kind not found",
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="kubectl not found",
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.get_missing() == ["docker", "kind", "kubectl"]

    def test_get_missing_returns_multiple_when_some_not_satisfied(self) -> None:
        """Test get_missing() returns multiple tools when some are not satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="docker not found",
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="kubectl not found",
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)

        assert results.get_missing() == ["docker", "kubectl"]

    def test_get_status_summary_with_all_satisfied(self) -> None:
        """Test get_status_summary() returns formatted summary when all satisfied."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=True,
            version="24.0.5",
            version_ok=True,
            daemon_running=True,
            path="/usr/bin/docker",
            error=None,
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.28.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error=None,
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)
        summary = results.get_status_summary()

        assert "docker" in summary.lower()
        assert "24.0.5" in summary
        assert (
            "✓" in summary or "ok" in summary.lower() or "satisfied" in summary.lower()
        )
        assert "kind" in summary.lower()
        assert "0.20.0" in summary
        assert "kubectl" in summary.lower()
        assert "1.28.0" in summary

    def test_get_status_summary_with_missing_tools(self) -> None:
        """Test get_status_summary() shows missing tools with errors."""
        docker = PrerequisiteStatus(
            name="docker",
            installed=False,
            version=None,
            version_ok=False,
            daemon_running=None,
            path=None,
            error="docker not found in PATH",
        )
        kind = PrerequisiteStatus(
            name="kind",
            installed=True,
            version="0.20.0",
            version_ok=True,
            daemon_running=None,
            path="/usr/local/bin/kind",
            error=None,
        )
        kubectl = PrerequisiteStatus(
            name="kubectl",
            installed=True,
            version="1.20.0",
            version_ok=False,
            daemon_running=None,
            path="/usr/bin/kubectl",
            error="Version 1.20.0 is below minimum 1.24.0",
        )

        results = PrerequisiteResults(docker=docker, kind=kind, kubectl=kubectl)
        summary = results.get_status_summary()

        assert "docker" in summary.lower()
        assert "not found" in summary.lower()
        assert "kubectl" in summary.lower()
        assert "1.20.0" in summary
        assert "kind" in summary.lower()
        assert "0.20.0" in summary
