#!/usr/bin/env bats
# Unit tests for lib/config.sh
# Tests AWS credential management, validation, and isolation

# Load test helpers
load ../test_helper

# Source the config library
setup() {
    setup_test_env

    # Source common.sh and config.sh
    source "${PROTOTYPE_ROOT}/lib/common.sh"
    source "${PROTOTYPE_ROOT}/lib/config.sh"

    # Set default test credentials
    export MK8_AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
    export MK8_AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    export MK8_AWS_REGION="us-east-1"
}

teardown() {
    # Clean up environment variables
    unset MK8_AWS_ACCESS_KEY_ID
    unset MK8_AWS_SECRET_ACCESS_KEY
    unset MK8_AWS_REGION
    unset AWS_ACCESS_KEY_ID
    unset AWS_SECRET_ACCESS_KEY
    unset AWS_REGION

    teardown_test_env
}

# ==============================================================================
# Environment Variable Checking Tests
# ==============================================================================

# Test: check_mk8_env_vars succeeds when all variables are set
@test "check_mk8_env_vars succeeds when all required MK8_* variables are set" {
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"

    run check_mk8_env_vars
    assert_success
}

# Test: check_mk8_env_vars fails when MK8_AWS_ACCESS_KEY_ID is missing
@test "check_mk8_env_vars exits with error when MK8_AWS_ACCESS_KEY_ID is missing" {
    unset MK8_AWS_ACCESS_KEY_ID
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"

    run check_mk8_env_vars
    [ "$status" -eq 4 ]  # EXIT_AWS_ERROR
    assert_output_contains "Missing required environment variables"
    assert_output_contains "MK8_AWS_ACCESS_KEY_ID"
}

# Test: check_mk8_env_vars fails when MK8_AWS_SECRET_ACCESS_KEY is missing
@test "check_mk8_env_vars exits with error when MK8_AWS_SECRET_ACCESS_KEY is missing" {
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    unset MK8_AWS_SECRET_ACCESS_KEY

    run check_mk8_env_vars
    [ "$status" -eq 4 ]  # EXIT_AWS_ERROR
    assert_output_contains "Missing required environment variables"
    assert_output_contains "MK8_AWS_SECRET_ACCESS_KEY"
}

# Test: check_mk8_env_vars fails when both variables are missing
@test "check_mk8_env_vars lists all missing variables when multiple are unset" {
    unset MK8_AWS_ACCESS_KEY_ID
    unset MK8_AWS_SECRET_ACCESS_KEY

    run check_mk8_env_vars
    [ "$status" -eq 4 ]  # EXIT_AWS_ERROR
    assert_output_contains "Missing required environment variables"
    assert_output_contains "MK8_AWS_ACCESS_KEY_ID"
    assert_output_contains "MK8_AWS_SECRET_ACCESS_KEY"
}

# Test: check_mk8_env_vars includes usage hint in error message
@test "check_mk8_env_vars error message includes env-bootstrap.sh hint" {
    unset MK8_AWS_ACCESS_KEY_ID

    run check_mk8_env_vars
    [ "$status" -eq 4 ]  # EXIT_AWS_ERROR
    assert_output_contains "source ./env-bootstrap.sh"
}

# Test: MK8_AWS_REGION is optional (has default)
@test "check_mk8_env_vars succeeds when MK8_AWS_REGION is not set (has default)" {
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"
    unset MK8_AWS_REGION

    run check_mk8_env_vars
    assert_success
}

# ==============================================================================
# AWS Environment Variable Isolation Tests
# ==============================================================================

# Test: with_mk8_aws_env maps MK8_* to AWS_* temporarily
@test "with_mk8_aws_env temporarily maps MK8_* variables to AWS_* variables" {
    export MK8_AWS_ACCESS_KEY_ID="test-key-123"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret-456"
    export MK8_AWS_REGION="us-west-2"

    # Create a test script that prints AWS_* variables
    cat > "${TEST_TEMP_DIR}/test_env.sh" <<'EOF'
#!/usr/bin/env bash
echo "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}"
echo "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}"
echo "AWS_REGION=${AWS_REGION}"
EOF
    chmod +x "${TEST_TEMP_DIR}/test_env.sh"

    run with_mk8_aws_env "${TEST_TEMP_DIR}/test_env.sh"
    assert_success
    assert_output_contains "AWS_ACCESS_KEY_ID=test-key-123"
    assert_output_contains "AWS_SECRET_ACCESS_KEY=test-secret-456"
    assert_output_contains "AWS_REGION=us-west-2"
}

