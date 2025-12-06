"""Tests for version module."""

import pytest
from mk8.core.version import Version


class TestVersion:
    """Tests for Version class."""

    def test_get_version_basic(self) -> None:
        """Test basic version string generation."""
        # Save original values
        original_major = Version.MAJOR
        original_minor = Version.MINOR
        original_patch = Version.PATCH
        original_prerelease = Version.PRERELEASE
        original_build = Version.BUILD

        try:
            # Set test values
            Version.MAJOR = 1
            Version.MINOR = 2
            Version.PATCH = 3
            Version.PRERELEASE = None
            Version.BUILD = None

            version = Version.get_version()
            assert version == "1.2.3"
        finally:
            # Restore original values
            Version.MAJOR = original_major
            Version.MINOR = original_minor
            Version.PATCH = original_patch
            Version.PRERELEASE = original_prerelease
            Version.BUILD = original_build

    def test_get_version_with_prerelease(self) -> None:
        """Test version string with prerelease."""
        original_major = Version.MAJOR
        original_minor = Version.MINOR
        original_patch = Version.PATCH
        original_prerelease = Version.PRERELEASE
        original_build = Version.BUILD

        try:
            Version.MAJOR = 1
            Version.MINOR = 2
            Version.PATCH = 3
            Version.PRERELEASE = "alpha.1"
            Version.BUILD = None

            version = Version.get_version()
            assert version == "1.2.3-alpha.1"
        finally:
            Version.MAJOR = original_major
            Version.MINOR = original_minor
            Version.PATCH = original_patch
            Version.PRERELEASE = original_prerelease
            Version.BUILD = original_build

    def test_get_version_with_build(self) -> None:
        """Test version string with build metadata."""
        original_major = Version.MAJOR
        original_minor = Version.MINOR
        original_patch = Version.PATCH
        original_prerelease = Version.PRERELEASE
        original_build = Version.BUILD

        try:
            Version.MAJOR = 1
            Version.MINOR = 2
            Version.PATCH = 3
            Version.PRERELEASE = None
            Version.BUILD = "20240101.abc123"

            version = Version.get_version()
            assert version == "1.2.3+20240101.abc123"
        finally:
            Version.MAJOR = original_major
            Version.MINOR = original_minor
            Version.PATCH = original_patch
            Version.PRERELEASE = original_prerelease
            Version.BUILD = original_build

    def test_get_version_with_prerelease_and_build(self) -> None:
        """Test version string with both prerelease and build."""
        original_major = Version.MAJOR
        original_minor = Version.MINOR
        original_patch = Version.PATCH
        original_prerelease = Version.PRERELEASE
        original_build = Version.BUILD

        try:
            Version.MAJOR = 1
            Version.MINOR = 2
            Version.PATCH = 3
            Version.PRERELEASE = "beta.2"
            Version.BUILD = "20240101.abc123"

            version = Version.get_version()
            assert version == "1.2.3-beta.2+20240101.abc123"
        finally:
            Version.MAJOR = original_major
            Version.MINOR = original_minor
            Version.PATCH = original_patch
            Version.PRERELEASE = original_prerelease
            Version.BUILD = original_build

    def test_get_version_info(self) -> None:
        """Test version info dictionary."""
        original_major = Version.MAJOR
        original_minor = Version.MINOR
        original_patch = Version.PATCH
        original_prerelease = Version.PRERELEASE
        original_build = Version.BUILD

        try:
            Version.MAJOR = 1
            Version.MINOR = 2
            Version.PATCH = 3
            Version.PRERELEASE = "alpha.1"
            Version.BUILD = "abc123"

            info = Version.get_version_info()

            assert info["version"] == "1.2.3-alpha.1+abc123"
            assert info["major"] == 1
            assert info["minor"] == 2
            assert info["patch"] == 3
            assert info["prerelease"] == "alpha.1"
            assert info["build"] == "abc123"
        finally:
            Version.MAJOR = original_major
            Version.MINOR = original_minor
            Version.PATCH = original_patch
            Version.PRERELEASE = original_prerelease
            Version.BUILD = original_build

    def test_current_version_format(self) -> None:
        """Test that current version follows semantic versioning format."""
        version = Version.get_version()
        # Should have at least MAJOR.MINOR.PATCH
        parts = version.split("+")[0].split("-")[0].split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)
