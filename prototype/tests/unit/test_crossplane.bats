#!/usr/bin/env bats
# Unit tests for lib/crossplane.sh
# Tests Crossplane installation, AWS Provider configuration, and S3 bucket management

# Load test helpers
load ../test_helper

# Source the crossplane library
setup() {
    setup_test_env
    
    # Source required libraries
    source "${PROTOTYPE_ROOT}/lib/common.sh"
    source "${PROTOTYPE_ROOT}/lib/config.sh"
    source "${PROTOTYPE_ROOT}/lib/bootstrap.sh"
    source "${PROTOTYPE_ROOT}/lib/crossplane.sh"
    
    # Set up test config directory
    export CONFIG_DIR="${TEST_TEMP_DIR}/.config"
    mkdir -p "${CONFIG_DIR}"
    
    # Override KUBECONFIG_FILE for testing
    export KUBECONFIG_FILE="${CONFIG_DIR}/mk8-bootstrap"
    
    # Override STATE_FILE for testing
    export STATE_FILE="${TEST_TEMP_DIR}/.config/mk8-prototype-state"
    
    # Set up AWS credentials for testing
    export MK8_AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
    export MK8_AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    export MK8_AWS_REGION="us-east-1"
}

teardown() {
    teardown_test_env
}

# Test: crossplane_install checks for helm prerequisite
@test "crossplane_install fails when helm command not found" {
    run crossplane_install
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "helm"
}

# Test: crossplane_install checks for kubectl prerequisite
@test "crossplane_install fails when kubectl command not found" {
    mock_command "helm" "" 0
    
    run crossplane_install
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kubectl"
}

# Test: crossplane_install fails when kubeconfig not found
@test "crossplane_install fails when kubeconfig file does not exist" {
    mock_command "helm" "" 0
    mock_command "kubectl" "" 0
    
    # Ensure kubeconfig doesn't exist
    rm -f "${KUBECONFIG_FILE}"
    
    run crossplane_install
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "Kubeconfig not found"
}

# Test: crossplane_install logs helm repo add command
@test "crossplane_install logs helm repo add command" {
    mock_command "kubectl" "" 0
    
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock helm to fail on install (so we can see the repo add)
    cat > "${TEST_TEMP_DIR}/bin/helm" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "repo" ]] && [[ "$2" == "add" ]]; then
    exit 0
fi
if [[ "$1" == "repo" ]] && [[ "$2" == "update" ]]; then
    exit 0
fi
if [[ "$1" == "install" ]]; then
    exit 1  # Fail install
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/helm"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run crossplane_install
    assert_output_contains "[CMD]"
    assert_output_contains "helm repo add"
    assert_output_contains "crossplane-stable"
}

# Test: crossplane_install logs helm install command with parameters
@test "crossplane_install logs helm install command with all parameters" {
    mock_command "kubectl" "" 0
    
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock helm
    cat > "${TEST_TEMP_DIR}/bin/helm" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "repo" ]]; then
    exit 0
fi
if [[ "$1" == "install" ]]; then
    exit 1  # Fail for test purposes
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/helm"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run crossplane_install
    assert_output_contains "[CMD]"
    assert_output_contains "helm install"
    assert_output_contains "crossplane"
    assert_output_contains "--namespace"
    assert_output_contains "--version"
    assert_output_contains "--kubeconfig"
}

# Test: create_aws_provider_config checks for kubectl prerequisite
@test "create_aws_provider_config fails when kubectl command not found" {
    run create_aws_provider_config
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kubectl"
}

# Test: create_aws_provider_config fails when AWS credentials not set
@test "create_aws_provider_config fails when MK8_AWS_ACCESS_KEY_ID not set" {
    mock_command "kubectl" "" 0
    
    unset MK8_AWS_ACCESS_KEY_ID
    
    run create_aws_provider_config
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "AWS credentials not configured"
}

# Test: create_aws_provider_config uses MK8_* environment variables
@test "create_aws_provider_config uses MK8_AWS_* environment variables" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock kubectl to capture secret creation
    cat > "${TEST_TEMP_DIR}/bin/kubectl" <<'EOF'
#!/usr/bin/env bash
# Just succeed for all operations
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kubectl"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run create_aws_provider_config
    assert_output_contains "[CMD]"
    assert_output_contains "kubectl"
    assert_output_contains "create secret"
    assert_output_contains "aws-creds"
}

# Test: create_aws_provider_config logs kubectl commands
@test "create_aws_provider_config logs kubectl apply commands" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock kubectl
    mock_command "kubectl" "" 0
    
    run create_aws_provider_config
    assert_output_contains "[CMD]"
    assert_output_contains "kubectl"
}

# Test: verify_aws_provider checks for kubectl prerequisite
@test "verify_aws_provider fails when kubectl command not found" {
    run verify_aws_provider
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kubectl"
}

