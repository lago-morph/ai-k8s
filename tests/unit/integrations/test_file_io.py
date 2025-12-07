"""Tests for FileIO integration layer."""

import os
import stat
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from hypothesis import given, strategies as st
from unittest.mock import Mock, patch, mock_open

from mk8.integrations.file_io import FileIO
from mk8.core.errors import ConfigurationError


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config"
        config_dir.mkdir(parents=True, exist_ok=True)
        yield config_dir


@pytest.fixture
def temp_config_file(temp_config_dir: Path) -> Path:
    """Create a temporary config file for testing."""
    config_file = temp_config_dir / "mk8"
    return config_file


class TestFileIOReadConfigFile:
    """Tests for FileIO.read_config_file()."""

    def test_read_existing_config_file(self, temp_config_file: Path) -> None:
        """Test reading an existing config file with valid content."""
        content = (
            "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
            "AWS_SECRET_ACCESS_KEY=secret\n"
            "AWS_DEFAULT_REGION=us-east-1\n"
        )
        temp_config_file.write_text(content)

        file_io = FileIO(config_path=str(temp_config_file))
        result = file_io.read_config_file()

        assert result is not None
        assert result["AWS_ACCESS_KEY_ID"] == "AKIAIOSFODNN7EXAMPLE"
        assert result["AWS_SECRET_ACCESS_KEY"] == "secret"
        assert result["AWS_DEFAULT_REGION"] == "us-east-1"

    def test_read_nonexistent_config_file(self, temp_config_file: Path) -> None:
        """Test reading a config file that doesn't exist returns None."""
        file_io = FileIO(config_path=str(temp_config_file))
        result = file_io.read_config_file()

        assert result is None

    def test_read_empty_config_file(self, temp_config_file: Path) -> None:
        """Test reading an empty config file returns empty dict."""
        temp_config_file.write_text("")

        file_io = FileIO(config_path=str(temp_config_file))
        result = file_io.read_config_file()

        assert result == {}

    def test_read_config_file_with_comments(self, temp_config_file: Path) -> None:
        """Test reading config file ignores comment lines."""
        content = (
            "# This is a comment\n"
            "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
            "# Another comment\n"
            "AWS_SECRET_ACCESS_KEY=secret\n"
        )
        temp_config_file.write_text(content)

        file_io = FileIO(config_path=str(temp_config_file))
        result = file_io.read_config_file()

        assert result is not None
        assert len(result) == 2
        assert result["AWS_ACCESS_KEY_ID"] == ("AKIAIOSFODNN7EXAMPLE")
        assert result["AWS_SECRET_ACCESS_KEY"] == "secret"

    def test_read_config_file_with_whitespace(self, temp_config_file: Path) -> None:
        """Test reading config file strips whitespace from keys and values."""
        content = (
            "  AWS_ACCESS_KEY_ID  =  AKIAIOSFODNN7EXAMPLE  \n"
            "  AWS_SECRET_ACCESS_KEY=secret\n"
        )
        temp_config_file.write_text(content)

        file_io = FileIO(config_path=str(temp_config_file))
        result = file_io.read_config_file()

        assert result is not None
        assert result["AWS_ACCESS_KEY_ID"] == "AKIAIOSFODNN7EXAMPLE"
        assert result["AWS_SECRET_ACCESS_KEY"] == "secret"

    def test_read_config_file_with_empty_lines(self, temp_config_file: Path) -> None:
        """Test reading config file ignores empty lines."""
        content = (
            "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
            "\n\n"
            "AWS_SECRET_ACCESS_KEY=secret\n\n"
        )
        temp_config_file.write_text(content)

        file_io = FileIO(config_path=str(temp_config_file))
        result = file_io.read_config_file()

        assert result is not None
        assert len(result) == 2

    def test_read_config_file_with_malformed_lines(
        self, temp_config_file: Path
    ) -> None:
        """Test reading config file skips malformed lines without = sign."""
        content = (
            "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
            "MALFORMED_LINE\n"
            "AWS_SECRET_ACCESS_KEY=secret\n"
        )
        temp_config_file.write_text(content)

        file_io = FileIO(config_path=str(temp_config_file))
        result = file_io.read_config_file()

        assert result is not None
        assert len(result) == 2
        assert "MALFORMED_LINE" not in result


