"""Verification of mk8 installation and prerequisites."""

import shutil
from typing import List

from mk8.business.verification_models import VerificationResult
from mk8.integrations.prerequisites import PrerequisiteChecker


class VerificationManager:
    """Verifies mk8 installation and prerequisites."""

    # Basic installation instructions for Linux
    INSTALLATION_INSTRUCTIONS = {
        "docker": (
            "Docker:\n"
            "  Install Docker: "
            "https://docs.docker.com/engine/install/\n"
            "  After installation, start the Docker daemon"
        ),
        "kind": (
            "kind:\n"
            "  curl -Lo ./kind "
            "https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64\n"
            "  chmod +x ./kind\n"
            "  sudo mv ./kind /usr/local/bin/kind"
        ),
        "kubectl": (
            "kubectl:\n"
            "  Install kubectl: "
            "https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/"
        ),
    }

    def verify(self) -> VerificationResult:
        """
        Perform installation verification.

        Returns:
            VerificationResult with complete verification status
        """
        messages = []

        # Check if mk8 is installed
        mk8_installed = self.verify_mk8_installed()
        if mk8_installed:
            messages.append("✓ mk8 is installed")
        else:
            messages.append("✗ mk8 is not in PATH")

        # Check prerequisites
        checker = PrerequisiteChecker()
        prerequisite_results = checker.check_all()
        prerequisites_ok = prerequisite_results.all_satisfied()

        if prerequisites_ok:
            messages.append("✓ All prerequisites satisfied")
        else:
            missing = prerequisite_results.get_missing()
            messages.append(f"✗ Missing prerequisites: {', '.join(missing)}")

        return VerificationResult(
            mk8_installed=mk8_installed,
            prerequisites_ok=prerequisites_ok,
            prerequisite_results=prerequisite_results,
            messages=messages,
        )

    def verify_mk8_installed(self) -> bool:
        """
        Verify mk8 command is available.

        Returns:
            True if mk8 is in PATH, False otherwise
        """
        return shutil.which("mk8") is not None

    def get_installation_instructions(self, missing: List[str]) -> str:
        """
        Get basic installation instructions for missing tools.

        Args:
            missing: List of missing tool names

        Returns:
            Formatted installation instructions
        """
        if not missing:
            return ""

        lines = ["Installation Instructions:", ""]

        for tool in missing:
            if tool in self.INSTALLATION_INSTRUCTIONS:
                lines.append(self.INSTALLATION_INSTRUCTIONS[tool])
                lines.append("")

        return "\n".join(lines)
