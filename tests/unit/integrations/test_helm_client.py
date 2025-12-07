"""Tests for HelmClient integration layer."""

import pytest
import subprocess
from unittest.mock import Mock, patch, mock_open
from mk8.integrations.helm_client import HelmClient, HelmError


@pytest.fixture
def helm_client() -> HelmClient:
    """Create HelmClient instance."""
    return HelmClient(context="test-context")


class TestHelmClientInit:
    """Tests for HelmClient initialization."""

    def test_init_with_default_context(self) -> None:
        """Test HelmClient initializes with default context."""
        client = HelmClient()
        assert client.context == "kind-mk8-bootstrap"

    def test_init_with_custom_context(self) -> None:
        """Test HelmClient initializes with custom context."""
        client = HelmClient(context="custom-context")
        assert client.context == "custom-context"


class TestHelmClientRunCommand:
    """Tests for HelmClient._run_helm_command()."""

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_run_helm_command_success(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test _run_helm_command returns stdout on success."""
        mock_run.return_value = Mock(returncode=0, stdout="success output")

        result = helm_client._run_helm_command(["version"])

        assert result == "success output"
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["helm", "version", "--kube-context", "test-context"]

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_run_helm_command_failure(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test _run_helm_command raises HelmError on failure."""
        mock_run.return_value = Mock(returncode=1, stderr="error message")

        with pytest.raises(HelmError, match="helm command failed"):
            helm_client._run_helm_command(["install"])

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_run_helm_command_timeout(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test _run_helm_command raises HelmError on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("helm", 300)

        with pytest.raises(HelmError, match="timed out"):
            helm_client._run_helm_command(["install"])

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_run_helm_command_not_found(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test _run_helm_command raises HelmError when helm not found."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(HelmError, match="helm command not found"):
            helm_client._run_helm_command(["version"])


class TestHelmClientParseError:
    """Tests for HelmClient._parse_helm_error()."""

    def test_parse_error_repository_not_found(self, helm_client: HelmClient) -> None:
        """Test _parse_helm_error suggests repository commands."""
        stderr = "Error: repository not found"

        suggestions = helm_client._parse_helm_error(stderr)

        assert any("helm repo add" in s for s in suggestions)
        assert any("helm repo update" in s for s in suggestions)

    def test_parse_error_already_exists(self, helm_client: HelmClient) -> None:
        """Test _parse_helm_error suggests force or uninstall."""
        stderr = "Error: release already exists"

        suggestions = helm_client._parse_helm_error(stderr)

        assert any("--force" in s for s in suggestions)
        assert any("helm uninstall" in s for s in suggestions)

    def test_parse_error_connection_refused(self, helm_client: HelmClient) -> None:
        """Test _parse_helm_error suggests connectivity checks."""
        stderr = "Error: connection refused"

        suggestions = helm_client._parse_helm_error(stderr)

        assert any("kubectl get nodes" in s for s in suggestions)
        assert any("context" in s.lower() for s in suggestions)

    def test_parse_error_forbidden(self, helm_client: HelmClient) -> None:
        """Test _parse_helm_error suggests RBAC checks."""
        stderr = "Error: forbidden"

        suggestions = helm_client._parse_helm_error(stderr)

        assert any("RBAC" in s for s in suggestions)
        assert any("permissions" in s.lower() for s in suggestions)

    def test_parse_error_unauthorized(self, helm_client: HelmClient) -> None:
        """Test _parse_helm_error suggests auth checks."""
        stderr = "Error: unauthorized"

        suggestions = helm_client._parse_helm_error(stderr)

        assert any("permissions" in s.lower() for s in suggestions)

    def test_parse_error_generic(self, helm_client: HelmClient) -> None:
        """Test _parse_helm_error provides generic suggestions."""
        stderr = "Error: unknown error"

        suggestions = helm_client._parse_helm_error(stderr)

        assert any("helm status" in s for s in suggestions)
        assert len(suggestions) > 0


class TestHelmClientAddRepository:
    """Tests for HelmClient.add_repository()."""

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_add_repository_success(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test add_repository adds repository successfully."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        helm_client.add_repository("stable", "https://charts.helm.sh/stable")

        call_args = mock_run.call_args[0][0]
        assert "repo" in call_args
        assert "add" in call_args
        assert "stable" in call_args
        assert "https://charts.helm.sh/stable" in call_args

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_add_repository_with_force(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test add_repository with force flag."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        helm_client.add_repository(
            "stable", "https://charts.helm.sh/stable", force=True
        )

        call_args = mock_run.call_args[0][0]
        assert "--force-update" in call_args


class TestHelmClientUpdateRepositories:
    """Tests for HelmClient.update_repositories()."""

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_update_repositories_success(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test update_repositories updates all repositories."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        helm_client.update_repositories()

        call_args = mock_run.call_args[0][0]
        assert "repo" in call_args
        assert "update" in call_args


class TestHelmClientInstallChart:
    """Tests for HelmClient.install_chart()."""

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_install_chart_basic(self, mock_run: Mock, helm_client: HelmClient) -> None:
        """Test install_chart with basic parameters."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        helm_client.install_chart(
            release_name="my-release",
            chart="stable/nginx",
            namespace="default",
            values=None,
            wait=False,
        )

        call_args = mock_run.call_args[0][0]
        assert "install" in call_args
        assert "my-release" in call_args
        assert "stable/nginx" in call_args
        assert "--namespace" in call_args
        assert "default" in call_args

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_install_chart_with_create_namespace(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test install_chart creates namespace."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        helm_client.install_chart(
            release_name="my-release",
            chart="stable/nginx",
            namespace="new-ns",
            create_namespace=True,
            wait=False,
        )

        call_args = mock_run.call_args[0][0]
        assert "--create-namespace" in call_args

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_install_chart_with_wait(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test install_chart waits for completion."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        helm_client.install_chart(
            release_name="my-release",
            chart="stable/nginx",
            namespace="default",
            wait=True,
            timeout=300,
        )

        call_args = mock_run.call_args[0][0]
        assert "--wait" in call_args
        assert "--timeout" in call_args
        assert "300s" in call_args

    @patch("os.unlink")
    @patch("mk8.integrations.helm_client.subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("tempfile.NamedTemporaryFile")
    def test_install_chart_with_values(
        self,
        mock_tempfile: Mock,
        mock_file: Mock,
        mock_run: Mock,
        mock_unlink: Mock,
        helm_client: HelmClient,
    ) -> None:
        """Test install_chart with custom values."""
        mock_temp = Mock()
        mock_temp.name = "/tmp/values.yaml"
        mock_temp.__enter__ = Mock(return_value=mock_temp)
        mock_temp.__exit__ = Mock(return_value=False)
        mock_tempfile.return_value = mock_temp

        mock_run.return_value = Mock(returncode=0, stdout="")

        values = {"replicas": 3, "image": {"tag": "latest"}}
        helm_client.install_chart(
            release_name="my-release",
            chart="stable/nginx",
            namespace="default",
            values=values,
            wait=False,
        )

        call_args = mock_run.call_args[0][0]
        assert "--values" in call_args
        mock_unlink.assert_called_once_with("/tmp/values.yaml")


class TestHelmClientUninstallRelease:
    """Tests for HelmClient.uninstall_release()."""

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_uninstall_release_success(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test uninstall_release removes release."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        helm_client.uninstall_release("my-release", "default")

        call_args = mock_run.call_args[0][0]
        assert "uninstall" in call_args
        assert "my-release" in call_args
        assert "--namespace" in call_args
        assert "default" in call_args


class TestHelmClientListReleases:
    """Tests for HelmClient.list_releases()."""

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_list_releases_success(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test list_releases returns release list."""
        mock_output = """[
            {"name": "release1", "namespace": "default", "status": "deployed"},
            {"name": "release2", "namespace": "kube-system", "status": "deployed"}
        ]"""
        mock_run.return_value = Mock(returncode=0, stdout=mock_output)

        releases = helm_client.list_releases("default")

        assert len(releases) == 2
        assert releases[0]["name"] == "release1"
        assert releases[1]["name"] == "release2"

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_list_releases_empty(self, mock_run: Mock, helm_client: HelmClient) -> None:
        """Test list_releases returns empty list when no releases."""
        mock_run.return_value = Mock(returncode=0, stdout="[]")

        releases = helm_client.list_releases("default")

        assert releases == []


class TestHelmClientGetReleaseStatus:
    """Tests for HelmClient.get_release_status()."""

    @patch("mk8.integrations.helm_client.subprocess.run")
    def test_get_release_status_success(
        self, mock_run: Mock, helm_client: HelmClient
    ) -> None:
        """Test get_release_status returns status info."""
        mock_output = '{"name": "my-release", "info": {"status": "deployed"}}'
        mock_run.return_value = Mock(returncode=0, stdout=mock_output)

        status = helm_client.get_release_status("my-release", "default")

        assert status["name"] == "my-release"
        assert status["info"]["status"] == "deployed"


class TestHelmClientReleaseExists:
    """Tests for HelmClient.release_exists()."""

    @patch("mk8.integrations.helm_client.HelmClient.get_release_status")
    def test_release_exists_returns_true(
        self, mock_status: Mock, helm_client: HelmClient
    ) -> None:
        """Test release_exists returns True when release exists."""
        mock_status.return_value = {
            "name": "my-release",
            "info": {"status": "deployed"},
        }

        result = helm_client.release_exists("my-release", "default")

        assert result is True

    @patch("mk8.integrations.helm_client.HelmClient.get_release_status")
    def test_release_exists_returns_false(
        self, mock_status: Mock, helm_client: HelmClient
    ) -> None:
        """Test release_exists returns False when release doesn't exist."""
        mock_status.side_effect = HelmError("Release not found")

        result = helm_client.release_exists("my-release", "default")

        assert result is False
