"""Property-based tests for PrerequisiteChecker."""

from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

from mk8.integrations.prerequisites import PrerequisiteChecker
from mk8.integrations.prerequisite_models import PrerequisiteResults


class TestPrerequisiteCheckerProperties:
    """Property-based tests for PrerequisiteChecker."""

    @given(
        docker_installed=st.booleans(),
        kind_installed=st.booleans(),
        kubectl_installed=st.booleans(),
    )
    @settings(max_examples=100)
    def test_property_prerequisite_check_completeness(
        self, docker_installed, kind_installed, kubectl_installed
    ):
        """
        Feature: installer, Property 1: Prerequisite check completeness
        For any verification invocation, verify all three prerequisites are checked.
        """
        checker = PrerequisiteChecker()

        with patch("shutil.which") as mock_which:
            # Mock which() to return path or None based on installed status
            def which_side_effect(tool):
                if tool == "docker":
                    return f"/usr/bin/{tool}" if docker_installed else None
                elif tool == "kind":
                    return f"/usr/local/bin/{tool}" if kind_installed else None
                elif tool == "kubectl":
                    return f"/usr/bin/{tool}" if kubectl_installed else None
                return None

            mock_which.side_effect = which_side_effect

            with patch.object(checker, "is_docker_daemon_running", return_value=True):
                result = checker.check_all()

        # Property: All three prerequisites must be checked
        assert isinstance(result, PrerequisiteResults)
        assert result.docker is not None
        assert result.kind is not None
        assert result.kubectl is not None
        assert result.docker.name == "docker"
        assert result.kind.name == "kind"
        assert result.kubectl.name == "kubectl"

    @given(daemon_running=st.booleans())
    @settings(max_examples=100)
    def test_property_docker_daemon_verification(self, daemon_running):
        """
        Feature: installer, Property 2: Docker daemon verification
        For any Docker check when Docker is installed, verify daemon status is checked.
        """
        checker = PrerequisiteChecker()

        with patch("shutil.which", return_value="/usr/bin/docker"):
            with patch.object(
                checker, "is_docker_daemon_running", return_value=daemon_running
            ) as mock_daemon:
                result = checker.check_docker()

        # Property: When Docker is installed, daemon status must be checked
        assert result.installed is True
        assert result.daemon_running is not None
        assert result.daemon_running == daemon_running
        mock_daemon.assert_called_once()

    @given(
        docker_missing=st.booleans(),
        kind_missing=st.booleans(),
        kubectl_missing=st.booleans(),
    )
    @settings(max_examples=100)
    def test_property_missing_prerequisite_reporting(
        self, docker_missing, kind_missing, kubectl_missing
    ):
        """
        Feature: installer, Property 3: Missing prerequisite reporting
        For any subset of missing prerequisites, verify all are reported.
        """
        checker = PrerequisiteChecker()

        with patch("shutil.which") as mock_which:

            def which_side_effect(tool):
                if tool == "docker" and not docker_missing:
                    return "/usr/bin/docker"
                elif tool == "kind" and not kind_missing:
                    return "/usr/local/bin/kind"
                elif tool == "kubectl" and not kubectl_missing:
                    return "/usr/bin/kubectl"
                return None

            mock_which.side_effect = which_side_effect

            with patch.object(checker, "is_docker_daemon_running", return_value=True):
                result = checker.check_all()

        # Property: All missing prerequisites must be reported
        missing = result.get_missing()
        expected_missing = []
        if docker_missing:
            expected_missing.append("docker")
        if kind_missing:
            expected_missing.append("kind")
        if kubectl_missing:
            expected_missing.append("kubectl")

        assert set(missing) == set(expected_missing)

    @given(
        docker_installed=st.booleans(),
        kind_installed=st.booleans(),
        kubectl_installed=st.booleans(),
    )
    @settings(max_examples=100)
    def test_property_check_idempotence(
        self, docker_installed, kind_installed, kubectl_installed
    ):
        """
        Feature: installer, Property 9: Check idempotence
        For any system state, running checks multiple times returns consistent results.
        """
        checker = PrerequisiteChecker()

        with patch("shutil.which") as mock_which:

            def which_side_effect(tool):
                if tool == "docker":
                    return f"/usr/bin/{tool}" if docker_installed else None
                elif tool == "kind":
                    return f"/usr/local/bin/{tool}" if kind_installed else None
                elif tool == "kubectl":
                    return f"/usr/bin/{tool}" if kubectl_installed else None
                return None

            mock_which.side_effect = which_side_effect

            with patch.object(checker, "is_docker_daemon_running", return_value=True):
                # Run check multiple times
                result1 = checker.check_all()
                result2 = checker.check_all()
                result3 = checker.check_all()

        # Property: Multiple checks should return consistent results
        assert (
            result1.docker.installed
            == result2.docker.installed
            == result3.docker.installed
        )
        assert (
            result1.kind.installed == result2.kind.installed == result3.kind.installed
        )
        assert (
            result1.kubectl.installed
            == result2.kubectl.installed
            == result3.kubectl.installed
        )
        assert (
            result1.all_satisfied()
            == result2.all_satisfied()
            == result3.all_satisfied()
        )
        assert result1.get_missing() == result2.get_missing() == result3.get_missing()
