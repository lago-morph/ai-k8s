"""Version information for mk8."""

from typing import Dict, Any, Optional


class Version:
    """Version information using semantic versioning."""

    #C This should read from project.version of /pyproject.toml, and should not be hard-coded
    MAJOR: int = 0
    MINOR: int = 1
    PATCH: int = 0
    PRERELEASE: Optional[str] = None
    BUILD: Optional[str] = None

    @classmethod
    def get_version(cls) -> str:
        """
        Get the semantic version string.

        Returns:
            Version string in format MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
        """
        version = f"{cls.MAJOR}.{cls.MINOR}.{cls.PATCH}"

        if cls.PRERELEASE:
            version += f"-{cls.PRERELEASE}"

        if cls.BUILD:
            version += f"+{cls.BUILD}"

        return version

    @classmethod
    def get_version_info(cls) -> Dict[str, Any]:
        """
        Get detailed version information.

        Returns:
            Dictionary containing version components and metadata
        """
        return {
            "version": cls.get_version(),
            "major": cls.MAJOR,
            "minor": cls.MINOR,
            "patch": cls.PATCH,
            "prerelease": cls.PRERELEASE,
            "build": cls.BUILD,
        }