# Test: Standard AWS_* variables are not set outside subshell
@test "standard AWS_* variables remain unset after with_mk8_aws_env call" {
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"

    # Ensure AWS_* variables are NOT set initially
    unset AWS_ACCESS_KEY_ID
    unset AWS_SECRET_ACCESS_KEY
    unset AWS_REGION

    # Call with_mk8_aws_env
    with_mk8_aws_env "echo 'test'" > /dev/null

    # Verify AWS_* variables are still NOT set after the call
    [ -z "${AWS_ACCESS_KEY_ID:-}" ]
    [ -z "${AWS_SECRET_ACCESS_KEY:-}" ]
}

# Test: with_mk8_aws_env uses default region when MK8_AWS_REGION not set
@test "with_mk8_aws_env uses default region (us-east-1) when MK8_AWS_REGION not set" {
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"
    unset MK8_AWS_REGION

    cat > "${TEST_TEMP_DIR}/test_region.sh" <<'EOF'
#!/usr/bin/env bash
echo "AWS_REGION=${AWS_REGION}"
EOF
    chmod +x "${TEST_TEMP_DIR}/test_region.sh"

    run with_mk8_aws_env "${TEST_TEMP_DIR}/test_region.sh"
    assert_success
    assert_output_contains "AWS_REGION=us-east-1"
}

# Test: with_mk8_aws_env passes command exit code
@test "with_mk8_aws_env preserves exit code from executed command" {
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"

    # Test successful command
    run with_mk8_aws_env "exit 0"
    [ "$status" -eq 0 ]

    # Test failing command
    run with_mk8_aws_env "exit 42"
    [ "$status" -eq 42 ]
}

# Test: with_mk8_aws_env executes command with correct arguments
@test "with_mk8_aws_env executes command with all arguments preserved" {
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"

    run with_mk8_aws_env "echo arg1 arg2 arg3"
    assert_success
    assert_output_contains "arg1 arg2 arg3"
}

# ==============================================================================
# Credential Validation Tests
# ==============================================================================

# Test: validate_aws_credentials requires aws CLI
@test "validate_aws_credentials checks for aws CLI prerequisite" {
    # Remove aws from PATH
    export PATH="/nonexistent/path"

    run validate_aws_credentials
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "Required command 'aws' not found"
}

# Test: validate_aws_credentials checks for MK8_* variables
@test "validate_aws_credentials checks for required MK8_* environment variables" {
    # Mock aws command
    mock_command "aws" "success" 0

    unset MK8_AWS_ACCESS_KEY_ID

    run validate_aws_credentials
    [ "$status" -eq 4 ]  # EXIT_AWS_ERROR
    assert_output_contains "Missing required environment variables"
}

# Test: validate_aws_credentials calls AWS STS
@test "validate_aws_credentials calls 'aws sts get-caller-identity'" {
    # Create a mock aws command that logs the command
    mkdir -p "${TEST_TEMP_DIR}/bin"
    cat > "${TEST_TEMP_DIR}/bin/aws" <<'EOF'
#!/usr/bin/env bash
# Mock AWS CLI that succeeds for sts get-caller-identity
if [[ "$1" == "sts" ]] && [[ "$2" == "get-caller-identity" ]]; then
    echo '{"Account": "123456789012", "Arn": "arn:aws:iam::123456789012:user/test-user"}'
    exit 0
fi
echo "Unexpected aws command: $*" >&2
exit 1
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/aws"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"

    run validate_aws_credentials
    assert_success
    assert_output_contains "aws sts get-caller-identity"
    assert_output_contains "AWS credentials are valid"
}

