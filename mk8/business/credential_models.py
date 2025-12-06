"""Data models for AWS credential management."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


@dataclass
class AWSCredentials:
    """AWS credential set."""

    access_key_id: str
    secret_access_key: str
    region: str

    def is_complete(self) -> bool:
        """
        Check if all three credentials are present and non-empty.

        Returns:
            True if all credentials are non-empty strings
        """
        return bool(self.access_key_id and self.secret_access_key and self.region)

    def to_dict(self) -> Dict[str, str]:
        """
        Convert to dictionary for storage.

        Returns:
            Dictionary with AWS environment variable names as keys
        """
        return {
            "AWS_ACCESS_KEY_ID": self.access_key_id,
            "AWS_SECRET_ACCESS_KEY": self.secret_access_key,
            "AWS_DEFAULT_REGION": self.region,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "AWSCredentials":
        """
        Create from dictionary.

        Args:
            data: Dictionary with AWS environment variable names as keys

        Returns:
            AWSCredentials instance
        """
        return cls(
            access_key_id=data.get("AWS_ACCESS_KEY_ID", ""),
            secret_access_key=data.get("AWS_SECRET_ACCESS_KEY", ""),
            region=data.get("AWS_DEFAULT_REGION", ""),
        )

    @classmethod
    def from_env_vars(cls, prefix: str = "AWS") -> Optional["AWSCredentials"]:
        """
        Create from environment variables.

        Args:
            prefix: Variable prefix ("AWS" or "MK8_AWS")

        Returns:
            AWSCredentials if all three vars present, None otherwise
        """
        if prefix == "MK8_AWS":
            access_key = os.environ.get("MK8_AWS_ACCESS_KEY_ID", "")
            secret_key = os.environ.get("MK8_AWS_SECRET_ACCESS_KEY", "")
            region = os.environ.get("MK8_AWS_DEFAULT_REGION", "")
        else:
            access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
            secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
            region = os.environ.get("AWS_DEFAULT_REGION", "")

        # Only return credentials if all three are present
        if access_key and secret_key and region:
            return cls(
                access_key_id=access_key,
                secret_access_key=secret_key,
                region=region,
            )
        return None


@dataclass
class ValidationResult:
    """Result of credential validation."""

    success: bool
    account_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def get_suggestions(self) -> List[str]:
        """
        Get suggestions based on error code.

        Returns:
            List of actionable suggestions
        """
        if not self.success and self.error_code:
            return self._error_code_to_suggestions(self.error_code)
        return []

    def _error_code_to_suggestions(self, error_code: str) -> List[str]:
        """
        Map AWS error codes to user-friendly suggestions.

        Args:
            error_code: AWS error code

        Returns:
            List of suggestions
        """
        suggestions_map = {
            "InvalidClientTokenId": [
                "Verify your AWS Access Key ID is correct",
                "Check if the credentials have been deactivated in IAM",
                "Run 'mk8 config' to update credentials",
            ],
            "SignatureDoesNotMatch": [
                "Verify your AWS Secret Access Key is correct",
                "Run 'mk8 config' to update credentials",
            ],
            "AccessDenied": [
                "Ensure the IAM user/role has 'sts:GetCallerIdentity' permission",
                "Check IAM policies attached to your credentials",
                "Contact your AWS administrator for permission updates",
            ],
            "InvalidToken": [
                "Token may have expired, regenerate credentials",
                "Run 'mk8 config' to update credentials",
            ],
            "UnrecognizedClientException": [
                "Verify the region is correct",
                "Check AWS service availability in your region",
            ],
        }
        return suggestions_map.get(
            error_code,
            [
                "Check your AWS credentials and permissions",
                "Run 'mk8 config' to reconfigure credentials",
            ],
        )


@dataclass
class SyncResult:
    """Result of Crossplane credential synchronization."""

    success: bool
    cluster_exists: bool
    secret_updated: bool
    validation_result: Optional[ValidationResult] = None
    error: Optional[str] = None


class PromptChoice(Enum):
    """User choices for credential prompts."""

    USE_ENV_VARS = "use_env"
    ENTER_MANUALLY = "enter_manual"
    EXIT = "exit"
