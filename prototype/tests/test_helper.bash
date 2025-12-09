#!/usr/bin/env bash
# Test helper functions for BATS tests
# Provides common setup and teardown functions for unit and integration tests

# Get the absolute path to the prototype directory
PROTOTYPE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Test fixtures directory
TEST_FIXTURES="${PROTOTYPE_ROOT}/tests/fixtures"

# Temporary directory for test isolation
TEST_TEMP_DIR=""

# Setup test environment before each test
# Creates isolated temporary directory and sets up environment
setup_test_env() {
    # Create temporary directory for this test
    TEST_TEMP_DIR="$(mktemp -d)"

    # Export paths for test use
    export TEST_TEMP_DIR
    export PROTOTYPE_ROOT
    export TEST_FIXTURES

    # Change to temp directory to isolate file operations
    cd "$TEST_TEMP_DIR" || exit 1
}

# Teardown test environment after each test
# Cleans up temporary files and restores environment
teardown_test_env() {
    # Return to original directory
    cd "$PROTOTYPE_ROOT" || true

    # Remove temporary directory if it exists
    if [[ -n "$TEST_TEMP_DIR" ]] && [[ -d "$TEST_TEMP_DIR" ]]; then
        rm -rf "$TEST_TEMP_DIR"
    fi

    # Unset test environment variables
    unset TEST_TEMP_DIR
}

# Mock external command for testing
# Usage: mock_command "command_name" "mock_output" [exit_code]
mock_command() {
    local cmd_name="$1"
    local mock_output="${2:-}"
    local exit_code="${3:-0}"

    # Create mock script in PATH
    local mock_script="${TEST_TEMP_DIR}/bin/${cmd_name}"
    mkdir -p "${TEST_TEMP_DIR}/bin"

    cat > "$mock_script" <<EOF
#!/usr/bin/env bash
echo "$mock_output"
exit $exit_code
EOF

    chmod +x "$mock_script"

    # Add to PATH
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
}

# Assert that command succeeded (exit code 0)
# Usage: assert_success
assert_success() {
    if [ "$status" -ne 0 ]; then
        echo "Expected success (exit code 0), got: $status" >&2
        echo "Output: $output" >&2
        return 1
    fi
}

# Assert that command failed (exit code non-zero)
# Usage: assert_failure
assert_failure() {
    if [ "$status" -eq 0 ]; then
        echo "Expected failure (non-zero exit code), got: 0" >&2
        echo "Output: $output" >&2
        return 1
    fi
}

# Assert that a file exists
# Usage: assert_file_exists "path/to/file"
assert_file_exists() {
    local file_path="$1"
    if [[ ! -f "$file_path" ]]; then
        echo "Expected file to exist: $file_path" >&2
        return 1
    fi
}

# Assert that a directory exists
# Usage: assert_dir_exists "path/to/dir"
assert_dir_exists() {
    local dir_path="$1"
    if [[ ! -d "$dir_path" ]]; then
        echo "Expected directory to exist: $dir_path" >&2
        return 1
    fi
}

# Assert that output contains a string
# Usage: assert_output_contains "expected_string"
assert_output_contains() {
    local expected="$1"
    if [[ ! "$output" =~ $expected ]]; then
        echo "Expected output to contain: $expected" >&2
        echo "Actual output: $output" >&2
        return 1
    fi
}

# Assert that output does not contain a string
# Usage: assert_output_not_contains "unexpected_string"
assert_output_not_contains() {
    local unexpected="$1"
    if [[ "$output" =~ $unexpected ]]; then
        echo "Expected output NOT to contain: $unexpected" >&2
        echo "Actual output: $output" >&2
        return 1
    fi
}
