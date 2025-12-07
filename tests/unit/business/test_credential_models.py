"""Tests for AWS credential data models."""

import os
import pytest
from hypothesis import given, strategies as st

from mk8.business.credential_models import (
    AWSCredentials,
    ValidationResult,
    SyncResult,
    PromptChoice,
)


class TestAWSCredentials:
    """Tests for AWSCredentials dataclass."""

    def test_is_complete_with_all_fields(self) -> None:
        """Test is_complete returns True when all fields are non-empty."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
        )
        assert creds.is_complete() is True

    def test_is_complete_with_empty_access_key(self) -> None:
        """Test is_complete returns False when access_key_id is empty."""
        creds = AWSCredentials(
            access_key_id="",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
        )
        assert creds.is_complete() is False

    def test_is_complete_with_empty_secret_key(self) -> None:
        """Test is_complete returns False when secret_access_key is empty."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="",
            region="us-east-1",
        )
        assert creds.is_complete() is False

    def test_is_complete_with_empty_region(self) -> None:
        """Test is_complete returns False when region is empty."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="",
        )
        assert creds.is_complete() is False

    def test_is_complete_with_all_empty(self) -> None:
        """Test is_complete returns False when all fields are empty."""
        creds = AWSCredentials(
            access_key_id="",
            secret_access_key="",
            region="",
        )
        assert creds.is_complete() is False

    def test_to_dict_returns_correct_keys(self) -> None:
        """Test to_dict returns dictionary with correct AWS env var keys."""
        creds = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
        )
        result = creds.to_dict()

        assert "AWS_ACCESS_KEY_ID" in result
        assert "AWS_SECRET_ACCESS_KEY" in result
        assert "AWS_DEFAULT_REGION" in result
        assert result["AWS_ACCESS_KEY_ID"] == "AKIAIOSFODNN7EXAMPLE"
        assert (
            result["AWS_SECRET_ACCESS_KEY"]
            == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )
        assert result["AWS_DEFAULT_REGION"] == "us-east-1"

    def test_from_dict_creates_credentials(self) -> None:
        """Test from_dict creates AWSCredentials from dictionary."""
        data = {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "AWS_DEFAULT_REGION": "us-east-1",
        }
        creds = AWSCredentials.from_dict(data)

        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert creds.secret_access_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        assert creds.region == "us-east-1"

    def test_from_dict_with_missing_keys(self) -> None:
        """Test from_dict handles missing keys with empty strings."""
        data = {"AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE"}
        creds = AWSCredentials.from_dict(data)

        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert creds.secret_access_key == ""
        assert creds.region == ""

    def test_from_env_vars_with_aws_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test from_env_vars reads AWS_* environment variables."""
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv(
            "AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

        creds = AWSCredentials.from_env_vars("AWS")

        assert creds is not None
        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert creds.secret_access_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        assert creds.region == "us-east-1"

    def test_from_env_vars_with_mk8_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test from_env_vars reads MK8_AWS_* environment variables."""
        monkeypatch.setenv("MK8_AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv(
            "MK8_AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )
        monkeypatch.setenv("MK8_AWS_DEFAULT_REGION", "us-east-1")

        creds = AWSCredentials.from_env_vars("MK8_AWS")

        assert creds is not None
        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert creds.secret_access_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        assert creds.region == "us-east-1"

    def test_from_env_vars_returns_none_when_incomplete(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test from_env_vars returns None when not all vars are set."""
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv(
            "AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )
        # Missing AWS_DEFAULT_REGION

        creds = AWSCredentials.from_env_vars("AWS")

        assert creds is None

    def test_from_env_vars_returns_none_when_all_missing(self) -> None:
        """Test from_env_vars returns None when no vars are set."""
        # Ensure no AWS env vars are set
        for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"]:
            os.environ.pop(key, None)

        creds = AWSCredentials.from_env_vars("AWS")

        assert creds is None

    def test_roundtrip_to_dict_and_from_dict(self) -> None:
        """Test credentials can be converted to dict and back."""
        original = AWSCredentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
        )

        data = original.to_dict()
        restored = AWSCredentials.from_dict(data)

        assert restored.access_key_id == original.access_key_id
        assert restored.secret_access_key == original.secret_access_key
        assert restored.region == original.region


class TestAWSCredentialsProperties:
    """Property-based tests for AWSCredentials."""

    @given(
        access_key=st.text(min_size=1),
        secret_key=st.text(min_size=1),
        region=st.text(min_size=1),
    )
    def test_property_complete_credentials_are_complete(
        self, access_key: str, secret_key: str, region: str
    ) -> None:
        """Property: Credentials with all non-empty fields should be complete."""
        creds = AWSCredentials(
            access_key_id=access_key,
            secret_access_key=secret_key,
            region=region,
        )
        assert creds.is_complete() is True

    @given(
        access_key=st.one_of(st.just(""), st.text(min_size=1)),
        secret_key=st.one_of(st.just(""), st.text(min_size=1)),
        region=st.one_of(st.just(""), st.text(min_size=1)),
    )
    def test_property_incomplete_credentials_are_not_complete(
        self, access_key: str, secret_key: str, region: str
    ) -> None:
        """Property: Credentials with any empty field should not be complete."""
        # Skip the case where all are non-empty
        if access_key and secret_key and region:
            return

        creds = AWSCredentials(
            access_key_id=access_key,
            secret_access_key=secret_key,
            region=region,
        )
        assert creds.is_complete() is False

    @given(
        access_key=st.text(),
        secret_key=st.text(),
        region=st.text(),
    )
    def test_property_to_dict_has_correct_keys(
        self, access_key: str, secret_key: str, region: str
    ) -> None:
        """Property: to_dict should always return dict with AWS env var keys."""
        creds = AWSCredentials(
            access_key_id=access_key,
            secret_access_key=secret_key,
            region=region,
        )
        result = creds.to_dict()

        assert set(result.keys()) == {
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_DEFAULT_REGION",
        }
        assert result["AWS_ACCESS_KEY_ID"] == access_key
        assert result["AWS_SECRET_ACCESS_KEY"] == secret_key
        assert result["AWS_DEFAULT_REGION"] == region

    @given(
        access_key=st.text(),
        secret_key=st.text(),
        region=st.text(),
    )
    def test_property_roundtrip_preserves_data(
        self, access_key: str, secret_key: str, region: str
    ) -> None:
        """Property: Converting to dict and back should preserve all data."""
        original = AWSCredentials(
            access_key_id=access_key,
            secret_access_key=secret_key,
            region=region,
        )

        restored = AWSCredentials.from_dict(original.to_dict())

        assert restored.access_key_id == original.access_key_id
        assert restored.secret_access_key == original.secret_access_key
        assert restored.region == original.region


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_successful_validation_has_account_id(self) -> None:
        """Test successful validation includes account ID."""
        result = ValidationResult(
            success=True,
            account_id="123456789012",
        )
        assert result.success is True
        assert result.account_id == "123456789012"
        assert result.error_code is None
        assert result.error_message is None

    def test_failed_validation_has_error_details(self) -> None:
        """Test failed validation includes error code and message."""
        result = ValidationResult(
            success=False,
            error_code="InvalidClientTokenId",
            error_message="The security token included in the request is invalid",
        )
        assert result.success is False
        assert result.account_id is None
        assert result.error_code == "InvalidClientTokenId"
        assert (
            result.error_message
            == "The security token included in the request is invalid"
        )

    def test_get_suggestions_for_invalid_client_token(self) -> None:
        """Test suggestions for InvalidClientTokenId error."""
        result = ValidationResult(
            success=False,
            error_code="InvalidClientTokenId",
            error_message="The security token included in the request is invalid",
        )
        suggestions = result.get_suggestions()

        assert len(suggestions) > 0
        assert any("Access Key ID" in s for s in suggestions)

    def test_get_suggestions_for_access_denied(self) -> None:
        """Test suggestions for AccessDenied error."""
        result = ValidationResult(
            success=False,
            error_code="AccessDenied",
            error_message="User is not authorized",
        )
        suggestions = result.get_suggestions()

        assert len(suggestions) > 0
        assert any("IAM" in s or "permission" in s for s in suggestions)

    def test_get_suggestions_for_unknown_error(self) -> None:
        """Test suggestions for unknown error code."""
        result = ValidationResult(
            success=False,
            error_code="UnknownError",
            error_message="Something went wrong",
        )
        suggestions = result.get_suggestions()

        assert len(suggestions) > 0
        assert any("credentials" in s.lower() for s in suggestions)

    def test_get_suggestions_returns_empty_for_success(self) -> None:
        """Test get_suggestions returns empty list for successful validation."""
        result = ValidationResult(
            success=True,
            account_id="123456789012",
        )
        suggestions = result.get_suggestions()

        assert suggestions == []


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_successful_sync_with_validation(self) -> None:
        """Test successful sync result with validation."""
        validation = ValidationResult(success=True, account_id="123456789012")
        result = SyncResult(
            success=True,
            cluster_exists=True,
            secret_updated=True,
            validation_result=validation,
        )

        assert result.success is True
        assert result.cluster_exists is True
        assert result.secret_updated is True
        assert result.validation_result is not None
        assert result.validation_result.success is True
        assert result.error is None

    def test_failed_sync_with_error(self) -> None:
        """Test failed sync result with error message."""
        result = SyncResult(
            success=False,
            cluster_exists=True,
            secret_updated=False,
            error="kubectl command failed",
        )

        assert result.success is False
        assert result.cluster_exists is True
        assert result.secret_updated is False
        assert result.error == "kubectl command failed"

    def test_sync_skipped_no_cluster(self) -> None:
        """Test sync result when no cluster exists."""
        result = SyncResult(
            success=True,
            cluster_exists=False,
            secret_updated=False,
        )

        assert result.success is True
        assert result.cluster_exists is False
        assert result.secret_updated is False


class TestPromptChoice:
    """Tests for PromptChoice enum."""

    def test_enum_values_exist(self) -> None:
        """Test all expected enum values exist."""
        assert PromptChoice.USE_ENV_VARS.value == "use_env"
        assert PromptChoice.ENTER_MANUALLY.value == "enter_manual"
        assert PromptChoice.EXIT.value == "exit"

    def test_enum_members_are_unique(self) -> None:
        """Test all enum members have unique values."""
        values = [choice.value for choice in PromptChoice]
        assert len(values) == len(set(values))
