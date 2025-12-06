"""Bootstrap cluster management commands."""

import sys
import click

from mk8.business.bootstrap_manager import BootstrapManager
from mk8.cli.output import OutputFormatter
from mk8.core.errors import MK8Error, ExitCode
from mk8.core.logging import setup_logging


@click.group(invoke_without_command=True)
@click.pass_context
def bootstrap(ctx: click.Context) -> None:
    """Manage local bootstrap cluster."""
    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@bootstrap.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--force-recreate",
    "-f",
    is_flag=True,
    help="Delete existing cluster and create new one",
)
@click.option(
    "--kubernetes-version",
    "-k",
    help="Kubernetes version to use (e.g., v1.28.0)",
)
@click.pass_context
def create(
    ctx: click.Context,
    verbose: bool,
    force_recreate: bool,
    kubernetes_version: str,
) -> None:
    """
    Create the bootstrap cluster.

    Creates a local Kubernetes cluster using kind with the name 'mk8-bootstrap'.
    The cluster is optimized for running infrastructure management tools like
    Crossplane and ArgoCD.

    \b
    Examples:
      # Create bootstrap cluster with default settings
      $ mk8 bootstrap create

      # Create with specific Kubernetes version
      $ mk8 bootstrap create --kubernetes-version v1.28.0

      # Force recreate if cluster already exists
      $ mk8 bootstrap create --force-recreate

      # Create with verbose output
      $ mk8 bootstrap create --verbose
    """
    # Setup logging and output
    if verbose or (ctx.obj and ctx.obj.get("verbose", False)):
        verbose = True

    logger = setup_logging(verbose)
    output = OutputFormatter(verbose)

    try:
        manager = BootstrapManager(output=output)
        manager.create_cluster(
            kubernetes_version=kubernetes_version, force_recreate=force_recreate
        )
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
        logger.exception("Unexpected error in bootstrap create")
        sys.exit(ExitCode.GENERAL_ERROR.value)


@bootstrap.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete(ctx: click.Context, verbose: bool, yes: bool) -> None:
    """
    Delete the bootstrap cluster.

    Removes the local kind cluster and cleans up associated resources including
    kubeconfig entries and Docker containers.

    \b
    Examples:
      # Delete bootstrap cluster (with confirmation)
      $ mk8 bootstrap delete

      # Delete without confirmation
      $ mk8 bootstrap delete --yes

      # Delete with verbose output
      $ mk8 bootstrap delete --verbose
    """
    # Setup logging and output
    if verbose or (ctx.obj and ctx.obj.get("verbose", False)):
        verbose = True

    logger = setup_logging(verbose)
    output = OutputFormatter(verbose)

    try:
        manager = BootstrapManager(output=output)
        manager.delete_cluster(skip_confirmation=yes)
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
        logger.exception("Unexpected error in bootstrap delete")
        sys.exit(ExitCode.GENERAL_ERROR.value)


@bootstrap.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def status(ctx: click.Context, verbose: bool) -> None:
    """
    Show bootstrap cluster status.

    Displays the current state of the bootstrap cluster including node readiness,
    Kubernetes version, and kubectl context information.

    \b
    Examples:
      # Check cluster status
      $ mk8 bootstrap status

      # Check status with verbose output
      $ mk8 bootstrap status --verbose
    """
    # Setup logging and output
    if verbose or (ctx.obj and ctx.obj.get("verbose", False)):
        verbose = True

    logger = setup_logging(verbose)
    output = OutputFormatter(verbose)

    try:
        manager = BootstrapManager(output=output)
        cluster_status = manager.get_status()

        if not cluster_status.exists:
            output.info("Bootstrap cluster: Not found")
            output.info("\nTo create a cluster:")
            output.info("  mk8 bootstrap create")
            sys.exit(ExitCode.SUCCESS.value)

        # Display status
        output.info(f"Bootstrap cluster: {cluster_status.name}")
        output.info(f"Status: {'Ready' if cluster_status.ready else 'Not Ready'}")

        if cluster_status.kubernetes_version:
            output.info(f"Kubernetes version: {cluster_status.kubernetes_version}")

        if cluster_status.context_name:
            output.info(f"Context: {cluster_status.context_name}")

        output.info(f"Nodes: {cluster_status.node_count}")

        if verbose and cluster_status.nodes:
            output.info("\nNode details:")
            for node in cluster_status.nodes:
                output.info(f"  • {node['name']}: {node['status']}")

        if cluster_status.issues:
            output.warning("\nIssues detected:")
            for issue in cluster_status.issues:
                output.warning(f"  • {issue}")

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
        logger.exception("Unexpected error in bootstrap status")
        sys.exit(ExitCode.GENERAL_ERROR.value)
