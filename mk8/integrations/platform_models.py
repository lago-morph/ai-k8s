"""Platform detection data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PlatformInfo:
    """Information about the platform."""

    os: str  # "linux", "darwin", "windows", "wsl"
    distribution: Optional[str]  # "ubuntu", "debian", "fedora", etc.
    version: Optional[str]  # OS/distribution version
    architecture: str  # "x86_64", "arm64", etc.
    supported: bool  # Whether platform is supported

    def is_linux(self) -> bool:
        """
        Check if Linux-based platform.

        Returns:
            True if os is "linux" or "wsl", False otherwise
        """
        return self.os in ("linux", "wsl")

    def is_wsl(self) -> bool:
        """
        Check if WSL platform.

        Returns:
            True if os is "wsl", False otherwise
        """
        return self.os == "wsl"
