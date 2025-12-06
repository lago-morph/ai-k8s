"""AWS client for credential validation."""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

from mk8.business.credential_models import ValidationResult


class AWSClient:
    """Client for AWS API operations."""

    def __init__(self) -> None:
        """Initialize AWS client."""
        pass

    def validate_credentials(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str,
    ) -> ValidationResult:
        """
        Validate credentials using STS GetCallerIdentity.

        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region

        Returns:
            ValidationResult with account_id if successful
        """
        try:
            # Configure boto3 with timeout
            config = Config(
                connect_timeout=10,
                read_timeout=10,
                retries={"max_attempts": 0},  # No retries for fast feedback
            )
            
            # Create STS client with provided credentials
            sts = boto3.client(
                "sts",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region,
                config=config,
            )
            
            # Call GetCallerIdentity to validate credentials
            response = sts.get_caller_identity()
            
            return ValidationResult(
                success=True,
                account_id=response["Account"],
            )
            
        except ClientError as e:
            # AWS API error (invalid credentials, permissions, etc.)
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            return ValidationResult(
                success=False,
                error_code=error_code,
                error_message=error_message,
            )
            
        except BotoCoreError as e:
            # Network or connection error
            return ValidationResult(
                success=False,
                error_code="NetworkError",
                error_message=f"Network error: {str(e)}",
            )
            
        except Exception as e:
            # Unexpected error
            return ValidationResult(
                success=False,
                error_code="UnknownError",
                error_message=f"Unexpected error: {str(e)}",
            )

    def _mask_secret(self, secret: str) -> str:
        """
        Mask secret for display (show first/last 4 chars).

        Args:
            secret: Secret to mask

        Returns:
            Masked secret string
        """
        if len(secret) <= 8:
            return "****"
        
        first_four = secret[:4]
        last_four = secret[-4:]
        middle_length = len(secret) - 8
        
        return f"{first_four}{'*' * middle_length}{last_four}"
