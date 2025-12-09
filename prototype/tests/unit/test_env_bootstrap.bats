#!/usr/bin/env bats
# Unit tests for env-bootstrap.sh
# Tests KUBECONFIG setup, AWS credentials sourcing, and environment configuration

# Load test helpers
load ../test_helper

# Environment bootstrap script path
ENV_SCRIPT=""

setup() {
    setup_test_env
    ENV_SCRIPT="${PROTOTYPE_ROOT}/env-bootstrap.sh"

    # Create a mock .config directory structure
    mkdir -p "${TEST_TEMP_DIR}/.config"
}

teardown() {
    teardown_test_env
}

# ==============================================================================
# Script Execution Mode Tests
# ==============================================================================

# Test: Script cannot be executed directly
@test "env-bootstrap.sh exits with error when executed directly (not sourced)" {
    run "$ENV_SCRIPT"
    assert_failure
    assert_output_contains "This script must be sourced"
    assert_output_contains "source ./env-bootstrap.sh"
}

# Test: Script is executable
@test "env-bootstrap.sh is executable" {
    [ -x "$ENV_SCRIPT" ]
}

# Test: Script uses bash shebang
@test "env-bootstrap.sh uses bash shebang" {
    run head -n 1 "$ENV_SCRIPT"
    assert_success
    assert_output_contains "#!/usr/bin/env bash"
}

# ==============================================================================
# KUBECONFIG Setup Tests
# ==============================================================================

# Test: KUBECONFIG is set when config file exists
@test "env-bootstrap.sh sets KUBECONFIG when .config/mk8-bootstrap exists" {
    # Create mock kubeconfig file in prototype directory
    mkdir -p "${PROTOTYPE_ROOT}/.config"
    touch "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"

    # Source the script in a subshell and export KUBECONFIG
    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1; echo KUBECONFIG=\$KUBECONFIG"

    assert_success
    assert_output_contains "KUBECONFIG=${PROTOTYPE_ROOT}/.config/mk8-bootstrap"
    assert_output_contains "KUBECONFIG set to"

    # Clean up
    rm -f "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"
}

# Test: KUBECONFIG is set even when config file doesn't exist yet
@test "env-bootstrap.sh sets KUBECONFIG path even when file doesn't exist" {
    # Ensure kubeconfig file doesn't exist
    rm -f "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1; echo KUBECONFIG=\$KUBECONFIG"

    assert_success
    assert_output_contains "KUBECONFIG=${PROTOTYPE_ROOT}/.config/mk8-bootstrap"
    assert_output_contains "KUBECONFIG file not found"
    assert_output_contains "You may need to create the bootstrap cluster first"
}

# Test: Warning displayed when kubeconfig doesn't exist
@test "env-bootstrap.sh displays warning when kubeconfig file doesn't exist" {
    # Ensure kubeconfig doesn't exist
    rm -f "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "WARN"
    assert_output_contains "KUBECONFIG file not found"
    assert_output_contains "./mk8-prototype.sh bootstrap create"
}

# ==============================================================================
# AWS Credentials File Lookup Tests
# ==============================================================================

# Test: Loads from ~/.config/env-mk8-aws when it exists
@test "env-bootstrap.sh loads credentials from ~/.config/env-mk8-aws when it exists" {
    # Create home directory credentials file
    mkdir -p "${HOME}/.config"
    cat > "${HOME}/.config/env-mk8-aws" <<EOF
export MK8_AWS_ACCESS_KEY_ID="AKIA_HOME_CREDENTIALS"
export MK8_AWS_SECRET_ACCESS_KEY="home_secret_key"
export MK8_AWS_REGION="us-west-2"
EOF

    cd "$TEST_TEMP_DIR" || exit 1

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1; echo MK8_AWS_ACCESS_KEY_ID=\$MK8_AWS_ACCESS_KEY_ID; echo MK8_AWS_REGION=\$MK8_AWS_REGION"

    assert_success
    assert_output_contains "Loading AWS credentials from: ${HOME}/.config/env-mk8-aws"
    assert_output_contains "MK8_AWS_ACCESS_KEY_ID=AKIA_HOME_CREDENTIALS"
    assert_output_contains "MK8_AWS_REGION=us-west-2"

    # Clean up
    rm -f "${HOME}/.config/env-mk8-aws"
}

# Test: Falls back to template when home credentials don't exist
@test "env-bootstrap.sh falls back to template when ~/.config/env-mk8-aws doesn't exist" {
    # Ensure home credentials don't exist
    rm -f "${HOME}/.config/env-mk8-aws"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "Loading AWS credentials from template"
    assert_output_contains ".config/env-mk8-aws-template"
    assert_output_contains "Using TEMPLATE credentials"
}

# Test: Displays warning when using template credentials
@test "env-bootstrap.sh warns when using template (dummy) credentials" {
    # Ensure home credentials don't exist
    rm -f "${HOME}/.config/env-mk8-aws"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "WARN"
    assert_output_contains "Using TEMPLATE credentials"
    assert_output_contains "For real credentials, copy template to home directory"
    assert_output_contains "cp .config/env-mk8-aws-template"
}

