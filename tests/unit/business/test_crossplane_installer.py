"""Tests for CrossplaneInstaller business logic."""

import pytest
from unittest.mock import Mock, patch, call
from mk8.business.crossplane_installer import CrossplaneInstaller, CrossplaneStatus
from mk8.business.credential_models import AWSCredentials
from mk8.core.errors import CommandError
from mk8.integrations.helm_client import HelmError


@pytest.fixture
def mock_helm() -> Mock:
    """Create mock HelmClient."""
    return Mock()


@pytest.fixture
def mock_kubectl() -> Mock:
    """Create mock KubectlClient."""
    return Mock()


@pytest.fixture
def mock_cred_manager() -> Mock:
    """Create mock CredentialManager."""
    return Mock()


@pytest.fixture
def mock_output() -> Mock:
    """Create mock OutputFormatter."""
    mock = Mock()
    mock.verbose = False
    return mock


@pytest.fixture
def installer(
    mock_helm: Mock, mock_kubectl: Mock, mock_cred_manager: Mock, mock_output: Mock
) -> CrossplaneInstaller:
    """Create CrossplaneInstaller with mocked dependencies."""
    return CrossplaneInstaller(
        helm_client=mock_helm,
        kubectl_client=mock_kubectl,
        credential_manager=mock_cred_manager,
        output=mock_output,
    )


class TestCrossplaneInstallerInit:
    """Tests for CrossplaneInstaller initialization."""

    def test_init_with_dependencies(
        self,
        mock_helm: Mock,
        mock_kubectl: Mock,
        mock_cred_manager: Mock,
        mock_output: Mock,
    ) -> None:
        """Test initialization with provided dependencies."""
        installer = CrossplaneInstaller(
            helm_client=mock_helm,
            kubectl_client=mock_kubectl,
            credential_manager=mock_cred_manager,
            output=mock_output,
        )

        assert installer.helm == mock_helm
        assert installer.kubectl == mock_kubectl
        assert installer.credential_manager == mock_cred_manager
        assert installer.output == mock_output

    def test_init_without_dependencies(self) -> None:
        """Test initialization creates default dependencies."""
        installer = CrossplaneInstaller()

        assert installer.helm is not None
        assert installer.kubectl is not None
        assert installer.credential_manager is not None
        assert installer.output is not None


class TestCrossplaneInstallerInstall:
    """Tests for CrossplaneInstaller.install_crossplane()."""

    @patch.object(CrossplaneInstaller, "_wait_for_crossplane_ready")
    @patch.object(CrossplaneInstaller, "_get_crossplane_values")
    def test_install_crossplane_success(
        self,
        mock_get_values: Mock,
        mock_wait: Mock,
        installer: CrossplaneInstaller,
        mock_helm: Mock,
    ) -> None:
        """Test install_crossplane installs successfully."""
        mock_get_values.return_value = {"key": "value"}

        installer.install_crossplane()

        mock_helm.add_repository.assert_called_once()
        mock_helm.update_repositories.assert_called_once()
        mock_helm.install_chart.assert_called_once()
        mock_wait.assert_called_once()

    @patch.object(CrossplaneInstaller, "_wait_for_crossplane_ready")
    @patch.object(CrossplaneInstaller, "_get_crossplane_values")
    def test_install_crossplane_with_version(
        self,
        mock_get_values: Mock,
        mock_wait: Mock,
        installer: CrossplaneInstaller,
        mock_helm: Mock,
    ) -> None:
        """Test install_crossplane with specific version."""
        mock_get_values.return_value = {}

        installer.install_crossplane(version="1.14.0")

        call_args = mock_helm.install_chart.call_args
        assert "1.14.0" in str(call_args)

    @patch.object(CrossplaneInstaller, "_get_crossplane_values")
    def test_install_crossplane_helm_error(
        self,
        mock_get_values: Mock,
        installer: CrossplaneInstaller,
        mock_helm: Mock,
    ) -> None:
        """Test install_crossplane raises CommandError on Helm failure."""
        mock_get_values.return_value = {}
        mock_helm.add_repository.side_effect = HelmError("Helm failed")

        with pytest.raises(CommandError, match="Failed to install Crossplane"):
            installer.install_crossplane()

    @patch.object(CrossplaneInstaller, "_get_crossplane_values")
    def test_install_crossplane_generic_error(
        self,
        mock_get_values: Mock,
        installer: CrossplaneInstaller,
        mock_helm: Mock,
    ) -> None:
        """Test install_crossplane handles generic errors."""
        mock_get_values.return_value = {}
        mock_helm.add_repository.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(CommandError, match="Failed to install Crossplane"):
            installer.install_crossplane()


