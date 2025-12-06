"""Main CLI entry point for mk8."""

import sys
import click
import functools
from dataclasses import dataclass
import logging

from mk8.core.version import Version
from mk8.core.errors import MK8Error, ExitCode
from mk8.core.logging import setup_logging
from mk8.cli.output import OutputFormatter
from mk8.cli.commands.version import VersionCommand


@dataclass
class CommandContext:
    """Context shared across command execution."""

    verbose: bool
    logger: logging.Logger
    output: OutputFormatter


def safe_command_execution(func):  # type: ignore[no-untyped-def]
    """Decorator for safe command execution with error handling."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            click.echo("\n\nOperation cancelled by user.", err=True)
            sys.exit(ExitCode.KEYBOARD_INTERRUPT.value)
        except MK8Error as e:
            # Our custom errors - format nicely
            click.echo(e.format_error(), err=True)
            sys.exit(ExitCode.COMMAND_ERROR.value)
        except click.ClickException:
            # Click's exceptions - let Click handle them
            raise
        except Exception as e:
            # Unexpected errors - show and suggest bug report
            click.echo(f"Error: Unexpected error occurred: {str(e)}", err=True)
            click.echo("\nThis may be a bug. Please report it at:", err=True)
            click.echo("https://github.com/your-org/mk8/issues", err=True)
            sys.exit(ExitCode.GENERAL_ERROR.value)

    return wrapper


@click.group(
    invoke_without_command=True,
    context_settings={
        "help_option_names": ["-h", "--help"],
        "allow_interspersed_args": True,
    },
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, version: bool) -> None:
    """mk8 - Manage Kubernetes infrastructure on AWS."""
    # Handle --version flag at top level
    if version:
        click.echo(f"mk8 version {Version.get_version()}")
        ctx.exit(0)

    # Store context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["logger"] = setup_logging(verbose)
    ctx.obj["output"] = OutputFormatter(verbose)

    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def version(ctx: click.Context, verbose: bool) -> None:
    """Show version information."""
    # Use command-level verbose if provided, otherwise use parent verbose
    if verbose or ctx.obj.get("verbose", False):
        ctx.obj["verbose"] = True
        ctx.obj["logger"] = setup_logging(True)
        ctx.obj["output"] = OutputFormatter(True)
    exit_code = VersionCommand.execute()
    ctx.exit(exit_code)


@cli.group(invoke_without_command=True)
@click.pass_context
def bootstrap(ctx: click.Context) -> None:
    """Manage local bootstrap cluster."""
    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Configure AWS credentials."""
    # Placeholder implementation
    output = ctx.obj.get("output", OutputFormatter())
    output.info("Config command - placeholder implementation")
    output.info("This will be implemented in the aws-credentials-management spec")


def main() -> int:
    """
    Main entry point for the mk8 CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        cli(obj={})
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0
    except Exception:
        return ExitCode.GENERAL_ERROR.value
