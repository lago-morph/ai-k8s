"""Tests for AWSClient integration layer."""

import pytest
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st
from botocore.exceptions import ClientError, BotoCoreError

from mk8.integrations.aws_client import AWSClient
from mk8.business.credential_models import ValidationResult


class TestAWSClientValidateCredentials:
    """Tests for AWSClient.validate_credentials()."""

    @patch("mk8.integrations.aws_client.boto3")
    def test_successful_validation_returns_account_id(self, mock_boto3: Mock) -> None:
        """Test successful validation returns account ID."""
        mock_sts = Mock()
        mock_sts.get_caller_identity.return_value = {
            "Account": "123456789012",
            "UserId": "AIDAI...",
            "Arn": "arn:aws:iam::123456789012:user/test",
        }
        mock_boto3.client.return_value = mock_sts

        client = AWSClient()
        result = client.validate_credentials(
            "AKIAIOSFODNN7EXAMPLE",
            "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "us-east-1",
        )

        assert result.success is True
        assert result.account_id == "123456789012"
        assert result.error_code is None
        assert result.error_message is None

    @patch("mk8.integrations.aws_client.boto3")
    def test_invalid_client_token_error(self, mock_boto3: Mock) -> None:
        """Test InvalidClientTokenId error is handled correctly."""
        mock_sts = Mock()
        error_response = {
            "Error": {
                "Code": "InvalidClientTokenId",
                "Message": "The security token included in the request is invalid",
            }
        }
        mock_sts.get_caller_identity.side_effect = ClientError(
            error_response, "GetCallerIdentity"
        )
        mock_boto3.client.return_value = mock_sts

        client = AWSClient()
        result = client.validate_credentials(
            "AKIAIOSFODNN7EXAMPLE",
            "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "us-east-1",
        )

        assert result.success is False
        assert result.account_id is None
        assert result.error_code == "InvalidClientTokenId"
        assert "invalid" in result.error_message.lower()

    @patch("mk8.integrations.aws_client.boto3")
    def test_access_denied_error(self, mock_boto3: Mock) -> None:
        """Test AccessDenied error is handled correctly."""
        mock_sts = Mock()
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "User is not authorized to perform: sts:GetCallerIdentity",
            }
        }
        mock_sts.get_caller_identity.side_effect = ClientError(
            error_response, "GetCallerIdentity"
        )
        mock_boto3.client.return_value = mock_sts

        client = AWSClient()
        result = client.validate_credentials(
            "AKIAIOSFODNN7EXAMPLE",
            "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "us-east-1",
        )

        assert result.success is False
        assert result.error_code == "AccessDenied"
        assert "authorized" in result.error_message.lower()

    @patch("mk8.integrations.aws_client.boto3")
    def test_signature_does_not_match_error(self, mock_boto3: Mock) -> None:
        """Test SignatureDoesNotMatch error is handled correctly."""
        mock_sts = Mock()
        error_response = {
            "Error": {
                "Code": "SignatureDoesNotMatch",
                "Message": "The request signature we calculated does not match",
            }
        }
        mock_sts.get_caller_identity.side_effect = ClientError(
            error_response, "GetCallerIdentity"
        )
        mock_boto3.client.return_value = mock_sts

        client = AWSClient()
        result = client.validate_credentials(
            "AKIAIOSFODNN7EXAMPLE",
            "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "us-east-1",
        )

        assert result.success is False
        assert result.error_code == "SignatureDoesNotMatch"

    @patch("mk8.integrations.aws_client.boto3")
    def test_network_error(self, mock_boto3: Mock) -> None:
        """Test network errors are handled correctly."""
        mock_sts = Mock()
        mock_sts.get_caller_identity.side_effect = BotoCoreError()
        mock_boto3.client.return_value = mock_sts

        client = AWSClient()
        result = client.validate_credentials(
            "AKIAIOSFODNN7EXAMPLE",
            "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "us-east-1",
        )

        assert result.success is False
        assert result.error_code == "NetworkError"

    @patch("mk8.integrations.aws_client.boto3")
    def test_timeout_error(self, mock_boto3: Mock) -> None:
        """Test timeout errors are handled correctly."""
        mock_sts = Mock()
        mock_sts.get_caller_identity.side_effect = Exception("Read timeout")
        mock_boto3.client.return_value = mock_sts

        client = AWSClient()
        result = client.validate_credentials(
            "AKIAIOSFODNN7EXAMPLE",
            "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "us-east-1",
        )

        assert result.success is False
        assert result.error_code == "UnknownError"