class TestCrossplaneInstallerAWSProvider:
    """Tests for AWS provider installation."""

    @patch.object(CrossplaneInstaller, "_wait_for_provider_ready")
    @patch.object(CrossplaneInstaller, "_apply_yaml_resource")
    @patch.object(CrossplaneInstaller, "_get_aws_provider_yaml")
    def test_install_aws_provider_success(
        self,
        mock_get_yaml: Mock,
        mock_apply: Mock,
        mock_wait: Mock,
        installer: CrossplaneInstaller,
    ) -> None:
        """Test install_aws_provider installs successfully."""
        mock_get_yaml.return_value = "provider yaml"

        installer.install_aws_provider()

        mock_get_yaml.assert_called_once()
        mock_apply.assert_called_once_with("provider yaml")
        mock_wait.assert_called_once()

    @patch.object(CrossplaneInstaller, "_get_aws_provider_yaml")
    def test_install_aws_provider_error(
        self,
        mock_get_yaml: Mock,
        installer: CrossplaneInstaller,
    ) -> None:
        """Test install_aws_provider raises CommandError on failure."""
        mock_get_yaml.side_effect = RuntimeError("Failed")

        with pytest.raises(CommandError, match="Failed to install AWS provider"):
            installer.install_aws_provider()


class TestCrossplaneInstallerConfigureAWS:
    """Tests for AWS provider configuration."""

    @patch.object(CrossplaneInstaller, "_wait_for_provider_config_ready")
    @patch.object(CrossplaneInstaller, "_apply_yaml_resource")
    @patch.object(CrossplaneInstaller, "_get_provider_config_yaml")
    @patch.object(CrossplaneInstaller, "_create_aws_secret")
    def test_configure_aws_provider_with_credentials(
        self,
        mock_create_secret: Mock,
        mock_get_config: Mock,
        mock_apply: Mock,
        mock_wait: Mock,
        installer: CrossplaneInstaller,
    ) -> None:
        """Test configure_aws_provider with provided credentials."""
        mock_get_config.return_value = "config yaml"
        creds = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )

        installer.configure_aws_provider(credentials=creds)

        mock_create_secret.assert_called_once_with(creds)
        mock_apply.assert_called_once()
        mock_wait.assert_called_once()

    @patch.object(CrossplaneInstaller, "_wait_for_provider_config_ready")
    @patch.object(CrossplaneInstaller, "_apply_yaml_resource")
    @patch.object(CrossplaneInstaller, "_get_provider_config_yaml")
    @patch.object(CrossplaneInstaller, "_create_aws_secret")
    def test_configure_aws_provider_without_credentials(
        self,
        mock_create_secret: Mock,
        mock_get_config: Mock,
        mock_apply: Mock,
        mock_wait: Mock,
        installer: CrossplaneInstaller,
        mock_cred_manager: Mock,
    ) -> None:
        """Test configure_aws_provider retrieves credentials."""
        mock_get_config.return_value = "config yaml"
        creds = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )
        mock_cred_manager.get_credentials.return_value = creds

        installer.configure_aws_provider()

        mock_cred_manager.get_credentials.assert_called_once()
        mock_create_secret.assert_called_once()

    @patch.object(CrossplaneInstaller, "_create_aws_secret")
    def test_configure_aws_provider_error(
        self,
        mock_create_secret: Mock,
        installer: CrossplaneInstaller,
    ) -> None:
        """Test configure_aws_provider raises CommandError on failure."""
        creds = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )
        mock_create_secret.side_effect = RuntimeError("Failed")

        with pytest.raises(CommandError, match="Failed to configure AWS provider"):
            installer.configure_aws_provider(credentials=creds)


