"""Tests for version command."""

import pytest
from unittest.mock import patch
from io import StringIO
from mk8.cli.commands.version import VersionCommand


class TestVersionCommand:
    """Tests for VersionCommand class."""

    def test_execute_displays_version(self) -> None:
        """Test that execute displays version information."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = VersionCommand.execute()

            assert exit_code == 0
            output = fake_out.getvalue()
            assert "mk8 version" in output
            assert "0.1.0" in output
            #C this should use the version value from /pyproject.toml, not hard coded

    def test_execute_format(self) -> None:
        """Test that version output follows expected format."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            VersionCommand.execute()

            output = fake_out.getvalue().strip()
            # Should be "mk8 version X.Y.Z..."
            assert output.startswith("mk8 version ")
            version_part = output.replace("mk8 version ", "")
            # Basic version format check
            assert len(version_part) > 0
            #C this should check that the first two parts (X and Y) are numeric, that there exists a third part, and that the third part does not contain a dot.  So 1.2.aldk is ok (X and Y numeric, Z exists and does not contain a dot), a.b.c.d is not (X is not numeric, Y is not numeric, Z contains a dot).  Also .1.2 is also an error (no "X" part)