# Test: verify_aws_provider checks Provider status
@test "verify_aws_provider checks for AWS Provider" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock kubectl to fail on get provider
    cat > "${TEST_TEMP_DIR}/bin/kubectl" <<'EOF'
#!/usr/bin/env bash
if [[ "$2" == "get" ]] && [[ "$3" == "provider" ]]; then
    exit 1  # Provider not found
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kubectl"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run verify_aws_provider
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "AWS Provider not found"
}

# Test: crossplane_status checks for kubectl prerequisite
@test "crossplane_status fails when kubectl command not found" {
    run crossplane_status
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kubectl"
}

# Test: crossplane_status fails when kubeconfig not found
@test "crossplane_status fails when kubeconfig file does not exist" {
    mock_command "kubectl" "" 0
    
    # Ensure kubeconfig doesn't exist
    rm -f "${KUBECONFIG_FILE}"
    
    run crossplane_status
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "Kubeconfig not found"
}

# Test: crossplane_status fails when Crossplane namespace not found
@test "crossplane_status fails when Crossplane namespace does not exist" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock kubectl to fail on namespace check
    cat > "${TEST_TEMP_DIR}/bin/kubectl" <<'EOF'
#!/usr/bin/env bash
if [[ "$2" == "get" ]] && [[ "$3" == "namespace" ]]; then
    exit 1  # Namespace not found
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kubectl"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run crossplane_status
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "Crossplane namespace"
    assert_output_contains "not found"
}

# Test: crossplane_status displays pod status
@test "crossplane_status displays Crossplane pod status" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock kubectl
    cat > "${TEST_TEMP_DIR}/bin/kubectl" <<'EOF'
#!/usr/bin/env bash
if [[ "$2" == "get" ]] && [[ "$3" == "namespace" ]]; then
    exit 0  # Namespace exists
fi
if [[ "$2" == "get" ]] && [[ "$3" == "pods" ]]; then
    echo "NAME                                READY   STATUS    RESTARTS   AGE"
    echo "crossplane-7d8f9c8b9d-abc12         1/1     Running   0          5m"
    exit 0
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kubectl"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run crossplane_status
    assert_success
    assert_output_contains "Crossplane pods:"
}

# Test: generate_bucket_name creates unique names
@test "generate_bucket_name creates unique bucket names" {
    local name1
    local name2
    
    name1="$(generate_bucket_name)"
    name2="$(generate_bucket_name)"
    
    # Names should be different
    [ "$name1" != "$name2" ]
    
    # Names should have correct prefix
    assert_output_contains "test-s3-bucket"
}

# Test: generate_bucket_name format
@test "generate_bucket_name follows correct format" {
    run generate_bucket_name
    assert_success
    assert_output_contains "test-s3-bucket-"
    
    # Should have 8 character UUID after prefix
    local bucket_name="$output"
    local uuid_part="${bucket_name#test-s3-bucket-}"
    [ ${#uuid_part} -eq 8 ]
}

# Test: save_bucket_state creates state file
@test "save_bucket_state creates state file with bucket name" {
    local bucket_name="test-s3-bucket-abc12345"
    
    run save_bucket_state "${bucket_name}"
    assert_success
    
    # State file should exist
    assert_file_exists "${STATE_FILE}"
    
    # State file should contain bucket name
    local saved_name
    saved_name=$(cat "${STATE_FILE}")
    [ "$saved_name" = "$bucket_name" ]
}

# Test: save_bucket_state creates directory if needed
@test "save_bucket_state creates state directory if missing" {
    local bucket_name="test-s3-bucket-abc12345"
    
    # Remove state directory
    rm -rf "$(dirname "${STATE_FILE}")"
    
    run save_bucket_state "${bucket_name}"
    assert_success
    
    # Directory should be created
    assert_dir_exists "$(dirname "${STATE_FILE}")"
}

# Test: load_bucket_state returns bucket name
@test "load_bucket_state returns saved bucket name" {
    local bucket_name="test-s3-bucket-abc12345"
    
    # Save bucket name
    save_bucket_state "${bucket_name}"
    
    # Load bucket name
    run load_bucket_state
    assert_success
    [ "$output" = "$bucket_name" ]
}

# Test: load_bucket_state fails when state file doesn't exist
@test "load_bucket_state fails when state file does not exist" {
    # Ensure state file doesn't exist
    rm -f "${STATE_FILE}"
    
    run load_bucket_state
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
}

# Test: clear_bucket_state removes state file
@test "clear_bucket_state removes state file" {
    local bucket_name="test-s3-bucket-abc12345"
    
    # Create state file
    save_bucket_state "${bucket_name}"
    assert_file_exists "${STATE_FILE}"
    
    # Clear state
    run clear_bucket_state
    assert_success
    
    # State file should be removed
    if [[ -f "${STATE_FILE}" ]]; then
        echo "Expected state file to be removed: ${STATE_FILE}" >&2
        return 1
    fi
}

# Test: clear_bucket_state succeeds when state file doesn't exist
@test "clear_bucket_state succeeds when state file does not exist" {
    # Ensure state file doesn't exist
    rm -f "${STATE_FILE}"
    
    run clear_bucket_state
    assert_success
}

# Test: crossplane_create_s3 checks for kubectl prerequisite
@test "crossplane_create_s3 fails when kubectl command not found" {
    run crossplane_create_s3
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kubectl"
}

# Test: crossplane_create_s3 checks for aws prerequisite
@test "crossplane_create_s3 fails when aws command not found" {
    mock_command "kubectl" "" 0
    
    run crossplane_create_s3
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "aws"
}

# Test: crossplane_create_s3 fails when kubeconfig not found
@test "crossplane_create_s3 fails when kubeconfig file does not exist" {
    mock_command "kubectl" "" 0
    mock_command "aws" "" 0
    
    # Ensure kubeconfig doesn't exist
    rm -f "${KUBECONFIG_FILE}"
    
    run crossplane_create_s3
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "Kubeconfig not found"
}

# Test: crossplane_create_s3 fails when bucket already exists
@test "crossplane_create_s3 fails when bucket already exists in state" {
    mock_command "kubectl" "" 0
    mock_command "aws" "" 0
    
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Create existing bucket state
    save_bucket_state "test-s3-bucket-existing"
    
    run crossplane_create_s3
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "Bucket already exists"
}

# Test: crossplane_create_s3 generates unique bucket name
@test "crossplane_create_s3 generates unique bucket name" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock kubectl and aws to fail quickly
    mock_command "kubectl" "" 1
    mock_command "aws" "" 0
    
    run crossplane_create_s3
    assert_output_contains "Generated bucket name:"
    assert_output_contains "test-s3-bucket-"
}

# Test: crossplane_create_s3 logs kubectl apply command
@test "crossplane_create_s3 logs kubectl apply command for MRD" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock kubectl to fail on apply
    mock_command "kubectl" "" 1
    mock_command "aws" "" 0
    
    run crossplane_create_s3
    assert_output_contains "[CMD]"
    assert_output_contains "kubectl"
    assert_output_contains "apply"
}

