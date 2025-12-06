"""Verify command implementation."""

import sys

import click

from mk8.business.verification import VerificationManager
from mk8.business.verification_models import VerificationResult
from mk8.cli.output import OutputFormatter
from mk8.core.errors import ExitCode


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def verify(ctx: click.Context, verbose: bool) -> None:
    """Verify mk8 installation and prerequisites."""
    # Use command-level verbose if provided, otherwise use parent verbose
    verbose = verbose or ctx.obj.get("verbose", False)
    output = OutputFormatter(verbose=verbose)
    manager = VerificationManager()

    # Run verification
    result = manager.verify()

    # Display messages
    for message in result.messages:
        output.info(message)

    # Show detailed status if verbose
    if verbose:
        output.info("")
        output.info("Detailed Status:")
        status_summary = result.prerequisite_results.get_status_summary()
        output.info(status_summary)

    # If not verified, show installation instructions and exit with error
    if not result.is_verified():
        output.info("")
        _show_installation_help(output, manager, result)
        sys.exit(_get_exit_code(result))

    # Success
    output.success("Verification complete!")
    sys.exit(ExitCode.SUCCESS.value)


def _show_installation_help(
    output: OutputFormatter,
    manager: VerificationManager,
    result: VerificationResult,
) -> None:
    """Show installation instructions for missing components."""
    if not result.prerequisites_ok:
        missing = result.prerequisite_results.get_missing()
        instructions = manager.get_installation_instructions(missing)
        output.info(instructions)

    if not result.mk8_installed:
        output.info("mk8 Installation:")
        output.info("  Ensure mk8 is installed via pip:")
        output.info("  pip install -e .")
        output.info("  Or check your PATH configuration")


def _get_exit_code(result: VerificationResult) -> int:
    """Determine appropriate exit code based on verification result."""
    if not result.prerequisites_ok:
        return ExitCode.PREREQUISITE_ERROR.value
    return ExitCode.GENERAL_ERROR.value
