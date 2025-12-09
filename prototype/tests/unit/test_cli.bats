#!/usr/bin/env bats
# Unit tests for mk8-prototype.sh CLI framework
# Tests command-line argument parsing, command routing, and error handling

# Load test helpers
load ../test_helper

# Main CLI script path
CLI_SCRIPT=""

setup() {
    setup_test_env
    CLI_SCRIPT="${PROTOTYPE_ROOT}/mk8-prototype.sh"
}

teardown() {
    teardown_test_env
}

# ==============================================================================
# CLI Argument Parsing Tests
# ==============================================================================

# Test: No arguments displays usage
@test "invoking CLI with no arguments displays usage information" {
    run "$CLI_SCRIPT"
    [ "$status" -eq 3 ]  # EXIT_INVALID_ARGS
    assert_output_contains "Error: No command specified"
    assert_output_contains "USAGE:"
    assert_output_contains "./mk8-prototype.sh <command>"
}

# Test: Help flag displays help
@test "invoking CLI with --help flag displays help information" {
    run "$CLI_SCRIPT" --help
    assert_success
    assert_output_contains "mk8-prototype"
    assert_output_contains "USAGE:"
    assert_output_contains "COMMANDS:"
    assert_output_contains "version"
    assert_output_contains "config"
    assert_output_contains "bootstrap"
    assert_output_contains "crossplane"
}

# Test: Help command displays help
@test "invoking CLI with 'help' command displays help information" {
    run "$CLI_SCRIPT" help
    assert_success
    assert_output_contains "mk8-prototype"
    assert_output_contains "USAGE:"
    assert_output_contains "COMMANDS:"
}

# Test: Short help flag displays help
@test "invoking CLI with -h flag displays help information" {
    run "$CLI_SCRIPT" -h
    assert_success
    assert_output_contains "USAGE:"
    assert_output_contains "COMMANDS:"
}

# Test: Version flag displays version
@test "invoking CLI with --version flag displays version information" {
    run "$CLI_SCRIPT" --version
    assert_success
    assert_output_contains "mk8-prototype version"
    assert_output_contains "0.1.0-prototype"
}

# Test: Version command displays version
@test "invoking CLI with 'version' command displays version information" {
    run "$CLI_SCRIPT" version
    assert_success
    assert_output_contains "mk8-prototype version"
    assert_output_contains "bash-based implementation"
}

# Test: Short version flag displays version
@test "invoking CLI with -v flag displays version information" {
    run "$CLI_SCRIPT" -v
    assert_success
    assert_output_contains "mk8-prototype version"
}

# ==============================================================================
# Command Routing Tests - Valid Commands
# ==============================================================================

# Test: Config command routes correctly
@test "invoking 'config' command routes to config handler" {
    run "$CLI_SCRIPT" config
    # Config is now implemented, so it will fail due to missing env vars
    assert_failure
    [ "$status" -eq 4 ]  # EXIT_AWS_ERROR
    assert_output_contains "Missing required environment variables"
    assert_output_contains "MK8_AWS_ACCESS_KEY_ID"
}

# Test: Bootstrap create command routes correctly
@test "invoking 'bootstrap create' command routes to bootstrap handler" {
    run "$CLI_SCRIPT" bootstrap create
    # Should fail because bootstrap create is not yet implemented, but routing works
    assert_failure
    assert_output_contains "Bootstrap create not yet implemented"
}

# Test: Bootstrap status command routes correctly
@test "invoking 'bootstrap status' command routes to bootstrap handler" {
    run "$CLI_SCRIPT" bootstrap status
    # Should fail because bootstrap status is not yet implemented, but routing works
    assert_failure
    assert_output_contains "Bootstrap status not yet implemented"
}

# Test: Bootstrap delete command routes correctly
@test "invoking 'bootstrap delete' command routes to bootstrap handler" {
    run "$CLI_SCRIPT" bootstrap delete
    # Should fail because bootstrap delete is not yet implemented, but routing works
    assert_failure
    assert_output_contains "Bootstrap delete not yet implemented"
}

# Test: Crossplane install command routes correctly
@test "invoking 'crossplane install' command routes to crossplane handler" {
    run "$CLI_SCRIPT" crossplane install
    # Should fail because crossplane install is not yet implemented, but routing works
    assert_failure
    assert_output_contains "Crossplane install not yet implemented"
}

# Test: Crossplane status command routes correctly
@test "invoking 'crossplane status' command routes to crossplane handler" {
    run "$CLI_SCRIPT" crossplane status
    # Should fail because crossplane status is not yet implemented, but routing works
    assert_failure
    assert_output_contains "Crossplane status not yet implemented"
}

# Test: Crossplane create-s3 command routes correctly
@test "invoking 'crossplane create-s3' command routes to crossplane handler" {
    run "$CLI_SCRIPT" crossplane create-s3
    # Should fail because crossplane create-s3 is not yet implemented, but routing works
    assert_failure
    assert_output_contains "Crossplane create-s3 not yet implemented"
}

# Test: Crossplane delete-s3 command routes correctly
@test "invoking 'crossplane delete-s3' command routes to crossplane handler" {
    run "$CLI_SCRIPT" crossplane delete-s3
    # Should fail because crossplane delete-s3 is not yet implemented, but routing works
    assert_failure
    assert_output_contains "Crossplane delete-s3 not yet implemented"
}

# ==============================================================================
# Command Routing Tests - Invalid Commands
# ==============================================================================