# Test: crossplane_delete_s3 checks for kubectl prerequisite
@test "crossplane_delete_s3 fails when kubectl command not found" {
    run crossplane_delete_s3
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kubectl"
}

# Test: crossplane_delete_s3 checks for aws prerequisite
@test "crossplane_delete_s3 fails when aws command not found" {
    mock_command "kubectl" "" 0
    
    run crossplane_delete_s3
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "aws"
}

# Test: crossplane_delete_s3 fails when kubeconfig not found
@test "crossplane_delete_s3 fails when kubeconfig file does not exist" {
    mock_command "kubectl" "" 0
    mock_command "aws" "" 0
    
    # Ensure kubeconfig doesn't exist
    rm -f "${KUBECONFIG_FILE}"
    
    run crossplane_delete_s3
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "Kubeconfig not found"
}

# Test: crossplane_delete_s3 fails when no bucket in state
@test "crossplane_delete_s3 fails when no bucket found in state file" {
    mock_command "kubectl" "" 0
    mock_command "aws" "" 0
    
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Ensure state file doesn't exist
    rm -f "${STATE_FILE}"
    
    run crossplane_delete_s3
    [ "$status" -eq 6 ]  # EXIT_CROSSPLANE_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "No bucket found in state file"
}

# Test: crossplane_delete_s3 reads bucket name from state
@test "crossplane_delete_s3 reads bucket name from state file" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Create bucket state
    local bucket_name="test-s3-bucket-abc12345"
    save_bucket_state "${bucket_name}"
    
    # Mock kubectl and aws to fail quickly
    mock_command "kubectl" "" 1
    mock_command "aws" "" 0
    
    run crossplane_delete_s3
    assert_output_contains "Deleting bucket: ${bucket_name}"
}

# Test: crossplane_delete_s3 logs kubectl delete command
@test "crossplane_delete_s3 logs kubectl delete command" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Create bucket state
    save_bucket_state "test-s3-bucket-abc12345"
    
    # Mock kubectl to fail on delete
    mock_command "kubectl" "" 1
    mock_command "aws" "" 0
    
    run crossplane_delete_s3
    assert_output_contains "[CMD]"
    assert_output_contains "kubectl"
    assert_output_contains "delete bucket"
}

# Test: State file consistency - create-delete-create cycle
@test "create-delete-create cycle generates new UUID each time" {
    # This test verifies that each bucket creation gets a unique UUID
    
    # First creation
    local name1
    name1="$(generate_bucket_name)"
    
    # Second creation (simulating after delete)
    local name2
    name2="$(generate_bucket_name)"
    
    # Third creation
    local name3
    name3="$(generate_bucket_name)"
    
    # All names should be different
    [ "$name1" != "$name2" ]
    [ "$name2" != "$name3" ]
    [ "$name1" != "$name3" ]
}