class TestCrossplaneInstallerUninstall:
    """Tests for Crossplane uninstallation."""

    @patch.object(CrossplaneInstaller, "_delete_resource")
    def test_uninstall_crossplane_success(
        self,
        mock_delete: Mock,
        installer: CrossplaneInstaller,
        mock_helm: Mock,
        mock_kubectl: Mock,
    ) -> None:
        """Test uninstall_crossplane removes all resources."""
        installer.uninstall_crossplane()

        # Should attempt to delete multiple resources
        assert mock_delete.call_count >= 2
        mock_helm.uninstall_release.assert_called_once()

    @patch.object(CrossplaneInstaller, "_delete_resource")
    def test_uninstall_crossplane_continues_on_error(
        self,
        mock_delete: Mock,
        installer: CrossplaneInstaller,
        mock_helm: Mock,
        mock_output: Mock,
    ) -> None:
        """Test uninstall_crossplane continues even if steps fail."""
        mock_delete.side_effect = RuntimeError("Delete failed")

        # Should not raise, just warn
        installer.uninstall_crossplane()

        mock_output.warning.assert_called()


class TestCrossplaneInstallerStatus:
    """Tests for Crossplane status checking."""

    @patch.object(CrossplaneInstaller, "_resource_exists")
    @patch.object(CrossplaneInstaller, "_get_pods_in_namespace")
    def test_get_status_all_ready(
        self,
        mock_get_pods: Mock,
        mock_resource_exists: Mock,
        installer: CrossplaneInstaller,
        mock_helm: Mock,
    ) -> None:
        """Test get_status returns complete status."""
        mock_helm.release_exists.return_value = True
        mock_helm.get_release_status.return_value = {"version": "1.14.0"}
        mock_get_pods.return_value = [
            {"name": "pod1", "ready": True},
            {"name": "pod2", "ready": True},
        ]
        mock_resource_exists.return_value = True

        status = installer.get_status()

        assert status.installed is True
        assert status.ready is True
        assert status.version == "1.14.0"

    def test_get_status_not_installed(
        self,
        installer: CrossplaneInstaller,
        mock_helm: Mock,
    ) -> None:
        """Test get_status when Crossplane not installed."""
        mock_helm.release_exists.return_value = False

        status = installer.get_status()

        assert status.installed is False
        assert status.ready is False


class TestCrossplaneInstallerHelpers:
    """Tests for helper methods."""

    def test_get_crossplane_values(self, installer: CrossplaneInstaller) -> None:
        """Test _get_crossplane_values returns dict."""
        values = installer._get_crossplane_values()

        assert isinstance(values, dict)

    def test_get_aws_provider_yaml(self, installer: CrossplaneInstaller) -> None:
        """Test _get_aws_provider_yaml returns YAML string."""
        yaml_str = installer._get_aws_provider_yaml()

        assert isinstance(yaml_str, str)
        assert "Provider" in yaml_str

    def test_get_provider_config_yaml(self, installer: CrossplaneInstaller) -> None:
        """Test _get_provider_config_yaml returns YAML string."""
        yaml_str = installer._get_provider_config_yaml()

        assert isinstance(yaml_str, str)
        assert "ProviderConfig" in yaml_str

    def test_create_aws_secret(
        self,
        installer: CrossplaneInstaller,
        mock_kubectl: Mock,
    ) -> None:
        """Test _create_aws_secret creates secret."""
        creds = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )

        installer._create_aws_secret(creds)

        mock_kubectl.create_secret.assert_called_once()

    def test_apply_yaml_resource(
        self,
        installer: CrossplaneInstaller,
        mock_kubectl: Mock,
    ) -> None:
        """Test _apply_yaml_resource applies YAML."""
        installer._apply_yaml_resource("yaml content")

        mock_kubectl.apply_yaml.assert_called_once_with("yaml content")

    def test_delete_resource(
        self,
        installer: CrossplaneInstaller,
        mock_kubectl: Mock,
    ) -> None:
        """Test _delete_resource deletes resource."""
        installer._delete_resource("provider", "name", "namespace")

        mock_kubectl.delete_resource.assert_called_once()


