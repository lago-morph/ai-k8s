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
    """Configure AWS credentials for mk8."""
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
                        f"✓ Credentials validated (Account: {sync_result.validation_result.account_id})"
                    )
                else:
                    output.warning(
                        f"⚠ Credential validation failed: {sync_result.validation_result.error_message}"
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
