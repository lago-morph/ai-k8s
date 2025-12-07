"""Config command for AWS credentials management."""

import sys
import click

from mk8.business.credential_manager import CredentialManager
from mk8.business.crossplane_manager import CrossplaneManager
from mk8.integrations.file_io import FileIO
from mk8.integrations.aws_client import AWSClient
from mk8.integrations.kubectl_client import KubectlClient
from mk8.cli.output import OutputFormatter
from mk8.core.errors import ConfigurationError, ExitCode
from mk8.core.logging import setup_logging


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def config(ctx: click.Context, verbose: bool) -> None:
    """
    Configure AWS credentials for mk8.

    This command configures AWS credentials used by mk8 for provisioning
    infrastructure. Credentials are stored in ~/.config/mk8 and automatically
    synchronized with Crossplane in managed clusters.

    \b
    Credential Sources (in priority order):
      1. MK8_AWS_* environment variables (auto-configured)
      2. AWS_* environment variables (with user prompt)
      3. Interactive entry (manual input)

    \b
    Environment Variables:
      MK8_AWS_ACCESS_KEY_ID       AWS access key ID (auto-configured)
      MK8_AWS_SECRET_ACCESS_KEY   AWS secret access key (auto-configured)
      MK8_AWS_DEFAULT_REGION      AWS default region (auto-configured)

      AWS_ACCESS_KEY_ID           Standard AWS access key ID (prompted)
      AWS_SECRET_ACCESS_KEY       Standard AWS secret access key (prompted)
      AWS_DEFAULT_REGION          Standard AWS default region (prompted)

    \b
    Examples:
      # Configure credentials interactively
      $ mk8 config

      # Auto-configure from MK8_* environment variables
      $ export MK8_AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
      $ export MK8_AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
      $ export MK8_AWS_DEFAULT_REGION=us-east-1
      $ mk8 config

      # Configure with verbose output
      $ mk8 config --verbose

    \b
    Notes:
      - Credentials are stored in ~/.config/mk8 with secure permissions (0600)
      - If a Crossplane cluster exists, credentials are automatically synced
      - Credentials are validated using AWS STS GetCallerIdentity
      - Running this command will overwrite existing credentials
    """
    # Setup logging and output
    if ctx.obj and ctx.obj.get("verbose", False):
        verbose = True

    logger = setup_logging(verbose)
    output = OutputFormatter(verbose)

    try:
        # Initialize dependencies
        file_io = FileIO()
        aws_client = AWSClient()
        kubectl_client = KubectlClient()

        # Initialize managers
        cred_manager = CredentialManager(file_io, aws_client, output)
        crossplane_manager = CrossplaneManager(kubectl_client, aws_client, output)

        # Update credentials
        output.info("Configuring AWS credentials...")
        credentials = cred_manager.update_credentials()

        # Sync to Crossplane if cluster exists
        sync_result = crossplane_manager.sync_credentials(credentials)

        # Report results
        if sync_result.cluster_exists:
            if sync_result.secret_updated:
                output.success("Credentials synchronized to Crossplane")
            if sync_result.validation_result:
                if sync_result.validation_result.success:
                    output.success(
                        f"✓ Credentials validated "
                        f"(Account: {sync_result.validation_result.account_id})"
                    )
                else:
                    output.warning(
                        f"⚠ Credential validation failed: "
                        f"{sync_result.validation_result.error_message}"
                    )

        output.success("✓ Configuration complete")
        sys.exit(ExitCode.SUCCESS.value)

    except ConfigurationError as e:
        output.error(str(e))
        if e.suggestions:
            output.info("\nSuggestions:")
            for suggestion in e.suggestions:
                output.info(f"  • {suggestion}")
        sys.exit(ExitCode.CONFIGURATION_ERROR.value)

    except KeyboardInterrupt:
        output.info("\n\nOperation cancelled by user")
        sys.exit(ExitCode.KEYBOARD_INTERRUPT.value)

    except Exception as e:
        output.error(f"Unexpected error: {str(e)}")
        logger.exception("Unexpected error in config command")
        sys.exit(ExitCode.GENERAL_ERROR.value)
