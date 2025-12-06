"""Version command implementation."""

from mk8.core.version import Version


class VersionCommand:
    """Handler for the version command."""

    @staticmethod
    def execute() -> int:
        """
        Execute the version command.

        Displays the current version of mk8.

        Returns:
            Exit code (0 for success)
        """
        version = Version.get_version()
        print(f"mk8 version {version}")
        return 0
