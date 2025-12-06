"""Credential manager for AWS credentials."""

import sys
import click
from typing import Optional

from mk8.business.credential_models import AWSCredentials, ValidationResult, PromptChoice
from mk8.integrations.file_io import FileIO
from mk8.integrations.aws_client import AWSClient
from mk8.cli.output import OutputFormatter
from mk8.core.errors import ConfigurationError


class CredentialManager:
    """Manages AWS credential acquisition, storage, and validation."""

    def __init__(
        self,
        file_io: FileIO,
        aws_client: AWSClient,
        output: OutputFormatter,
    ):
        """
        Initialize credential manager with dependencies.

        Args:
            file_io: FileIO instance for config file operations
            aws_client: AWSClient instance for credential validation
            output: OutputFormatter instance for user feedback
        """
        self.file_io = file_io
        self.aws_client = aws_client
        self.output = output

    def get_credentials(self) -> AWSCredentials:
        """
        Get AWS credentials using priority order.

        Priority:
        1. Config file (~/.config/mk8)
        2. MK8_* environment variables (auto-save)
        3. AWS_* environment variables (prompt user)
        4. Interactive entry (prompt user)

        Returns:
            AWSCredentials object

        Raises:
            ConfigurationError: If credentials cannot be acquired
            SystemExit: If user chooses to exit
        """
        # 1. Check config file first
        creds = self._read_from_config_file()
        if creds and creds.is_complete():
            return creds

        # 2. Check MK8_* environment variables (auto-save)
        creds = self._read_from_mk8_env_vars()
        if creds and creds.is_complete():
            self.output.info("Credentials configured from MK8_AWS_* environment variables")
            self._save_credentials(creds)
            return creds

        # 3. Check AWS_* environment variables (prompt user)
        creds = self._read_from_aws_env_vars()
        if creds and creds.is_complete():
            choice = self._prompt_for_env_var_usage()
            if choice == PromptChoice.USE_ENV_VARS:
                self._save_credentials(creds)
                self.output.info("Credentials saved from AWS_* environment variables")
                return creds
            elif choice == PromptChoice.ENTER_MANUALLY:
                creds = self._interactive_credential_entry()
                self._save_credentials(creds)
                return creds
            else:  # EXIT
                sys.exit(0)

        # 4. Interactive entry
        choice = self._prompt_for_manual_entry(allow_env_option=False)
        if choice == PromptChoice.ENTER_MANUALLY:
            creds = self._interactive_credential_entry()
            self._save_credentials(creds)
            return creds
        else:  # EXIT
            sys.exit(0)

    def update_credentials(self, force: bool = False) -> AWSCredentials:
        """
        Update credentials via mk8 config command.

        Args:
            force: If True, always prompt even if config exists

        Returns:
            Updated AWSCredentials
        """
        # Read existing credentials for change detection
        old_creds = self._read_from_config_file()

        # Acquire new credentials (skip config file check)
        # Check MK8_* environment variables first
        creds = self._read_from_mk8_env_vars()
        if creds and creds.is_complete():
            self.output.info("Credentials configured from MK8_AWS_* environment variables")
            self._save_credentials(creds)
            self._report_credential_changes(old_creds, creds)
            return creds

        # Check AWS_* environment variables
        creds = self._read_from_aws_env_vars()
        if creds and creds.is_complete():
            choice = self._prompt_for_env_var_usage()
            if choice == PromptChoice.USE_ENV_VARS:
                self._save_credentials(creds)
                self.output.info("Credentials saved from AWS_* environment variables")
                self._report_credential_changes(old_creds, creds)
                return creds
            elif choice == PromptChoice.ENTER_MANUALLY:
                creds = self._interactive_credential_entry()
                self._save_credentials(creds)
                self._report_credential_changes(old_creds, creds)
                return creds
            else:  # EXIT
                sys.exit(0)

        # Interactive entry
        choice = self._prompt_for_manual_entry(allow_env_option=False)
        if choice == PromptChoice.ENTER_MANUALLY:
            creds = self._interactive_credential_entry()
            self._save_credentials(creds)
            self._report_credential_changes(old_creds, creds)
            return creds
        else:  # EXIT
            sys.exit(0)

    def validate_credentials(self, credentials: AWSCredentials) -> ValidationResult:
        """
        Validate credentials by calling AWS STS GetCallerIdentity.

        Args:
            credentials: Credentials to validate

        Returns:
            ValidationResult with success status and account_id or error
        """
        return self.aws_client.validate_credentials(
            credentials.access_key_id,
            credentials.secret_access_key,
            credentials.region,
        )

    def _read_from_config_file(self) -> Optional[AWSCredentials]:
        """
        Read credentials from ~/.config/mk8.

        Returns:
            AWSCredentials if file exists, None otherwise
        """
        config = self.file_io.read_config_file()
        if config is None:
            return None

        creds = AWSCredentials.from_dict(config)
        
        # Check if complete
        if not creds.is_complete():
            missing = []
            if not creds.access_key_id:
                missing.append("AWS_ACCESS_KEY_ID")
            if not creds.secret_access_key:
                missing.append("AWS_SECRET_ACCESS_KEY")
            if not creds.region:
                missing.append("AWS_DEFAULT_REGION")
            
            self.output.warning(
                f"Configuration file is incomplete. Missing: {', '.join(missing)}"
            )
            return None

        return creds

    def _read_from_mk8_env_vars(self) -> Optional[AWSCredentials]:
        """
        Read from MK8_AWS_* environment variables.

        Returns:
            AWSCredentials if all three vars present, None otherwise
        """
        return AWSCredentials.from_env_vars("MK8_AWS")

    def _read_from_aws_env_vars(self) -> Optional[AWSCredentials]:
        """
        Read from standard AWS_* environment variables.

        Returns:
            AWSCredentials if all three vars present, None otherwise
        """
        return AWSCredentials.from_env_vars("AWS")

    def _prompt_for_env_var_usage(self) -> PromptChoice:
        """
        Prompt user about using AWS_* environment variables.

        Returns:
            User's choice
        """
        click.echo("\nAWS credentials detected in environment variables.\n")
        click.echo("Options:")
        click.echo("  1. Use existing AWS_* environment variables and save to config")
        click.echo("  2. Enter credentials manually and save to config")
        click.echo("  3. Exit without configuring\n")
        
        choice = click.prompt("Choice", type=click.Choice(["1", "2", "3"]))
        
        if choice == "1":
            return PromptChoice.USE_ENV_VARS
        elif choice == "2":
            return PromptChoice.ENTER_MANUALLY
        else:
            return PromptChoice.EXIT

    def _prompt_for_manual_entry(self, allow_env_option: bool) -> PromptChoice:
        """
        Prompt user to enter credentials or exit.

        Args:
            allow_env_option: Whether to show option 1 (use env vars)

        Returns:
            User's choice
        """
        click.echo("\nAWS credentials not found in environment variables.\n")
        click.echo("Options:")
        if allow_env_option:
            click.echo("  1. Use existing AWS_* environment variables and save to config (disabled - not all variables set)")
        click.echo("  1. Enter credentials manually and save to config")
        click.echo("  2. Exit without configuring\n")
        
        choice = click.prompt("Choice", type=click.Choice(["1", "2"]))
        
        if choice == "1":
            return PromptChoice.ENTER_MANUALLY
        else:
            return PromptChoice.EXIT

    def _interactive_credential_entry(self) -> AWSCredentials:
        """
        Prompt user to enter credentials interactively.

        Returns:
            AWSCredentials from user input
        """
        click.echo()
        access_key_id = click.prompt("AWS Access Key ID")
        secret_access_key = click.prompt("AWS Secret Access Key", hide_input=True)
        region = click.prompt("AWS Default Region")
        
        return AWSCredentials(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region=region,
        )

    def _save_credentials(self, credentials: AWSCredentials) -> None:
        """
        Save credentials to config file with secure permissions.

        Args:
            credentials: Credentials to save
        """
        self.file_io.write_config_file(credentials.to_dict())

    def _check_credentials_changed(
        self,
        old: Optional[AWSCredentials],
        new: AWSCredentials,
    ) -> bool:
        """
        Check if credentials have changed.

        Args:
            old: Old credentials (may be None)
            new: New credentials

        Returns:
            True if credentials changed, False otherwise
        """
        if old is None:
            return True
        
        return (
            old.access_key_id != new.access_key_id
            or old.secret_access_key != new.secret_access_key
            or old.region != new.region
        )

    def _report_credential_changes(
        self,
        old: Optional[AWSCredentials],
        new: AWSCredentials,
    ) -> None:
        """
        Report credential changes to user.

        Args:
            old: Old credentials (may be None)
            new: New credentials
        """
        if self._check_credentials_changed(old, new):
            self.output.info("Credentials have been updated")
        else:
            self.output.info("Credentials are already up to date")