class TestCrossplaneInstallerWaitMethods:
    """Tests for wait methods."""

    @patch("mk8.business.crossplane_installer.time.sleep")
    def test_wait_for_crossplane_ready_success(
        self,
        mock_sleep: Mock,
        installer: CrossplaneInstaller,
        mock_kubectl: Mock,
    ) -> None:
        """Test _wait_for_crossplane_ready succeeds when pods ready."""
        mock_kubectl.get_pods.return_value = [
            {"name": "pod1", "ready": True},
            {"name": "pod2", "ready": True},
        ]

        installer._wait_for_crossplane_ready(timeout=10)

        mock_kubectl.get_pods.assert_called()

    @patch("mk8.business.crossplane_installer.time.time")
    @patch("mk8.business.crossplane_installer.time.sleep")
    @patch.object(CrossplaneInstaller, "_get_pods_in_namespace")
    def test_wait_for_crossplane_ready_timeout(
        self,
        mock_get_pods: Mock,
        mock_sleep: Mock,
        mock_time: Mock,
        installer: CrossplaneInstaller,
    ) -> None:
        """Test _wait_for_crossplane_ready raises on timeout."""
        mock_time.side_effect = [0, 200]
        mock_get_pods.return_value = [
            {"name": "pod1", "ready": False},
        ]

        with pytest.raises(CommandError, match="Timeout waiting"):
            installer._wait_for_crossplane_ready(timeout=120)

    @patch("mk8.business.crossplane_installer.time.sleep")
    @patch.object(CrossplaneInstaller, "_get_resource_status")
    @patch.object(CrossplaneInstaller, "_resource_exists")
    def test_wait_for_provider_ready_success(
        self,
        mock_exists: Mock,
        mock_get_status: Mock,
        mock_sleep: Mock,
        installer: CrossplaneInstaller,
    ) -> None:
        """Test _wait_for_provider_ready succeeds."""
        mock_exists.return_value = True
        mock_get_status.return_value = {"status": {"conditions": [{"status": "True"}]}}

        installer._wait_for_provider_ready(timeout=10)

        mock_exists.assert_called()

    @patch("mk8.business.crossplane_installer.time.sleep")
    def test_wait_for_provider_config_ready_success(
        self,
        mock_sleep: Mock,
        installer: CrossplaneInstaller,
        mock_kubectl: Mock,
    ) -> None:
        """Test _wait_for_provider_config_ready succeeds."""
        mock_kubectl.resource_exists.return_value = True

        installer._wait_for_provider_config_ready(timeout=10)

        mock_kubectl.resource_exists.assert_called()


class TestCrossplaneStatus:
    """Tests for CrossplaneStatus dataclass."""

    def test_crossplane_status_defaults(self) -> None:
        """Test CrossplaneStatus has correct defaults."""
        status = CrossplaneStatus()

        assert status.installed is False
        assert status.ready is False
        assert status.pod_count == 0
        assert status.issues == []

    def test_crossplane_status_with_values(self) -> None:
        """Test CrossplaneStatus with custom values."""
        status = CrossplaneStatus(
            installed=True,
            version="1.14.0",
            ready=True,
            pod_count=3,
            ready_pods=3,
        )

        assert status.installed is True
        assert status.version == "1.14.0"
        assert status.ready is True


