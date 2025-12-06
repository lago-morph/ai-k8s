"""Tests for platform detection data models."""

import pytest
from mk8.integrations.platform_models import PlatformInfo


class TestPlatformInfo:
    """Tests for PlatformInfo dataclass."""

    def test_create_platform_info_with_all_fields(self) -> None:
        """Test creating PlatformInfo with all fields populated."""
        info = PlatformInfo(
            os="linux",
            distribution="ubuntu",
            version="22.04",
            architecture="x86_64",
            supported=True,
        )

        assert info.os == "linux"
        assert info.distribution == "ubuntu"
        assert info.version == "22.04"
        assert info.architecture == "x86_64"
        assert info.supported is True

    def test_create_platform_info_with_optional_none(self) -> None:
        """Test creating PlatformInfo with optional fields as None."""
        info = PlatformInfo(
            os="darwin",
            distribution=None,
            version="13.0",
            architecture="arm64",
            supported=True,
        )

        assert info.os == "darwin"
        assert info.distribution is None
        assert info.version == "13.0"
        assert info.architecture == "arm64"
        assert info.supported is True

    def test_is_linux_returns_true_for_linux_os(self) -> None:
        """Test is_linux() returns True when os is 'linux'."""
        info = PlatformInfo(
            os="linux",
            distribution="ubuntu",
            version="22.04",
            architecture="x86_64",
            supported=True,
        )

        assert info.is_linux() is True

    def test_is_linux_returns_true_for_wsl(self) -> None:
        """Test is_linux() returns True when os is 'wsl'."""
        info = PlatformInfo(
            os="wsl",
            distribution="ubuntu",
            version="22.04",
            architecture="x86_64",
            supported=True,
        )

        assert info.is_linux() is True

    def test_is_linux_returns_false_for_darwin(self) -> None:
        """Test is_linux() returns False when os is 'darwin'."""
        info = PlatformInfo(
            os="darwin",
            distribution=None,
            version="13.0",
            architecture="arm64",
            supported=True,
        )

        assert info.is_linux() is False

    def test_is_linux_returns_false_for_windows(self) -> None:
        """Test is_linux() returns False when os is 'windows'."""
        info = PlatformInfo(
            os="windows",
            distribution=None,
            version="11",
            architecture="x86_64",
            supported=False,
        )

        assert info.is_linux() is False

    def test_is_wsl_returns_true_for_wsl_os(self) -> None:
        """Test is_wsl() returns True when os is 'wsl'."""
        info = PlatformInfo(
            os="wsl",
            distribution="ubuntu",
            version="22.04",
            architecture="x86_64",
            supported=True,
        )

        assert info.is_wsl() is True

    def test_is_wsl_returns_false_for_linux(self) -> None:
        """Test is_wsl() returns False when os is 'linux'."""
        info = PlatformInfo(
            os="linux",
            distribution="ubuntu",
            version="22.04",
            architecture="x86_64",
            supported=True,
        )

        assert info.is_wsl() is False

    def test_is_wsl_returns_false_for_darwin(self) -> None:
        """Test is_wsl() returns False when os is 'darwin'."""
        info = PlatformInfo(
            os="darwin",
            distribution=None,
            version="13.0",
            architecture="arm64",
            supported=True,
        )

        assert info.is_wsl() is False

    def test_platform_info_equality(self) -> None:
        """Test that two PlatformInfo instances with same values are equal."""
        info1 = PlatformInfo(
            os="linux",
            distribution="ubuntu",
            version="22.04",
            architecture="x86_64",
            supported=True,
        )
        info2 = PlatformInfo(
            os="linux",
            distribution="ubuntu",
            version="22.04",
            architecture="x86_64",
            supported=True,
        )

        assert info1 == info2

    def test_platform_info_inequality(self) -> None:
        """Test that two PlatformInfo instances with different values are not equal."""
        info1 = PlatformInfo(
            os="linux",
            distribution="ubuntu",
            version="22.04",
            architecture="x86_64",
            supported=True,
        )
        info2 = PlatformInfo(
            os="darwin",
            distribution=None,
            version="13.0",
            architecture="arm64",
            supported=True,
        )

        assert info1 != info2
