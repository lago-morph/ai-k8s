"""Crossplane management commands."""

import sys
import click

from mk8.business.crossplane_installer import CrossplaneInstaller
from mk8.business.credential_manager import CredentialManager
from mk8.cli.output import OutputFormatter
from mk8.core.errors import MK8Error, ExitCode
from mk8.core.logging import setup_logging


@click.group(invoke_without_command=True)
@click.pass_context
def crossplane(ctx: click.Context) -> None:
    """Manage Crossplane on bootstrap cluster."""
    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@crossplane.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--version",
    help="Crossplane version to install (e.g., 1.14.0)",
)
@click.pass_context
def install(ctx: click.Context, verbose: bool, version: str) -> None:
    """
    Install Crossplane on bootstrap cluster.

    Installs Crossplane via Helm, sets up the AWS provider, and configures
    AWS credentials for resource provisioning.

    \b
    Examples:
      # Install latest Crossplane version
      $ mk8 crossplane install

      # Install specific version
      $ mk8 crossplane install --version 1.14.0

      # Install with verbose output
      $ mk8 crossplane install --verbose
    """
    # Setup logging and output
    if verbose or (ctx.obj and ctx.obj.get("verbose", False)):
        verbose = True

    logger = setup_logging(verbose)
    output = OutputFormatter(verbose)

    try:
        # Get AWS credentials
        output.info("Validating AWS credentials...")
        credential_manager = CredentialManager(output=output)
        credentials = credential_manager.get_credentials()

        # Validate credentials
        validation_result = credential_manager.validate_credentials(credentials)
        if not validation_result.success:
            output.error("AWS credential validation failed")
            output.error(validation_result.error_message or "Unknown error")
            suggestions = validation_result.get_suggestions()
            if suggestions:
                output.info("\nSuggestions:")
                for suggestion in suggestions:
                    output.info(f"  • {suggestion}")
            sys.exit(ExitCode.COMMAND_ERROR.value)

        output.success(
            f"Credentials validated (Account: {validation_result.account_id})"
        )

        # Install Crossplane
        installer = CrossplaneInstaller(output=output)
        installer.install_crossplane(version=version)

        # Install AWS provider
        installer.install_aws_provider()

        # Configure AWS provider
        installer.configure_aws_provider(credentials)

        # Show success message
        output.success("\n✓ Crossplane installation complete!")
        output.info("\nNext steps:")
        output.info("  • Check status: mk8 crossplane status")
        output.info("  • View pods: kubectl get pods -n crossplane-system")
        output.info("  • Create AWS resources using Crossplane compositions")

        sys.exit(ExitCode.SUCCESS.value)

    except MK8Error as e:
        output.error(str(e))
        if e.suggestions:
            output.info("\nSuggestions:")
            for suggestion in e.suggestions:
                output.info(f"  • {suggestion}")
        sys.exit(ExitCode.COMMAND_ERROR.value)

    except KeyboardInterrupt:
        output.info("\n\nOperation cancelled by user")
        sys.exit(ExitCode.KEYBOARD_INTERRUPT.value)

    except Exception as e:
        output.error(f"Unexpected error: {str(e)}")
        logger.exception("Unexpected error in crossplane install")
        sys.exit(ExitCode.GENERAL_ERROR.value)


