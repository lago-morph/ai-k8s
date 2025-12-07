"""Tests for CredentialManager business logic."""

import pytest
from unittest.mock import Mock, patch, call
from hypothesis import given, strategies as st

from mk8.business.credential_manager import CredentialManager
from mk8.business.credential_models import (
    AWSCredentials,
    ValidationResult,
    PromptChoice,
)
from mk8.core.errors import ConfigurationError


@pytest.fixture
def mock_file_io() -> Mock:
    """Create mock FileIO."""
    return Mock()


@pytest.fixture
def mock_aws_client() -> Mock:
    """Create mock AWSClient."""
    return Mock()


@pytest.fixture
def mock_output() -> Mock:
    """Create mock OutputFormatter."""
    return Mock()


@pytest.fixture
def credential_manager(
    mock_file_io: Mock, mock_aws_client: Mock, mock_output: Mock
) -> CredentialManager:
    """Create CredentialManager with mocked dependencies."""
    return CredentialManager(mock_file_io, mock_aws_client, mock_output)


class TestCredentialManagerGetCredentials:
    """Tests for CredentialManager.get_credentials()."""

    def test_uses_complete_config_file_first(
        self, credential_manager: CredentialManager, mock_file_io: Mock
    ) -> None:
        """Test get_credentials uses config file when complete."""
        mock_file_io.read_config_file.return_value = {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "AWS_SECRET_ACCESS_KEY": "secret",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        creds = credential_manager.get_credentials()

        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert creds.secret_access_key == "secret"
        assert creds.region == "us-east-1"
        mock_file_io.read_config_file.assert_called_once()

    def test_skips_incomplete_config_file(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test get_credentials skips incomplete config file."""
        mock_file_io.read_config_file.return_value = {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            # Missing secret and region
        }

        # Set MK8 env vars so we don't prompt
        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager.get_credentials()

        # Should use MK8 env vars instead
        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        mock_output.warning.assert_called()

    def test_auto_saves_mk8_env_vars(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test get_credentials auto-saves MK8_* environment variables."""
        mock_file_io.read_config_file.return_value = None

        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager.get_credentials()

        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        mock_file_io.write_config_file.assert_called_once()
        mock_output.info.assert_called()

    def test_skips_partial_mk8_env_vars(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test get_credentials skips partial MK8_* environment variables."""
        mock_file_io.read_config_file.return_value = None

        # Only set 2 out of 3 MK8 vars
        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "secret")
        # Missing MK8_AWS_DEFAULT_REGION

        # Set AWS vars so we can test the prompt
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        with patch.object(
            credential_manager,
            "_prompt_for_env_var_usage",
            return_value=PromptChoice.USE_ENV_VARS,
        ):
            creds = credential_manager.get_credentials()

        # Should proceed to AWS env vars
        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"

    def test_prompts_for_aws_env_vars(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test get_credentials prompts when AWS_* vars are set."""
        mock_file_io.read_config_file.return_value = None

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        with patch.object(
            credential_manager,
            "_prompt_for_env_var_usage",
            return_value=PromptChoice.USE_ENV_VARS,
        ):
            creds = credential_manager.get_credentials()

        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        mock_file_io.write_config_file.assert_called_once()

    def test_prompts_for_manual_entry_when_no_env_vars(
        self, credential_manager: CredentialManager, mock_file_io: Mock
    ) -> None:
        """Test get_credentials prompts for manual entry when no env vars."""
        mock_file_io.read_config_file.return_value = None

        manual_creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        with patch.object(
            credential_manager,
            "_prompt_for_manual_entry",
            return_value=PromptChoice.ENTER_MANUALLY,
        ):
            with patch.object(
                credential_manager,
                "_interactive_credential_entry",
                return_value=manual_creds,
            ):
                creds = credential_manager.get_credentials()

        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        mock_file_io.write_config_file.assert_called_once()

    def test_exits_when_user_chooses_exit(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test get_credentials exits when user chooses exit."""
        mock_file_io.read_config_file.return_value = None

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        with patch.object(
            credential_manager,
            "_prompt_for_env_var_usage",
            return_value=PromptChoice.EXIT,
        ):
            with pytest.raises(SystemExit):
                credential_manager.get_credentials()


class TestCredentialManagerUpdateCredentials:
    """Tests for CredentialManager.update_credentials()."""

    def test_update_credentials_overwrites_existing(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test update_credentials overwrites existing config."""
        mock_file_io.read_config_file.return_value = {
            "AWS_ACCESS_KEY_ID": "OLD_KEY",
            "AWS_SECRET_ACCESS_KEY": "old_secret",
            "AWS_DEFAULT_REGION": "us-west-2",
        }

        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "NEW_KEY")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "new_secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager.update_credentials()

        assert creds.access_key_id == "NEW_KEY"
        mock_file_io.write_config_file.assert_called_once()

    def test_update_credentials_detects_changes(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test update_credentials detects credential changes."""
        mock_file_io.read_config_file.return_value = {
            "AWS_ACCESS_KEY_ID": "OLD_KEY",
            "AWS_SECRET_ACCESS_KEY": "old_secret",
            "AWS_DEFAULT_REGION": "us-west-2",
        }

        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "NEW_KEY")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "new_secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        credential_manager.update_credentials()

        # Should inform user of change
        assert any(
            "updated" in str(c).lower() or "changed" in str(c).lower()
            for c in mock_output.info.call_args_list
        )

    def test_update_credentials_reports_no_change(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test update_credentials reports when credentials unchanged."""
        mock_file_io.read_config_file.return_value = {
            "AWS_ACCESS_KEY_ID": "SAME_KEY",
            "AWS_SECRET_ACCESS_KEY": "same_secret",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "SAME_KEY")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "same_secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        credential_manager.update_credentials()

        # Should inform user no change
        assert any(
            "up to date" in str(c).lower() or "unchanged" in str(c).lower()
            for c in mock_output.info.call_args_list
        )


class TestCredentialManagerValidateCredentials:
    """Tests for CredentialManager.validate_credentials()."""

    def test_validate_credentials_calls_aws_client(
        self, credential_manager: CredentialManager, mock_aws_client: Mock
    ) -> None:
        """Test validate_credentials calls AWS client."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="secret",
            region="us-east-1",
        )

        mock_aws_client.validate_credentials.return_value = ValidationResult(
            success=True,
            account_id="123456789012",
        )

        result = credential_manager.validate_credentials(creds)

        assert result.success is True
        assert result.account_id == "123456789012"
        mock_aws_client.validate_credentials.assert_called_once_with(
            "AKIAIOSFODNN7EXAMPLE",
            "secret",
            "us-east-1",
        )


class TestCredentialManagerInteractiveEntry:
    """Tests for CredentialManager._interactive_credential_entry()."""

    @patch("mk8.business.credential_manager.click.prompt")
    def test_interactive_entry_prompts_for_all_fields(
        self, mock_prompt: Mock, credential_manager: CredentialManager
    ) -> None:
        """Test interactive entry prompts for all three fields."""
        mock_prompt.side_effect = [
            "AKIAIOSFODNN7EXAMPLE",
            "secret",
            "us-east-1",
        ]

        creds = credential_manager._interactive_credential_entry()

        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert creds.secret_access_key == "secret"
        assert creds.region == "us-east-1"
        assert mock_prompt.call_count == 3

    @patch("mk8.business.credential_manager.click.prompt")
    def test_interactive_entry_hides_secret_key(
        self, mock_prompt: Mock, credential_manager: CredentialManager
    ) -> None:
        """Test interactive entry hides secret access key input."""
        mock_prompt.side_effect = [
            "AKIAIOSFODNN7EXAMPLE",
            "secret",
            "us-east-1",
        ]

        credential_manager._interactive_credential_entry()

        # Second call should have hide_input=True
        calls = mock_prompt.call_args_list
        assert calls[1][1]["hide_input"] is True


class TestCredentialManagerProperties:
    """Property-based tests for CredentialManager."""

    def test_property_credential_source_priority(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Property: Config file should be checked before environment variables."""
        # Set both config file and env vars
        mock_file_io.read_config_file.return_value = {
            "AWS_ACCESS_KEY_ID": "FROM_FILE",
            "AWS_SECRET_ACCESS_KEY": "from_file",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "FROM_ENV")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "from_env")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-west-2")

        creds = credential_manager.get_credentials()

        # Should use config file, not env vars
        assert creds.access_key_id == "FROM_FILE"
        assert creds.region == "us-east-1"

    def test_property_mk8_vars_take_precedence_over_aws_vars(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Property: MK8_* vars should take precedence over AWS_* vars."""
        mock_file_io.read_config_file.return_value = None

        # Set both MK8 and AWS vars
        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "FROM_MK8")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "from_mk8")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "FROM_AWS")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "from_aws")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")

        creds = credential_manager.get_credentials()

        # Should use MK8 vars
        assert creds.access_key_id == "FROM_MK8"
        assert creds.region == "us-east-1"

    def test_property_incomplete_credentials_reported(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Property: Incomplete config file should report missing credentials."""
        mock_file_io.read_config_file.return_value = {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            # Missing secret and region
        }

        # Set MK8 vars so we don't prompt
        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        credential_manager.get_credentials()

        # Should warn about incomplete config
        warning_calls = [str(c) for c in mock_output.warning.call_args_list]
        assert any(
            "incomplete" in c.lower() or "missing" in c.lower() for c in warning_calls
        )

    def test_property_credentials_always_saved_after_acquisition(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Property: Credentials should be saved after acquisition from env vars."""
        mock_file_io.read_config_file.return_value = None

        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        credential_manager.get_credentials()

        # Should save to file
        mock_file_io.write_config_file.assert_called_once()
        saved_config = mock_file_io.write_config_file.call_args[0][0]
        assert saved_config["AWS_ACCESS_KEY_ID"] == "AKIAIOSFODNN7EXAMPLE"


class TestCredentialManagerUpdateCredentialsAdvanced:
    """Advanced tests for CredentialManager.update_credentials()."""

    def test_update_from_mk8_env_vars(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test update_credentials uses MK8_* env vars."""
        mock_file_io.read_config_file.return_value = {
            "AWS_ACCESS_KEY_ID": "OLD_KEY",
            "AWS_SECRET_ACCESS_KEY": "old_secret",
            "AWS_DEFAULT_REGION": "us-west-1",
        }

        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "NEW_KEY")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "new_secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager.update_credentials()

        assert creds.access_key_id == "NEW_KEY"
        assert creds.secret_access_key == "new_secret"
        assert creds.region == "us-east-1"
        mock_file_io.write_config_file.assert_called_once()
        mock_output.info.assert_any_call(
            "Credentials configured from MK8_AWS_* environment variables"
        )
        mock_output.info.assert_any_call("Credentials have been updated")

    def test_update_with_same_credentials(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test update_credentials reports no change when credentials same."""
        mock_file_io.read_config_file.return_value = {
            "AWS_ACCESS_KEY_ID": "SAME_KEY",
            "AWS_SECRET_ACCESS_KEY": "same_secret",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "SAME_KEY")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "same_secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager.update_credentials()

        assert creds.access_key_id == "SAME_KEY"
        mock_output.info.assert_any_call("Credentials are already up to date")

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_update_from_aws_env_vars_use_them(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test update_credentials with AWS_* env vars and user chooses to use them."""
        mock_file_io.read_config_file.return_value = None
        mock_prompt.return_value = "1"  # Use env vars

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AWS_KEY")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager.update_credentials()

        assert creds.access_key_id == "AWS_KEY"
        mock_file_io.write_config_file.assert_called_once()
        mock_output.info.assert_any_call(
            "Credentials saved from AWS_* environment variables"
        )

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_update_from_aws_env_vars_enter_manually(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test update_credentials with AWS_* env vars but user enters manually."""
        mock_file_io.read_config_file.return_value = None
        # First prompt: choice, then manual entry prompts
        mock_prompt.side_effect = [
            "2",  # Enter manually
            "MANUAL_KEY",
            "manual_secret",
            "us-west-2",
        ]

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AWS_KEY")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager.update_credentials()

        assert creds.access_key_id == "MANUAL_KEY"
        assert creds.secret_access_key == "manual_secret"
        assert creds.region == "us-west-2"
        mock_file_io.write_config_file.assert_called_once()

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    @patch("mk8.business.credential_manager.sys.exit")
    def test_update_from_aws_env_vars_exit(
        self,
        mock_exit: Mock,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test update_credentials with AWS_* env vars and user exits."""
        mock_file_io.read_config_file.return_value = None
        mock_prompt.return_value = "3"  # Exit

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AWS_KEY")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        credential_manager.update_credentials()

        mock_exit.assert_called_with(0)

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_update_interactive_entry(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
    ) -> None:
        """Test update_credentials with interactive entry."""
        mock_file_io.read_config_file.return_value = None
        # First prompt: choice, then manual entry prompts
        mock_prompt.side_effect = [
            "1",  # Enter manually
            "INTERACTIVE_KEY",
            "interactive_secret",
            "eu-west-1",
        ]

        creds = credential_manager.update_credentials()

        assert creds.access_key_id == "INTERACTIVE_KEY"
        assert creds.secret_access_key == "interactive_secret"
        assert creds.region == "eu-west-1"
        mock_file_io.write_config_file.assert_called_once()

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    @patch("mk8.business.credential_manager.sys.exit")
    def test_update_interactive_exit(
        self,
        mock_exit: Mock,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
    ) -> None:
        """Test update_credentials with interactive exit."""
        mock_file_io.read_config_file.return_value = None
        mock_prompt.return_value = "2"  # Exit

        credential_manager.update_credentials()

        mock_exit.assert_called_with(0)


class TestCredentialManagerGetCredentialsAdvanced:
    """Advanced tests for CredentialManager.get_credentials()."""

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_get_from_aws_env_vars_use_them(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        mock_output: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test get_credentials with AWS_* env vars and user chooses to use them."""
        mock_file_io.read_config_file.return_value = None
        mock_prompt.return_value = "1"  # Use env vars

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AWS_KEY")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager.get_credentials()

        assert creds.access_key_id == "AWS_KEY"
        mock_file_io.write_config_file.assert_called_once()
        mock_output.info.assert_called_with(
            "Credentials saved from AWS_* environment variables"
        )

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_get_from_aws_env_vars_enter_manually(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test get_credentials with AWS_* env vars but user enters manually."""
        mock_file_io.read_config_file.return_value = None
        # First prompt: choice, then manual entry prompts
        mock_prompt.side_effect = [
            "2",  # Enter manually
            "MANUAL_KEY",
            "manual_secret",
            "us-west-2",
        ]

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AWS_KEY")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager.get_credentials()

        assert creds.access_key_id == "MANUAL_KEY"
        assert creds.secret_access_key == "manual_secret"
        assert creds.region == "us-west-2"

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    @patch("mk8.business.credential_manager.sys.exit")
    def test_get_from_aws_env_vars_exit(
        self,
        mock_exit: Mock,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test get_credentials with AWS_* env vars and user exits."""
        mock_file_io.read_config_file.return_value = None
        mock_prompt.return_value = "3"  # Exit

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AWS_KEY")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        credential_manager.get_credentials()

        mock_exit.assert_called_with(0)

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_get_interactive_entry(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
    ) -> None:
        """Test get_credentials with interactive entry."""
        mock_file_io.read_config_file.return_value = None
        # First prompt: choice, then manual entry prompts
        mock_prompt.side_effect = [
            "1",  # Enter manually
            "INTERACTIVE_KEY",
            "interactive_secret",
            "eu-west-1",
        ]

        creds = credential_manager.get_credentials()

        assert creds.access_key_id == "INTERACTIVE_KEY"
        assert creds.secret_access_key == "interactive_secret"
        assert creds.region == "eu-west-1"

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    @patch("mk8.business.credential_manager.sys.exit")
    def test_get_interactive_exit(
        self,
        mock_exit: Mock,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
    ) -> None:
        """Test get_credentials with interactive exit."""
        mock_file_io.read_config_file.return_value = None
        mock_prompt.return_value = "2"  # Exit

        credential_manager.get_credentials()

        mock_exit.assert_called_with(0)


class TestCredentialManagerValidateCredentialsAdvanced:
    """Advanced tests for CredentialManager.validate_credentials()."""

    def test_validate_calls_aws_client(
        self,
        credential_manager: CredentialManager,
        mock_aws_client: Mock,
    ) -> None:
        """Test validate_credentials calls AWS client."""
        mock_aws_client.validate_credentials.return_value = ValidationResult(
            success=True, account_id="123456789012"
        )

        creds = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = credential_manager.validate_credentials(creds)

        assert result.success is True
        assert result.account_id == "123456789012"
        mock_aws_client.validate_credentials.assert_called_once_with(
            "AKIATEST", "secret", "us-east-1"
        )


class TestCredentialManagerPrivateMethods:
    """Tests for CredentialManager private methods."""

    def test_check_credentials_changed_returns_true_when_old_none(
        self, credential_manager: CredentialManager
    ) -> None:
        """Test _check_credentials_changed returns True when old is None."""
        new_creds = AWSCredentials(
            access_key_id="KEY",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = credential_manager._check_credentials_changed(None, new_creds)

        assert result is True

    def test_check_credentials_changed_returns_true_when_access_key_differs(
        self, credential_manager: CredentialManager
    ) -> None:
        """Test _check_credentials_changed returns True when access key differs."""
        old_creds = AWSCredentials(
            access_key_id="OLD_KEY",
            secret_access_key="secret",
            region="us-east-1",
        )
        new_creds = AWSCredentials(
            access_key_id="NEW_KEY",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = credential_manager._check_credentials_changed(old_creds, new_creds)

        assert result is True

    def test_check_credentials_changed_returns_true_when_secret_differs(
        self, credential_manager: CredentialManager
    ) -> None:
        """Test _check_credentials_changed returns True when secret differs."""
        old_creds = AWSCredentials(
            access_key_id="KEY",
            secret_access_key="old_secret",
            region="us-east-1",
        )
        new_creds = AWSCredentials(
            access_key_id="KEY",
            secret_access_key="new_secret",
            region="us-east-1",
        )

        result = credential_manager._check_credentials_changed(old_creds, new_creds)

        assert result is True

    def test_check_credentials_changed_returns_true_when_region_differs(
        self, credential_manager: CredentialManager
    ) -> None:
        """Test _check_credentials_changed returns True when region differs."""
        old_creds = AWSCredentials(
            access_key_id="KEY",
            secret_access_key="secret",
            region="us-east-1",
        )
        new_creds = AWSCredentials(
            access_key_id="KEY",
            secret_access_key="secret",
            region="us-west-2",
        )

        result = credential_manager._check_credentials_changed(old_creds, new_creds)

        assert result is True

    def test_check_credentials_changed_returns_false_when_same(
        self, credential_manager: CredentialManager
    ) -> None:
        """Test _check_credentials_changed returns False when credentials same."""
        old_creds = AWSCredentials(
            access_key_id="KEY",
            secret_access_key="secret",
            region="us-east-1",
        )
        new_creds = AWSCredentials(
            access_key_id="KEY",
            secret_access_key="secret",
            region="us-east-1",
        )

        result = credential_manager._check_credentials_changed(old_creds, new_creds)

        assert result is False

    def test_save_credentials_calls_file_io(
        self,
        credential_manager: CredentialManager,
        mock_file_io: Mock,
    ) -> None:
        """Test _save_credentials calls file_io.write_config_file."""
        creds = AWSCredentials(
            access_key_id="KEY",
            secret_access_key="secret",
            region="us-east-1",
        )

        credential_manager._save_credentials(creds)

        mock_file_io.write_config_file.assert_called_once_with(creds.to_dict())

    def test_read_from_mk8_env_vars(
        self,
        credential_manager: CredentialManager,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test _read_from_mk8_env_vars reads MK8_AWS_* variables."""
        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "KEY")
        monkeypatch.setenv("MK8_AWS_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager._read_from_mk8_env_vars()

        assert creds is not None
        assert creds.access_key_id == "KEY"
        assert creds.secret_access_key == "secret"
        assert creds.region == "us-east-1"

    def test_read_from_aws_env_vars(
        self,
        credential_manager: CredentialManager,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test _read_from_aws_env_vars reads AWS_* variables."""
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "KEY")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        creds = credential_manager._read_from_aws_env_vars()

        assert creds is not None
        assert creds.access_key_id == "KEY"
        assert creds.secret_access_key == "secret"
        assert creds.region == "us-east-1"

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_prompt_for_env_var_usage_option_1(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
    ) -> None:
        """Test _prompt_for_env_var_usage returns USE_ENV_VARS for option 1."""
        mock_prompt.return_value = "1"

        result = credential_manager._prompt_for_env_var_usage()

        assert result == PromptChoice.USE_ENV_VARS

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_prompt_for_env_var_usage_option_2(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
    ) -> None:
        """Test _prompt_for_env_var_usage returns ENTER_MANUALLY for option 2."""
        mock_prompt.return_value = "2"

        result = credential_manager._prompt_for_env_var_usage()

        assert result == PromptChoice.ENTER_MANUALLY

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_prompt_for_env_var_usage_option_3(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
    ) -> None:
        """Test _prompt_for_env_var_usage returns EXIT for option 3."""
        mock_prompt.return_value = "3"

        result = credential_manager._prompt_for_env_var_usage()

        assert result == PromptChoice.EXIT

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_prompt_for_manual_entry_option_1(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
    ) -> None:
        """Test _prompt_for_manual_entry returns ENTER_MANUALLY for option 1."""
        mock_prompt.return_value = "1"

        result = credential_manager._prompt_for_manual_entry(allow_env_option=False)

        assert result == PromptChoice.ENTER_MANUALLY

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_prompt_for_manual_entry_option_2(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
    ) -> None:
        """Test _prompt_for_manual_entry returns EXIT for option 2."""
        mock_prompt.return_value = "2"

        result = credential_manager._prompt_for_manual_entry(allow_env_option=False)

        assert result == PromptChoice.EXIT

    @patch("mk8.business.credential_manager.click.prompt")
    @patch("mk8.business.credential_manager.click.echo")
    def test_interactive_credential_entry(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        credential_manager: CredentialManager,
    ) -> None:
        """Test _interactive_credential_entry prompts for credentials."""
        mock_prompt.side_effect = ["KEY", "secret", "us-east-1"]

        creds = credential_manager._interactive_credential_entry()

        assert creds.access_key_id == "KEY"
        assert creds.secret_access_key == "secret"
        assert creds.region == "us-east-1"
        assert mock_prompt.call_count == 3