# Test: Unknown top-level command displays error
@test "invoking CLI with unknown command displays error and exits with code 3" {
    run "$CLI_SCRIPT" invalid-command
    [ "$status" -eq 3 ]  # EXIT_INVALID_ARGS
    assert_output_contains "[ERROR]"
    assert_output_contains "Unknown command: 'invalid-command'"
    assert_output_contains "Run './mk8-prototype.sh help' for usage information"
}

# Test: Unknown bootstrap subcommand displays error
@test "invoking 'bootstrap' with unknown subcommand displays error and exits with code 3" {
    run "$CLI_SCRIPT" bootstrap invalid-subcommand
    [ "$status" -eq 3 ]  # EXIT_INVALID_ARGS
    assert_output_contains "[ERROR]"
    assert_output_contains "Unknown bootstrap subcommand: 'invalid-subcommand'"
    assert_output_contains "Valid subcommands: create, status, delete"
}

# Test: Bootstrap without subcommand displays error
@test "invoking 'bootstrap' without subcommand displays error" {
    run "$CLI_SCRIPT" bootstrap
    [ "$status" -eq 3 ]  # EXIT_INVALID_ARGS
    assert_output_contains "[ERROR]"
    assert_output_contains "Unknown bootstrap subcommand: ''"
    assert_output_contains "Valid subcommands: create, status, delete"
}

# Test: Unknown crossplane subcommand displays error
@test "invoking 'crossplane' with unknown subcommand displays error and exits with code 3" {
    run "$CLI_SCRIPT" crossplane invalid-subcommand
    [ "$status" -eq 3 ]  # EXIT_INVALID_ARGS
    assert_output_contains "[ERROR]"
    assert_output_contains "Unknown crossplane subcommand: 'invalid-subcommand'"
    assert_output_contains "Valid subcommands: install, status, create-s3, delete-s3"
}

# Test: Crossplane without subcommand displays error
@test "invoking 'crossplane' without subcommand displays error" {
    run "$CLI_SCRIPT" crossplane
    [ "$status" -eq 3 ]  # EXIT_INVALID_ARGS
    assert_output_contains "[ERROR]"
    assert_output_contains "Unknown crossplane subcommand: ''"
    assert_output_contains "Valid subcommands: install, status, create-s3, delete-s3"
}

# ==============================================================================
# Help and Usage Display Tests
# ==============================================================================

# Test: Help displays all main commands
@test "help output includes all main commands" {
    run "$CLI_SCRIPT" help
    assert_success
    assert_output_contains "version"
    assert_output_contains "config"
    assert_output_contains "bootstrap create"
    assert_output_contains "bootstrap status"
    assert_output_contains "bootstrap delete"
    assert_output_contains "crossplane install"
    assert_output_contains "crossplane status"
    assert_output_contains "crossplane create-s3"
    assert_output_contains "crossplane delete-s3"
}

# Test: Help displays environment variables
@test "help output includes environment variables section" {
    run "$CLI_SCRIPT" help
    assert_success
    assert_output_contains "ENVIRONMENT VARIABLES:"
    assert_output_contains "MK8_AWS_ACCESS_KEY_ID"
    assert_output_contains "MK8_AWS_SECRET_ACCESS_KEY"
    assert_output_contains "MK8_AWS_REGION"
    assert_output_contains "MK8_CLUSTER_NAME"
}

# Test: Help displays examples
@test "help output includes examples section" {
    run "$CLI_SCRIPT" help
    assert_success
    assert_output_contains "EXAMPLES:"
    assert_output_contains "env-bootstrap.sh"
    assert_output_contains "./mk8-prototype.sh config"
    assert_output_contains "./mk8-prototype.sh bootstrap create"
}

# Test: Help displays README reference
@test "help output includes reference to README" {
    run "$CLI_SCRIPT" help
    assert_success
    assert_output_contains "README.md"
}

# Test: Version output format
@test "version output displays correct format" {
    run "$CLI_SCRIPT" version
    assert_success
    assert_output_contains "mk8-prototype version 0.1.0-prototype"
    assert_output_contains "minimal, transparent bash-based implementation"
}

# ==============================================================================
# Error Handling Tests
# ==============================================================================

# Test: Multiple unknown arguments handled correctly
@test "invoking CLI with multiple unknown arguments displays error" {
    run "$CLI_SCRIPT" foo bar baz
    [ "$status" -eq 3 ]  # EXIT_INVALID_ARGS
    assert_output_contains "Unknown command: 'foo'"
}

# Test: Bootstrap with extra arguments
@test "invoking 'bootstrap create' with extra arguments still routes correctly" {
    run "$CLI_SCRIPT" bootstrap create extra-arg
    # Implementation not complete, but routing should work
    assert_failure
    # Should route to bootstrap create, not complain about extra-arg at CLI level
    assert_output_contains "Bootstrap create not yet implemented"
}

# Test: Crossplane with extra arguments
@test "invoking 'crossplane install' with extra arguments still routes correctly" {
    run "$CLI_SCRIPT" crossplane install extra-arg
    # Implementation not complete, but routing should work
    assert_failure
    # Should route to crossplane install, not complain about extra-arg at CLI level
    assert_output_contains "Crossplane install not yet implemented"
}

# ==============================================================================
# Script Execution Tests
# ==============================================================================

# Test: Script is executable
@test "mk8-prototype.sh script is executable" {
    [ -x "$CLI_SCRIPT" ]
}

# Test: Script uses correct shebang
@test "mk8-prototype.sh uses bash shebang" {
    run head -n 1 "$CLI_SCRIPT"
    assert_success
    assert_output_contains "#!/usr/bin/env bash"
}

# Test: Script sets errexit option
@test "mk8-prototype.sh sets strict error handling (set -euo pipefail)" {
    run grep -E "^set -euo pipefail" "$CLI_SCRIPT"
    assert_success
}