class TestFileIOWriteConfigFile:
    """Tests for FileIO.write_config_file()."""

    def test_write_config_file_creates_file(self, temp_config_file: Path) -> None:
        """Test writing config file creates the file."""
        config = {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "AWS_SECRET_ACCESS_KEY": "secret",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        file_io = FileIO(config_path=str(temp_config_file))
        file_io.write_config_file(config)

        assert temp_config_file.exists()

    def test_write_config_file_has_correct_content(
        self, temp_config_file: Path
    ) -> None:
        """Test writing config file produces correct key=value format."""
        config = {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "AWS_SECRET_ACCESS_KEY": "secret",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        file_io = FileIO(config_path=str(temp_config_file))
        file_io.write_config_file(config)

        content = temp_config_file.read_text()
        assert "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in content
        assert "AWS_SECRET_ACCESS_KEY=secret" in content
        assert "AWS_DEFAULT_REGION=us-east-1" in content

    def test_write_config_file_has_secure_permissions(
        self, temp_config_file: Path
    ) -> None:
        """Test writing config file sets permissions to 0600."""
        config = {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "AWS_SECRET_ACCESS_KEY": "secret",
        }

        file_io = FileIO(config_path=str(temp_config_file))
        file_io.write_config_file(config)

        # Check file permissions (0600 = owner read/write only)
        file_stat = temp_config_file.stat()
        permissions = stat.filemode(file_stat.st_mode)

        # On Unix-like systems, should be -rw-------
        # On Windows, permissions work differently but we still check
        if os.name != "nt":
            assert permissions == "-rw-------"

    def test_write_config_file_overwrites_existing(
        self, temp_config_file: Path
    ) -> None:
        """Test writing config file overwrites existing content."""
        temp_config_file.write_text("OLD_KEY=old_value\n")

        config = {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
        }

        file_io = FileIO(config_path=str(temp_config_file))
        file_io.write_config_file(config)

        content = temp_config_file.read_text()
        assert "OLD_KEY" not in content
        assert "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in content

    def test_write_config_file_creates_directory(self, temp_config_dir: Path) -> None:
        """Test writing config file creates parent directory if needed."""
        config_file = temp_config_dir / "subdir" / "mk8"
        config = {"AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE"}

        file_io = FileIO(config_path=str(config_file))
        file_io.write_config_file(config)

        assert config_file.exists()
        assert config_file.parent.exists()


class TestFileIOEnsureConfigDirectory:
    """Tests for FileIO.ensure_config_directory()."""

    def test_ensure_config_directory_creates_directory(
        self, temp_config_dir: Path
    ) -> None:
        """Test ensure_config_directory creates directory if it doesn't exist."""
        new_dir = temp_config_dir / "new_subdir"
        config_file = new_dir / "mk8"

        file_io = FileIO(config_path=str(config_file))
        file_io.ensure_config_directory()

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_config_directory_does_not_fail_if_exists(
        self, temp_config_dir: Path
    ) -> None:
        """Test ensure_config_directory succeeds if directory already exists."""
        config_file = temp_config_dir / "mk8"

        file_io = FileIO(config_path=str(config_file))
        file_io.ensure_config_directory()
        file_io.ensure_config_directory()  # Call twice

        assert temp_config_dir.exists()


class TestFileIOSetSecurePermissions:
    """Tests for FileIO.set_secure_permissions()."""

    def test_set_secure_permissions_sets_0600(self, temp_config_file: Path) -> None:
        """Test set_secure_permissions sets file to 0600."""
        temp_config_file.write_text("test")

        file_io = FileIO()
        file_io.set_secure_permissions(str(temp_config_file))

        if os.name != "nt":
            file_stat = temp_config_file.stat()
            permissions = stat.filemode(file_stat.st_mode)
            assert permissions == "-rw-------"

    def test_set_secure_permissions_on_nonexistent_file_raises_error(self) -> None:
        """Test set_secure_permissions raises error for nonexistent file."""
        file_io = FileIO()

        with pytest.raises(ConfigurationError) as exc_info:
            file_io.set_secure_permissions("/nonexistent/file")

        assert "Cannot set permissions" in str(exc_info.value)


class TestFileIOCheckFilePermissions:
    """Tests for FileIO.check_file_permissions()."""

    def test_check_file_permissions_returns_true_for_0600(
        self, temp_config_file: Path
    ) -> None:
        """Test check_file_permissions returns True for secure permissions."""
        temp_config_file.write_text("test")

        file_io = FileIO()
        file_io.set_secure_permissions(str(temp_config_file))

        result = file_io.check_file_permissions(str(temp_config_file))

        if os.name != "nt":
            assert result is True

    def test_check_file_permissions_returns_false_for_insecure(
        self, temp_config_file: Path
    ) -> None:
        """Test check_file_permissions returns False for insecure permissions."""
        temp_config_file.write_text("test")

        if os.name != "nt":
            # Set insecure permissions (0644 = readable by others)
            temp_config_file.chmod(0o644)

            file_io = FileIO()
            result = file_io.check_file_permissions(str(temp_config_file))

            assert result is False

    def test_check_file_permissions_on_nonexistent_file_returns_false(self) -> None:
        """Test check_file_permissions returns False for nonexistent file."""
        file_io = FileIO()
        result = file_io.check_file_permissions("/nonexistent/file")

        assert result is False


class TestFileIOProperties:
    """Property-based tests for FileIO."""

    @given(
        config=st.dictionaries(
            keys=st.text(
                min_size=1,
                max_size=50,
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
                ),
            ),
            values=st.text(
                min_size=1,
                max_size=100,
                alphabet=st.characters(min_codepoint=33, max_codepoint=126),
            ),  # Exclude space (32)
            min_size=1,
            max_size=10,
        )
    )
    def test_property_write_and_read_roundtrip(self, config: dict) -> None:
        """Property: Writing and reading config should preserve all data.

        Excludes whitespace-only values.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "mk8"
            file_io = FileIO(config_path=str(config_file))

            file_io.write_config_file(config)
            result = file_io.read_config_file()

            assert result is not None
            # Strip values for comparison since read_config_file strips them
            expected = {k: v.strip() for k, v in config.items()}
            assert result == expected

    @given(
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        )
    )
    def test_property_file_created_after_write(self, value: str) -> None:
        """Property: File should always exist after write_config_file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test_mk8"
            config = {"TEST_KEY": value}

            file_io = FileIO(config_path=str(config_file))
            file_io.write_config_file(config)

            assert config_file.exists()

    def test_property_directory_created_before_write(self) -> None:
        """Property: Parent directory should exist after ensure_config_directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new_test_dir"
            config_file = new_dir / "mk8"

            file_io = FileIO(config_path=str(config_file))
            file_io.ensure_config_directory()

            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_property_secure_permissions_after_write(self) -> None:
        """Property: File should have secure permissions after write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "mk8"
            config = {"AWS_ACCESS_KEY_ID": "test"}

            file_io = FileIO(config_path=str(config_file))
            file_io.write_config_file(config)

            if os.name != "nt":
                result = file_io.check_file_permissions(str(config_file))
                assert result is True


class TestFileIOReadConfigFileErrors:
    """Tests for FileIO.read_config_file() error handling."""

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_read_config_file_permission_error(self, mock_open_func: Mock) -> None:
        """Test read_config_file raises ConfigurationError on permission error."""
        file_io = FileIO(config_path="/tmp/test_config")

        # Create the file so exists() returns True
        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ConfigurationError, match="Failed to read config file"):
                file_io.read_config_file()

    @patch("builtins.open", side_effect=IOError("I/O error"))
    def test_read_config_file_io_error(self, mock_open_func: Mock) -> None:
        """Test read_config_file raises ConfigurationError on I/O error."""
        file_io = FileIO(config_path="/tmp/test_config")

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ConfigurationError, match="Failed to read config file"):
                file_io.read_config_file()


