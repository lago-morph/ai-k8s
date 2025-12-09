#!/usr/bin/env bats
# Unit tests for lib/common.sh
# Tests logging functions, prerequisite checking, and error handling

# Load test helpers
load ../test_helper

# Source the common library
setup() {
    setup_test_env
    # Source common.sh for testing
    source "${PROTOTYPE_ROOT}/lib/common.sh"
}

teardown() {
    teardown_test_env
}

# Test: log_info function
@test "log_info displays informational message with INFO prefix" {
    run log_info "Test information message"
    assert_success
    assert_output_contains "[INFO]"
    assert_output_contains "Test information message"
}

# Test: log_success function
@test "log_success displays success message with SUCCESS prefix" {
    run log_success "Operation completed successfully"
    assert_success
    assert_output_contains "[SUCCESS]"
    assert_output_contains "Operation completed successfully"
}

# Test: log_error function exits with default error code
@test "log_error exits with EXIT_GENERAL_ERROR (1) by default" {
    run log_error "Test error message"
    [ "$status" -eq 1 ]
    assert_output_contains "[ERROR]"
    assert_output_contains "Test error message"
}

# Test: log_error function exits with custom error code
@test "log_error exits with custom error code when provided" {
    run log_error "Missing prerequisite" "$EXIT_MISSING_PREREQ"
    [ "$status" -eq 2 ]
    assert_output_contains "[ERROR]"
    assert_output_contains "Missing prerequisite"
}

# Test: log_error function exits with AWS error code
@test "log_error exits with EXIT_AWS_ERROR (4) when specified" {
    run log_error "AWS credentials invalid" "$EXIT_AWS_ERROR"
    [ "$status" -eq 4 ]
    assert_output_contains "[ERROR]"
    assert_output_contains "AWS credentials invalid"
}

# Test: log_command function
@test "log_command displays command with CMD prefix" {
    run log_command "kubectl get nodes"
    assert_success
    assert_output_contains "[CMD]"
    assert_output_contains "kubectl get nodes"
}

# Test: log_separator function
@test "log_separator displays separator line" {
    run log_separator
    assert_success
    assert_output_contains "======="
}

# Test: check_prereq succeeds when command exists
@test "check_prereq succeeds when command exists in PATH" {
    # Create mock command
    mock_command "testcmd" "mock output" 0

    run check_prereq "testcmd"
    assert_success
}

# Test: check_prereq fails when command not found
@test "check_prereq exits with error when command not found" {
    run check_prereq "nonexistent_command_12345"
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "Required command 'nonexistent_command_12345' not found"
}

# Test: check_prereq with installation URL
@test "check_prereq includes installation URL in error message when provided" {
    run check_prereq "nonexistent_cmd" "https://example.com/install"
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "Required command 'nonexistent_cmd' not found"
    assert_output_contains "https://example.com/install"
}

# Test: check_var succeeds when variable is set
@test "check_var succeeds when variable is set and non-empty" {
    export TEST_VAR="some value"
    run check_var "TEST_VAR"
    assert_success
}

# Test: check_var fails when variable is not set
@test "check_var exits with error when variable is not set" {
    unset TEST_VAR || true
    run check_var "TEST_VAR"
    [ "$status" -eq 1 ]  # EXIT_GENERAL_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "Variable TEST_VAR is not set"
}

# Test: check_var fails when variable is empty
@test "check_var exits with error when variable is empty" {
    export TEST_VAR=""
    run check_var "TEST_VAR"
    [ "$status" -eq 1 ]  # EXIT_GENERAL_ERROR
    assert_output_contains "[ERROR]"
}

# Test: check_var with custom error message
@test "check_var uses custom error message when provided" {
    unset CUSTOM_VAR || true
    run check_var "CUSTOM_VAR" "Custom error: CUSTOM_VAR must be set"
    [ "$status" -eq 1 ]
    assert_output_contains "Custom error: CUSTOM_VAR must be set"
}

# Test: Exit codes are defined correctly
@test "exit codes are defined with correct values" {
    [ "$EXIT_SUCCESS" -eq 0 ]
    [ "$EXIT_GENERAL_ERROR" -eq 1 ]
    [ "$EXIT_MISSING_PREREQ" -eq 2 ]
    [ "$EXIT_INVALID_ARGS" -eq 3 ]
    [ "$EXIT_AWS_ERROR" -eq 4 ]
    [ "$EXIT_CLUSTER_ERROR" -eq 5 ]
    [ "$EXIT_CROSSPLANE_ERROR" -eq 6 ]
}

# Test: Color codes are defined
@test "color codes are defined for output formatting" {
    [ -n "$COLOR_RESET" ]
    [ -n "$COLOR_BLUE" ]
    [ -n "$COLOR_GREEN" ]
    [ -n "$COLOR_RED" ]
    [ -n "$COLOR_YELLOW" ]
}

# Test: Multiple log messages work correctly
@test "multiple log functions can be called in sequence" {
    {
        log_info "Step 1"
        log_info "Step 2"
        log_success "Completed"
    } > "$TEST_TEMP_DIR/output.log" 2>&1

    run cat "$TEST_TEMP_DIR/output.log"
    assert_success
    assert_output_contains "Step 1"
    assert_output_contains "Step 2"
    assert_output_contains "Completed"
}
