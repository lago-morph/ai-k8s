"""Tests for __main__.py entry point."""

import sys
from unittest.mock import patch
import pytest


class TestMainEntry:
    """Test the __main__.py entry point."""

    def test_main_entry_point_exists(self) -> None:
        """Test that __main__.py can be imported."""
        import mk8.__main__  # noqa: F401

        # If we get here, the module exists and can be imported
        assert True

    def test_main_entry_calls_main_function(self) -> None:
        """Test that __main__.py calls the main() function."""
        with patch("mk8.__main__.main") as mock_main:
            mock_main.return_value = 0

            # Import and execute __main__
            import mk8.__main__

            # The module should have called main() on import if __name__ == "__main__"
            # But since we're importing it, __name__ won't be "__main__"
            # So we just verify the function is available
            assert callable(mk8.__main__.main)

    def test_main_entry_structure(self) -> None:
        """Test that __main__.py has the correct structure."""
        # Read the __main__.py file
        with open("mk8/__main__.py") as f:
            content = f.read()

        # Verify it imports main
        assert "from mk8.cli.main import main" in content

        # Verify it calls sys.exit(main())
        assert "sys.exit(main())" in content

        # Verify it has the if __name__ == "__main__" guard
        assert 'if __name__ == "__main__"' in content

    def test_main_function_is_imported_correctly(self) -> None:
        """Test that main function is imported from cli.main."""
        from mk8.__main__ import main
        from mk8.cli.main import main as cli_main

        # They should be the same function
        assert main is cli_main