class TestFileIOWriteConfigFileErrors:
    """Tests for FileIO.write_config_file() error handling."""

    @patch("mk8.integrations.file_io.FileIO.ensure_config_directory")
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_write_config_file_permission_error(
        self, mock_open_func: Mock, mock_ensure: Mock
    ) -> None:
        """Test write_config_file raises ConfigurationError on permission error."""
        file_io = FileIO(config_path="/tmp/test_config")
        config = {"KEY": "value"}

        with pytest.raises(ConfigurationError, match="Failed to write config file"):
            file_io.write_config_file(config)

    @patch("mk8.integrations.file_io.FileIO.ensure_config_directory")
    @patch("builtins.open", side_effect=IOError("Disk full"))
    def test_write_config_file_io_error(
        self, mock_open_func: Mock, mock_ensure: Mock
    ) -> None:
        """Test write_config_file raises ConfigurationError on I/O error."""
        file_io = FileIO(config_path="/tmp/test_config")
        config = {"KEY": "value"}

        with pytest.raises(ConfigurationError, match="Failed to write config file"):
            file_io.write_config_file(config)


class TestFileIOSetSecurePermissionsErrors:
    """Tests for FileIO.set_secure_permissions() error handling."""

    def test_set_secure_permissions_nonexistent_file(self) -> None:
        """Test set_secure_permissions raises error for nonexistent file."""
        file_io = FileIO()

        with pytest.raises(
            ConfigurationError, match="Cannot set permissions on nonexistent file"
        ):
            file_io.set_secure_permissions("/nonexistent/file")

    @patch("os.name", "nt")
    def test_set_secure_permissions_windows(self, temp_config_file: Path) -> None:
        """Test set_secure_permissions on Windows (skips chmod)."""
        temp_config_file.write_text("test")
        file_io = FileIO()

        # Should not raise on Windows
        file_io.set_secure_permissions(str(temp_config_file))

    @patch("os.name", "posix")
    @patch.object(Path, "chmod", side_effect=OSError("Permission denied"))
    def test_set_secure_permissions_chmod_error(
        self, mock_chmod: Mock, temp_config_file: Path
    ) -> None:
        """Test set_secure_permissions raises error when chmod fails."""
        temp_config_file.write_text("test")
        file_io = FileIO(config_path=str(temp_config_file))

        with pytest.raises(
            ConfigurationError, match="Failed to set secure permissions"
        ):
            file_io.set_secure_permissions(str(temp_config_file))


class TestFileIOCheckFilePermissionsErrors:
    """Tests for FileIO.check_file_permissions() error handling."""

    def test_check_file_permissions_nonexistent_file(self) -> None:
        """Test check_file_permissions returns False for nonexistent file."""
        file_io = FileIO()

        result = file_io.check_file_permissions("/nonexistent/file")

        assert result is False

    @patch("os.name", "nt")
    def test_check_file_permissions_windows(self, temp_config_file: Path) -> None:
        """Test check_file_permissions on Windows always returns True."""
        temp_config_file.write_text("test")
        file_io = FileIO()

        result = file_io.check_file_permissions(str(temp_config_file))

        assert result is True

    @patch("os.name", "posix")
    @patch.object(Path, "stat", side_effect=OSError("Permission denied"))
    def test_check_file_permissions_stat_error(
        self, mock_stat: Mock, temp_config_file: Path
    ) -> None:
        """Test check_file_permissions returns False on stat error."""
        temp_config_file.write_text("test")
        file_io = FileIO(config_path=str(temp_config_file))

        result = file_io.check_file_permissions(str(temp_config_file))

        assert result is False