class TestCrossplaneInstallerVerboseMode:
    """Tests for verbose mode output."""

    @patch.object(CrossplaneInstaller, "_wait_for_crossplane_ready")
    @patch.object(CrossplaneInstaller, "_get_crossplane_values")
    def test_install_crossplane_verbose(
        self,
        mock_get_values: Mock,
        mock_wait: Mock,
        mock_helm: Mock,
        mock_kubectl: Mock,
        mock_cred_manager: Mock,
    ) -> None:
        """Test install_crossplane with verbose output."""
        mock_output = Mock()
        mock_output.verbose = True
        installer = CrossplaneInstaller(
            helm_client=mock_helm,
            kubectl_client=mock_kubectl,
            credential_manager=mock_cred_manager,
            output=mock_output,
        )
        mock_get_values.return_value = {}

        installer.install_crossplane()

        # Verify verbose messages were called
        assert mock_output.info.call_count >= 3

    @patch.object(CrossplaneInstaller, "_wait_for_provider_ready")
    @patch.object(CrossplaneInstaller, "_apply_yaml_resource")
    @patch.object(CrossplaneInstaller, "_get_aws_provider_yaml")
    def test_install_aws_provider_verbose(
        self,
        mock_get_yaml: Mock,
        mock_apply: Mock,
        mock_wait: Mock,
        mock_helm: Mock,
        mock_kubectl: Mock,
        mock_cred_manager: Mock,
    ) -> None:
        """Test install_aws_provider with verbose output."""
        mock_output = Mock()
        mock_output.verbose = True
        installer = CrossplaneInstaller(
            helm_client=mock_helm,
            kubectl_client=mock_kubectl,
            credential_manager=mock_cred_manager,
            output=mock_output,
        )
        mock_get_yaml.return_value = "provider yaml"

        installer.install_aws_provider()

        # Verify verbose message was called
        assert any(
            "Creating Provider" in str(c) for c in mock_output.info.call_args_list
        )

    @patch.object(CrossplaneInstaller, "_wait_for_provider_config_ready")
    @patch.object(CrossplaneInstaller, "_apply_yaml_resource")
    @patch.object(CrossplaneInstaller, "_get_provider_config_yaml")
    @patch.object(CrossplaneInstaller, "_create_aws_secret")
    def test_configure_aws_provider_verbose_with_credentials(
        self,
        mock_create_secret: Mock,
        mock_get_config: Mock,
        mock_apply: Mock,
        mock_wait: Mock,
        mock_helm: Mock,
        mock_kubectl: Mock,
        mock_cred_manager: Mock,
    ) -> None:
        """Test configure_aws_provider with verbose and provided credentials."""
        mock_output = Mock()
        mock_output.verbose = True
        installer = CrossplaneInstaller(
            helm_client=mock_helm,
            kubectl_client=mock_kubectl,
            credential_manager=mock_cred_manager,
            output=mock_output,
        )
        mock_get_config.return_value = "config yaml"
        creds = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )

        installer.configure_aws_provider(credentials=creds)

        # Verify verbose messages were called
        assert any(
            "Creating AWS" in str(c) for c in mock_output.info.call_args_list
        )
        assert any(
            "ProviderConfig" in str(c) for c in mock_output.info.call_args_list
        )

    @patch.object(CrossplaneInstaller, "_wait_for_provider_config_ready")
    @patch.object(CrossplaneInstaller, "_apply_yaml_resource")
    @patch.object(CrossplaneInstaller, "_get_provider_config_yaml")
    @patch.object(CrossplaneInstaller, "_create_aws_secret")
    def test_configure_aws_provider_verbose_without_credentials(
        self,
        mock_create_secret: Mock,
        mock_get_config: Mock,
        mock_apply: Mock,
        mock_wait: Mock,
        mock_helm: Mock,
        mock_kubectl: Mock,
        mock_cred_manager: Mock,
    ) -> None:
        """Test configure_aws_provider with verbose and no credentials."""
        mock_output = Mock()
        mock_output.verbose = True
        installer = CrossplaneInstaller(
            helm_client=mock_helm,
            kubectl_client=mock_kubectl,
            credential_manager=mock_cred_manager,
            output=mock_output,
        )
        mock_get_config.return_value = "config yaml"
        creds = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )
        mock_cred_manager.get_credentials.return_value = creds

        installer.configure_aws_provider()

        # Verify verbose message about retrieving credentials
        assert any(
            "Retrieving AWS" in str(c) for c in mock_output.info.call_args_list
        )
