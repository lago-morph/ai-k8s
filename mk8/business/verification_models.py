"""Verification result data models."""

from dataclasses import dataclass
from typing import List

from mk8.integrations.prerequisite_models import PrerequisiteResults


@dataclass
class VerificationResult:
    """Result of installation verification."""

    mk8_installed: bool
    prerequisites_ok: bool
    prerequisite_results: PrerequisiteResults
    messages: List[str]

    def is_verified(self) -> bool:
        """
        Check if fully verified.

        Returns:
            True if mk8 is installed and all prerequisites are satisfied
        """
        return self.mk8_installed and self.prerequisites_ok