@crossplane.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def uninstall(ctx: click.Context, verbose: bool, yes: bool) -> None:
    """
    Uninstall Crossplane from bootstrap cluster.

    Removes Crossplane, AWS provider, and all associated resources.
    This is a destructive operation that cannot be undone.

    \b
    Examples:
      # Uninstall with confirmation
      $ mk8 crossplane uninstall

      # Uninstall without confirmation
      $ mk8 crossplane uninstall --yes

      # Uninstall with verbose output
      $ mk8 crossplane uninstall --verbose
    """
    # Setup logging and output
    if verbose or (ctx.obj and ctx.obj.get("verbose", False)):
        verbose = True

    logger = setup_logging(verbose)
    output = OutputFormatter(verbose)

    try:
        # Confirmation prompt
        if not yes:
            output.warning(
                "This will remove Crossplane and all AWS provider resources."
            )
            output.warning("This operation cannot be undone.")
            if not click.confirm("\nDo you want to continue?"):
                output.info("Uninstall cancelled")
                sys.exit(ExitCode.SUCCESS.value)

        # Uninstall Crossplane
        installer = CrossplaneInstaller(output=output)
        installer.uninstall_crossplane()

        output.success("\n✓ Crossplane uninstalled successfully")

        sys.exit(ExitCode.SUCCESS.value)

    except MK8Error as e:
        output.error(str(e))
        if e.suggestions:
            output.info("\nSuggestions:")
            for suggestion in e.suggestions:
                output.info(f"  • {suggestion}")
        sys.exit(ExitCode.COMMAND_ERROR.value)

    except KeyboardInterrupt:
        output.info("\n\nOperation cancelled by user")
        sys.exit(ExitCode.KEYBOARD_INTERRUPT.value)

    except Exception as e:
        output.error(f"Unexpected error: {str(e)}")
        logger.exception("Unexpected error in crossplane uninstall")
        sys.exit(ExitCode.GENERAL_ERROR.value)


@crossplane.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def status(ctx: click.Context, verbose: bool) -> None:
    """
    Show Crossplane installation status.

    Displays the current state of Crossplane including version, pod status,
    AWS provider status, and ProviderConfig status.

    \b
    Examples:
      # Check Crossplane status
      $ mk8 crossplane status

      # Check status with verbose output
      $ mk8 crossplane status --verbose
    """
    # Setup logging and output
    if verbose or (ctx.obj and ctx.obj.get("verbose", False)):
        verbose = True

    logger = setup_logging(verbose)
    output = OutputFormatter(verbose)

    try:
        installer = CrossplaneInstaller(output=output)
        crossplane_status = installer.get_status()

        if not crossplane_status.installed:
            output.info("Crossplane: Not installed")
            output.info("\nTo install Crossplane:")
            output.info("  mk8 crossplane install")
            sys.exit(ExitCode.SUCCESS.value)

        # Display status
        output.info(f"Crossplane: Installed")
        if crossplane_status.version:
            output.info(f"Version: {crossplane_status.version}")

        output.info(f"Namespace: {crossplane_status.namespace}")
        output.info(
            f"Status: {'Ready' if crossplane_status.ready else 'Not Ready'}"
        )
        output.info(
            f"Pods: {crossplane_status.ready_pods}/{crossplane_status.pod_count} ready"
        )

        # AWS Provider status
        if crossplane_status.aws_provider_installed:
            provider_status = (
                "Ready" if crossplane_status.aws_provider_ready else "Not Ready"
            )
            output.info(f"AWS Provider: {provider_status}")
        else:
            output.info("AWS Provider: Not installed")

        # ProviderConfig status
        if crossplane_status.provider_config_exists:
            output.info("ProviderConfig: Configured")
        else:
            output.info("ProviderConfig: Not configured")

        # Issues
        if crossplane_status.issues:
            output.warning("\nIssues detected:")
            for issue in crossplane_status.issues:
                output.warning(f"  • {issue}")

            output.info("\nSuggestions:")
            output.info("  • Check pod logs: kubectl logs -n crossplane-system -l app=crossplane")
            output.info("  • Check provider logs: kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=provider-aws")
            output.info("  • Reinstall: mk8 crossplane uninstall && mk8 crossplane install")

        sys.exit(ExitCode.SUCCESS.value)

    except MK8Error as e:
        output.error(str(e))
        if e.suggestions:
            output.info("\nSuggestions:")
            for suggestion in e.suggestions:
                output.info(f"  • {suggestion}")
        sys.exit(ExitCode.COMMAND_ERROR.value)

    except KeyboardInterrupt:
        output.info("\n\nOperation cancelled by user")
        sys.exit(ExitCode.KEYBOARD_INTERRUPT.value)

    except Exception as e:
        output.error(f"Unexpected error: {str(e)}")
        logger.exception("Unexpected error in crossplane status")
        sys.exit(ExitCode.GENERAL_ERROR.value)