# Test: Warns when no credentials file found
@test "env-bootstrap.sh warns when no credentials file is found" {
    # This test verifies the warning logic by checking the script behavior
    # when the template file is missing. We skip this test in the unit test suite
    # because it requires modifying the actual prototype directory structure.
    # The functionality is covered by manual testing and integration tests.
    skip "Skipping test that requires modifying prototype directory structure"
}

# ==============================================================================
# MK8_* Environment Variable Tests
# ==============================================================================

# Test: MK8_* variables are exported after sourcing
@test "env-bootstrap.sh exports MK8_* variables from credentials file" {
    # Ensure home credentials don't exist
    rm -f "${HOME}/.config/env-mk8-aws"

    # The template file should already exist with dummy credentials
    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1; echo KEY=\$MK8_AWS_ACCESS_KEY_ID; echo SECRET=\$MK8_AWS_SECRET_ACCESS_KEY; echo REGION=\$MK8_AWS_REGION"

    assert_success
    assert_output_contains "KEY=AKIAIOSFODNN7EXAMPLE"
    assert_output_contains "SECRET=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    assert_output_contains "REGION=us-east-1"
}

# Test: Displays masked access key
@test "env-bootstrap.sh displays masked access key (security)" {
    # Ensure home credentials don't exist
    rm -f "${HOME}/.config/env-mk8-aws"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "MK8_AWS_ACCESS_KEY_ID: AKIAIOSFODNN7EXA***"
    # Should NOT display the full access key in the message (only shows first 16 chars + ***)
}

# Test: Displays region without masking
@test "env-bootstrap.sh displays AWS region without masking" {
    # Ensure home credentials don't exist
    rm -f "${HOME}/.config/env-mk8-aws"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "MK8_AWS_REGION: us-east-1"
}

# ==============================================================================
# Confirmation Message Tests
# ==============================================================================

# Test: Displays environment configured message
@test "env-bootstrap.sh displays environment configured message" {
    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "Environment configured for mk8-prototype"
}

# Test: Displays kubectl usage hint when kubeconfig exists
@test "env-bootstrap.sh displays kubectl usage hint when kubeconfig exists" {
    # Create mock kubeconfig in prototype directory
    mkdir -p "${PROTOTYPE_ROOT}/.config"
    touch "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "kubectl now points to mk8-bootstrap cluster"
    assert_output_contains "Try: kubectl get nodes"

    # Clean up
    rm -f "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"
}

# Test: Displays AWS config hint when credentials loaded
@test "env-bootstrap.sh displays AWS usage hint when credentials loaded" {
    # Ensure home credentials don't exist
    rm -f "${HOME}/.config/env-mk8-aws"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "AWS credentials loaded"
    assert_output_contains "Try: ./mk8-prototype.sh config"
}

# Test: Different message when kubeconfig doesn't exist yet
@test "env-bootstrap.sh displays different message when kubeconfig doesn't exist" {
    # Ensure kubeconfig doesn't exist
    rm -f "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "After creating bootstrap cluster, kubectl will work automatically"
}

# ==============================================================================
# Variable Cleanup Tests
# ==============================================================================

# Test: Temporary variables are cleaned up after sourcing
@test "env-bootstrap.sh cleans up temporary variables after execution" {
    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh > /dev/null 2>&1; env | grep -E '^_ENV|^_COLOR|^_AWS_ENV' || echo 'No temp vars found'"

    assert_success
    assert_output_contains "No temp vars found"
}

# Test: KUBECONFIG variable persists after sourcing
@test "env-bootstrap.sh KUBECONFIG variable persists after sourcing" {
    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh > /dev/null 2>&1; echo \$KUBECONFIG"

    assert_success
    assert_output_contains "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"
}

# Test: MK8_* variables persist after sourcing
@test "env-bootstrap.sh MK8_* variables persist after sourcing" {
    # Ensure home credentials don't exist
    rm -f "${HOME}/.config/env-mk8-aws"

    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh > /dev/null 2>&1; echo \$MK8_AWS_ACCESS_KEY_ID; echo \$MK8_AWS_REGION"

    assert_success
    assert_output_contains "AKIAIOSFODNN7EXAMPLE"
    assert_output_contains "us-east-1"
}

# ==============================================================================
# Integration Tests
# ==============================================================================

# Test: Can be sourced multiple times safely
@test "env-bootstrap.sh can be sourced multiple times without errors" {
    run bash -c "source ${PROTOTYPE_ROOT}/env-bootstrap.sh > /dev/null 2>&1; source ${PROTOTYPE_ROOT}/env-bootstrap.sh > /dev/null 2>&1; echo SUCCESS"

    assert_success
    assert_output_contains "SUCCESS"
}

# Test: Works with actual template file from prototype
@test "env-bootstrap.sh works with actual .config/env-mk8-aws-template file" {
    # Ensure home credentials don't interfere
    rm -f "${HOME}/.config/env-mk8-aws"

    cd "${PROTOTYPE_ROOT}" || exit 1

    run bash -c "source ./env-bootstrap.sh 2>&1"

    assert_success
    assert_output_contains "Loading AWS credentials from template"
    # Template should export MK8_* variables
    run bash -c "source ./env-bootstrap.sh > /dev/null 2>&1; echo \$MK8_AWS_ACCESS_KEY_ID"
    assert_success
    # Should have loaded the dummy credentials from template
    assert_output_contains "AKIAIOSFODNN7EXAMPLE"
}