class TestAWSClientMaskSecret:
    """Tests for AWSClient._mask_secret()."""

    def test_mask_secret_shows_first_and_last_four(self) -> None:
        """Test secret masking shows first and last 4 characters."""
        client = AWSClient()
        secret = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

        masked = client._mask_secret(secret)

        assert masked.startswith("wJal")
        assert masked.endswith("EKEY")
        assert "*" in masked

    def test_mask_secret_with_short_secret(self) -> None:
        """Test secret masking with secret shorter than 8 characters."""
        client = AWSClient()
        secret = "short"

        masked = client._mask_secret(secret)

        assert masked == "****"

    def test_mask_secret_with_exactly_8_chars(self) -> None:
        """Test secret masking with exactly 8 characters."""
        client = AWSClient()
        secret = "12345678"

        masked = client._mask_secret(secret)

        assert masked == "****"

    def test_mask_secret_with_9_chars(self) -> None:
        """Test secret masking with 9 characters shows first/last 4."""
        client = AWSClient()
        secret = "123456789"

        masked = client._mask_secret(secret)

        assert masked == "1234*6789"

    def test_mask_secret_preserves_length_info(self) -> None:
        """Test masked secret gives indication of original length."""
        client = AWSClient()
        short_secret = "123456789"
        long_secret = "1234567890123456789012345678901234567890"

        short_masked = client._mask_secret(short_secret)
        long_masked = client._mask_secret(long_secret)

        assert len(long_masked) > len(short_masked)


class TestAWSClientProperties:
    """Property-based tests for AWSClient."""

    @given(st.text(min_size=9, max_size=100))
    def test_property_mask_secret_always_masks_middle(self, secret: str) -> None:
        """Property: Masked secrets should always hide middle characters."""
        client = AWSClient()
        masked = client._mask_secret(secret)

        # Should contain asterisks
        assert "*" in masked
        # Should start with first 4 chars
        assert masked.startswith(secret[:4])
        # Should end with last 4 chars
        assert masked.endswith(secret[-4:])

    @given(st.text(min_size=1, max_size=8))
    def test_property_mask_short_secrets_completely(self, secret: str) -> None:
        """Property: Secrets 8 chars or less should be completely masked."""
        client = AWSClient()
        masked = client._mask_secret(secret)

        assert masked == "****"

    @patch("mk8.integrations.aws_client.boto3")
    def test_property_validation_result_has_suggestions_on_failure(
        self, mock_boto3: Mock
    ) -> None:
        """Property: Failed validation should always include suggestions."""
        mock_sts = Mock()
        error_response = {
            "Error": {
                "Code": "InvalidClientTokenId",
                "Message": "Invalid token",
            }
        }
        mock_sts.get_caller_identity.side_effect = ClientError(
            error_response, "GetCallerIdentity"
        )
        mock_boto3.client.return_value = mock_sts

        client = AWSClient()
        result = client.validate_credentials("key", "secret", "us-east-1")

        assert result.success is False
        suggestions = result.get_suggestions()
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)

    @patch("mk8.integrations.aws_client.boto3")
    def test_property_successful_validation_has_account_id(
        self, mock_boto3: Mock
    ) -> None:
        """Property: Successful validation should always return account ID."""
        mock_sts = Mock()
        mock_sts.get_caller_identity.return_value = {
            "Account": "123456789012",
            "UserId": "AIDAI...",
            "Arn": "arn:aws:iam::123456789012:user/test",
        }
        mock_boto3.client.return_value = mock_sts

        client = AWSClient()
        result = client.validate_credentials("key", "secret", "us-east-1")

        assert result.success is True
        assert result.account_id is not None
        assert len(result.account_id) > 0

    @patch("mk8.integrations.aws_client.boto3")
    def test_property_failed_validation_has_error_details(
        self, mock_boto3: Mock
    ) -> None:
        """Property: Failed validation should always include error code and message."""
        mock_sts = Mock()
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Not authorized",
            }
        }
        mock_sts.get_caller_identity.side_effect = ClientError(
            error_response, "GetCallerIdentity"
        )
        mock_boto3.client.return_value = mock_sts

        client = AWSClient()
        result = client.validate_credentials("key", "secret", "us-east-1")

        assert result.success is False
        assert result.error_code is not None
        assert result.error_message is not None
        assert len(result.error_code) > 0
        assert len(result.error_message) > 0