# Test: validate_aws_credentials displays account information on success
@test "validate_aws_credentials displays account ID and user ARN on success" {
    # Mock successful AWS STS call
    mkdir -p "${TEST_TEMP_DIR}/bin"
    cat > "${TEST_TEMP_DIR}/bin/aws" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "sts" ]] && [[ "$2" == "get-caller-identity" ]]; then
    echo '{"Account": "999888777666", "Arn": "arn:aws:iam::999888777666:user/alice"}'
    exit 0
fi
exit 1
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/aws"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"

    run validate_aws_credentials
    assert_success
    assert_output_contains "Account ID: 999888777666"
    assert_output_contains "User/Role:  arn:aws:iam::999888777666:user/alice"
}

# Test: validate_aws_credentials exits with error when AWS call fails
@test "validate_aws_credentials exits with AWS_ERROR when STS call fails" {
    # Mock failing AWS STS call
    mkdir -p "${TEST_TEMP_DIR}/bin"
    cat > "${TEST_TEMP_DIR}/bin/aws" <<'EOF'
#!/usr/bin/env bash
echo "An error occurred (InvalidClientTokenId): The security token included in the request is invalid" >&2
exit 255
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/aws"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"

    run validate_aws_credentials
    [ "$status" -eq 4 ]  # EXIT_AWS_ERROR
    assert_output_contains "AWS credential validation failed"
}

# Test: validate_aws_credentials displays which MK8_* variables are being used
@test "validate_aws_credentials displays MK8_* variables being used (masked)" {
    # Mock successful AWS STS call
    mkdir -p "${TEST_TEMP_DIR}/bin"
    cat > "${TEST_TEMP_DIR}/bin/aws" <<'EOF'
#!/usr/bin/env bash
echo '{"Account": "123456789012", "Arn": "arn:aws:iam::123456789012:user/test"}'
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/aws"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"

    export MK8_AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
    export MK8_AWS_REGION="eu-west-1"

    run validate_aws_credentials
    assert_success
    assert_output_contains "Using MK8.*environment variables"
    # Should show masked access key (first 16 chars + ***)
    assert_output_contains "AKIAIOSFODNN7EXA"
    assert_output_contains "eu-west-1"
}

# Test: validate_aws_credentials displays default region when not set
@test "validate_aws_credentials displays default region when MK8_AWS_REGION not set" {
    # Mock successful AWS STS call
    mkdir -p "${TEST_TEMP_DIR}/bin"
    cat > "${TEST_TEMP_DIR}/bin/aws" <<'EOF'
#!/usr/bin/env bash
echo '{"Account": "123456789012", "Arn": "arn:aws:iam::123456789012:user/test"}'
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/aws"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"

    unset MK8_AWS_REGION

    run validate_aws_credentials
    assert_success
    assert_output_contains "MK8_AWS_REGION: us-east-1"
}

# ==============================================================================
# Configuration Constants Tests
# ==============================================================================

# Test: Default AWS region constant is defined
@test "DEFAULT_AWS_REGION constant is defined as us-east-1" {
    [ "$DEFAULT_AWS_REGION" = "us-east-1" ]
}

# Test: Required MK8 variables array is defined correctly
@test "REQUIRED_MK8_VARS array includes expected variables" {
    # Check array contains expected values
    [[ " ${REQUIRED_MK8_VARS[*]} " =~ " MK8_AWS_ACCESS_KEY_ID " ]]
    [[ " ${REQUIRED_MK8_VARS[*]} " =~ " MK8_AWS_SECRET_ACCESS_KEY " ]]
}

# ==============================================================================
# Integration Tests with CLI
# ==============================================================================

# Test: CLI config command uses validate_aws_credentials
@test "CLI 'config' command invokes validate_aws_credentials function" {
    # Mock successful AWS STS call
    mkdir -p "${TEST_TEMP_DIR}/bin"
    cat > "${TEST_TEMP_DIR}/bin/aws" <<'EOF'
#!/usr/bin/env bash
echo '{"Account": "123456789012", "Arn": "arn:aws:iam::123456789012:user/test"}'
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/aws"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"

    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" config
    assert_success
    assert_output_contains "Validating AWS credentials"
    assert_output_contains "AWS credentials are valid"
}
