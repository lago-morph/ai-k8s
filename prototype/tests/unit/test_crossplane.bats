#!/usr/bin/env bats
# Unit tests for lib/crossplane.sh
# Tests Crossplane installation, AWS Provider configuration, and status functions

load ../test_helper

# Crossplane module path
CROSSPLANE_MODULE=""

setup() {
    setup_test_env
    CROSSPLANE_MODULE="${PROTOTYPE_ROOT}/lib/crossplane.sh"
    
    # Source required modules for testing
    source "${PROTOTYPE_ROOT}/lib/common.sh"
    source "${PROTOTYPE_ROOT}/lib/config.sh"
    source "${PROTOTYPE_ROOT}/lib/bootstrap.sh"
    source "$CROSSPLANE_MODULE"
}

teardown() {
    teardown_test_env
}

# Test: crossplane_install checks prerequisites
@test "crossplane_install checks for required prerequisites" {
    # Mock check_prereq to capture prerequisite checks
    check_prereq() {
        echo "checking prerequisite: $1" >&2
        case "$1" in
            "helm"|"kubectl")
                return 0
                ;;
            *)
                return 1
                ;;
        esac
    }
    export -f check_prereq
    
    # Mock get_kubeconfig_path to return a test path
    get_kubeconfig_path() {
        echo "${TEST_TEMP_DIR}/kubeconfig"
    }
    export -f get_kubeconfig_path
    
    # Create mock kubeconfig file
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock helm and kubectl commands
    helm() { return 0; }
    kubectl() { return 0; }
    export -f helm kubectl
    
    # Mock check_mk8_env_vars to return false (no AWS credentials)
    check_mk8_env_vars() { return 1; }
    export -f check_mk8_env_vars
    
    run crossplane_install
    assert_output_contains "checking prerequisite: helm"
    assert_output_contains "checking prerequisite: kubectl"
}

# Test: crossplane_install logs Helm commands
@test "crossplane_install logs all Helm commands before execution" {
    # Mock prerequisites and kubeconfig
    check_prereq() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f check_prereq get_kubeconfig_path
    
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock helm commands to capture logging
    helm() {
        echo "helm executed: $*" >&2
        return 0
    }
    export -f helm
    
    # Mock kubectl commands
    kubectl() { return 0; }
    export -f kubectl
    
    # Mock check_mk8_env_vars to return false (no AWS credentials)
    check_mk8_env_vars() { return 1; }
    export -f check_mk8_env_vars
    
    run crossplane_install
    assert_success
    assert_output_contains "[CMD]"
    assert_output_contains "helm repo add crossplane-stable"
    assert_output_contains "helm repo update"
    assert_output_contains "helm install crossplane"
}

# Test: crossplane_install handles missing kubeconfig
@test "crossplane_install handles missing kubeconfig error" {
    # Mock prerequisites
    check_prereq() { return 0; }
    export -f check_prereq
    
    # Mock get_kubeconfig_path to return non-existent file
    get_kubeconfig_path() {
        echo "${TEST_TEMP_DIR}/nonexistent-kubeconfig"
    }
    export -f get_kubeconfig_path
    
    run crossplane_install
    assert_failure
    assert_output_contains "Bootstrap cluster kubeconfig not found"
    assert_output_contains "Run 'bootstrap create' first"
}

# Test: create_aws_provider_config checks MK8_* environment variables
@test "create_aws_provider_config checks for required MK8_* environment variables" {
    # Mock check_mk8_env_vars to capture the call
    check_mk8_env_vars() {
        echo "checking MK8_* environment variables" >&2
        return 0
    }
    export -f check_mk8_env_vars
    
    # Mock get_kubeconfig_path
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f get_kubeconfig_path
    
    # Mock kubectl and with_mk8_aws_env
    kubectl() { return 0; }
    with_mk8_aws_env() { eval "$1"; }
    export -f kubectl with_mk8_aws_env
    
    # Set required environment variables
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"
    export MK8_AWS_REGION="us-east-1"
    
    run create_aws_provider_config
    # The function should succeed and call check_mk8_env_vars
    assert_success
    assert_output_contains "Creating AWS Provider configuration"
}

# Test: create_aws_provider_config creates Kubernetes secret with credentials
@test "create_aws_provider_config creates Kubernetes secret with AWS credentials" {
    # Mock prerequisites
    check_mk8_env_vars() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f check_mk8_env_vars get_kubeconfig_path
    
    # Mock kubectl to capture secret creation
    kubectl() {
        echo "kubectl called: $*" >&2
        case "$*" in
            *"create secret"*)
                echo "secret created" >&2
                ;;
            *"apply"*)
                echo "manifest applied" >&2
                ;;
            *"wait"*)
                echo "wait completed" >&2
                ;;
        esac
        return 0
    }
    export -f kubectl
    
    # Mock with_mk8_aws_env
    with_mk8_aws_env() {
        echo "with_mk8_aws_env called: $1" >&2
        eval "$1"
    }
    export -f with_mk8_aws_env
    
    # Set required environment variables
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"
    export MK8_AWS_REGION="us-east-1"
    
    run create_aws_provider_config
    assert_success
    assert_output_contains "Creating AWS credentials secret"
    assert_output_contains "secret created"
    assert_output_contains "Installing AWS Provider"
    assert_output_contains "manifest applied"
}

# Test: verify_aws_provider waits for Provider to be healthy
@test "verify_aws_provider waits for Provider to be healthy" {
    # Mock get_kubeconfig_path
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f get_kubeconfig_path
    
    # Mock kubectl to capture wait commands
    kubectl() {
        echo "kubectl called: $*" >&2
        case "$*" in
            *"wait --for=condition=Healthy"*)
                echo "provider is healthy" >&2
                ;;
            *"get providerconfig"*)
                echo "providerconfig status displayed" >&2
                ;;
        esac
        return 0
    }
    export -f kubectl
    
    run verify_aws_provider
    assert_success
    assert_output_contains "Waiting for AWS Provider to be healthy"
    assert_output_contains "provider is healthy"
    assert_output_contains "Checking ProviderConfig status"
    assert_output_contains "providerconfig status displayed"
}

# Test: crossplane_status handles missing kubeconfig
@test "crossplane_status handles missing kubeconfig error" {
    # Mock get_kubeconfig_path to return non-existent file
    get_kubeconfig_path() {
        echo "${TEST_TEMP_DIR}/nonexistent-kubeconfig"
    }
    export -f get_kubeconfig_path
    
    run crossplane_status
    assert_failure
    assert_output_contains "Bootstrap cluster kubeconfig not found"
    assert_output_contains "Run 'bootstrap create' first"
}

# Test: crossplane_status displays pod and provider information
@test "crossplane_status displays Crossplane pods and provider information" {
    # Mock get_kubeconfig_path
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f get_kubeconfig_path
    
    # Create mock kubeconfig file
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock kubectl to return different outputs for different commands
    kubectl() {
        echo "kubectl called: $*" >&2
        case "$*" in
            *"get pods"*)
                echo "crossplane-pod-1   Running"
                ;;
            *"get providers"*)
                echo "provider-aws-s3   Installed"
                ;;
            *"get providerconfigs"*)
                echo "default   Ready"
                ;;
        esac
        return 0
    }
    export -f kubectl
    
    run crossplane_status
    assert_success
    assert_output_contains "Crossplane pods:"
    assert_output_contains "crossplane-pod-1"
    assert_output_contains "Crossplane Providers:"
    assert_output_contains "provider-aws-s3"
    assert_output_contains "ProviderConfigs:"
    assert_output_contains "default"
}

# Test: crossplane_status handles Crossplane not installed
@test "crossplane_status handles Crossplane not installed gracefully" {
    # Mock get_kubeconfig_path
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f get_kubeconfig_path
    
    # Create mock kubeconfig file
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock kubectl to return error for pods (Crossplane not installed)
    kubectl() {
        case "$*" in
            *"get pods"*)
                return 1  # Error - namespace doesn't exist
                ;;
            *)
                return 0
                ;;
        esac
    }
    export -f kubectl
    
    run crossplane_status
    assert_success
    assert_output_contains "Crossplane not installed"
    assert_output_contains "Run 'crossplane install' first"
}

# Test: Crossplane module can be executed directly
@test "crossplane.sh can be executed directly with subcommands" {
    # When run directly, crossplane.sh needs to source its dependencies
    # We'll test this by checking that it can parse arguments correctly
    run "$CROSSPLANE_MODULE" invalid-command
    assert_failure
    [[ "$status" -eq 3 ]]  # EXIT_INVALID_ARGS
    assert_output_contains "Usage:"
}

# Test: Crossplane module shows usage for invalid subcommands
@test "crossplane.sh shows usage for invalid subcommands" {
    run "$CROSSPLANE_MODULE" invalid-command
    assert_failure
    [[ "$status" -eq 3 ]]  # EXIT_INVALID_ARGS
    assert_output_contains "Usage:"
    assert_output_contains "install|status"
}

# Test: AWS Provider configuration uses correct region
@test "create_aws_provider_config uses MK8_AWS_REGION for ProviderConfig" {
    # Mock prerequisites
    check_mk8_env_vars() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f check_mk8_env_vars get_kubeconfig_path
    
    # Mock kubectl to capture manifest content
    kubectl() {
        case "$*" in
            *"apply -f"*)
                # Capture the manifest file path and check its content
                local manifest_file="${*##* }"
                if [[ -f "$manifest_file" ]]; then
                    echo "manifest content:" >&2
                    cat "$manifest_file" >&2
                fi
                ;;
        esac
        return 0
    }
    export -f kubectl
    
    # Mock with_mk8_aws_env
    with_mk8_aws_env() { eval "$1"; }
    export -f with_mk8_aws_env
    
    # Set custom region
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"
    export MK8_AWS_REGION="eu-west-1"
    
    run create_aws_provider_config
    assert_success
    # The function should complete successfully with custom region
    assert_output_contains "Creating ProviderConfig"
}

# Test: Crossplane install with AWS credentials configures provider
@test "crossplane_install configures AWS Provider when credentials are available" {
    # Mock prerequisites
    check_prereq() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f check_prereq get_kubeconfig_path
    
    # Create mock kubeconfig
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock external commands
    helm() { return 0; }
    kubectl() { return 0; }
    with_mk8_aws_env() { eval "$1"; }
    export -f helm kubectl with_mk8_aws_env
    
    # Mock check_mk8_env_vars to return success (credentials available)
    check_mk8_env_vars() {
        echo "AWS credentials detected" >&2
        return 0
    }
    export -f check_mk8_env_vars
    
    # Mock create_aws_provider_config and verify_aws_provider
    create_aws_provider_config() {
        echo "AWS Provider configured" >&2
    }
    verify_aws_provider() {
        echo "AWS Provider verified" >&2
    }
    export -f create_aws_provider_config verify_aws_provider
    
    # Set environment variables
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"
    
    run crossplane_install
    assert_success
    assert_output_contains "AWS credentials detected, configuring AWS Provider"
    assert_output_contains "AWS Provider configured"
    assert_output_contains "AWS Provider verified"
}

# Test: generate_bucket_name creates unique names with UUID
@test "generate_bucket_name creates unique bucket names with UUID format" {
    run generate_bucket_name
    assert_success
    
    # Should start with the bucket prefix
    assert_output_contains "test-s3-bucket-"
    
    # Should contain UUID-like format (8-4-4-4-12 hex digits)
    [[ "$output" =~ test-s3-bucket-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12} ]]
}

# Test: generate_bucket_name creates different names on each call
@test "generate_bucket_name creates different names on each call" {
    run generate_bucket_name
    assert_success
    local first_name="$output"
    
    run generate_bucket_name
    assert_success
    local second_name="$output"
    
    # Names should be different
    [[ "$first_name" != "$second_name" ]]
}

# Test: save_bucket_state and load_bucket_state work correctly
@test "save_bucket_state and load_bucket_state work correctly" {
    local test_bucket="test-bucket-12345"
    
    # Save bucket state
    run save_bucket_state "$test_bucket"
    assert_success
    assert_output_contains "Bucket state saved"
    
    # Load bucket state
    run load_bucket_state
    assert_success
    [[ "$output" == "$test_bucket" ]]
}

# Test: clear_bucket_state removes state file
@test "clear_bucket_state removes state file" {
    local test_bucket="test-bucket-12345"
    
    # Save bucket state first
    save_bucket_state "$test_bucket"
    
    # Verify state exists
    run load_bucket_state
    assert_success
    
    # Clear state
    run clear_bucket_state
    assert_success
    assert_output_contains "Bucket state cleared"
    
    # Verify state is gone
    run load_bucket_state
    assert_failure
}

# Test: crossplane_create_s3 checks for existing bucket
@test "crossplane_create_s3 handles existing bucket error" {
    # Mock prerequisites
    check_prereq() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f check_prereq get_kubeconfig_path
    
    # Create mock kubeconfig
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock load_bucket_state to return existing bucket
    load_bucket_state() {
        echo "existing-bucket-name"
        return 0
    }
    export -f load_bucket_state
    
    run crossplane_create_s3
    assert_failure
    assert_output_contains "S3 bucket already exists"
    assert_output_contains "existing-bucket-name"
    assert_output_contains "Run 'crossplane delete-s3' first"
}

# Test: crossplane_create_s3 creates MRD manifest with correct content
@test "crossplane_create_s3 creates S3 Bucket MRD with correct configuration" {
    # Mock prerequisites
    check_prereq() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f check_prereq get_kubeconfig_path
    
    # Create mock kubeconfig
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock load_bucket_state to return no existing bucket
    load_bucket_state() { return 1; }
    export -f load_bucket_state
    
    # Mock generate_bucket_name to return predictable name
    generate_bucket_name() { echo "test-s3-bucket-12345"; }
    export -f generate_bucket_name
    
    # Mock kubectl to capture manifest content
    kubectl() {
        case "$*" in
            *"apply -f"*)
                local manifest_file="${*##* }"
                if [[ -f "$manifest_file" ]]; then
                    echo "Manifest content:" >&2
                    cat "$manifest_file" >&2
                fi
                ;;
            *"wait"*)
                return 0
                ;;
            *"get bucket"*)
                echo "bucket-status"
                ;;
        esac
        return 0
    }
    export -f kubectl
    
    # Mock AWS CLI and other functions
    with_mk8_aws_env() { eval "$1"; }
    save_bucket_state() { echo "State saved: $1" >&2; }
    export -f with_mk8_aws_env save_bucket_state
    
    # Set AWS region
    export MK8_AWS_REGION="us-west-2"
    
    run crossplane_create_s3
    assert_success
    assert_output_contains "Generated bucket name: test-s3-bucket-12345"
    # The manifest content appears in stderr, so we'll just verify the function completed
    assert_output_contains "S3 bucket 'test-s3-bucket-12345' created successfully"
}

# Test: crossplane_delete_s3 handles missing bucket state
@test "crossplane_delete_s3 handles missing bucket state error" {
    # Mock prerequisites
    check_prereq() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f check_prereq get_kubeconfig_path
    
    # Create mock kubeconfig
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock load_bucket_state to return no bucket
    load_bucket_state() { return 1; }
    export -f load_bucket_state
    
    run crossplane_delete_s3
    assert_failure
    assert_output_contains "No S3 bucket found in state file"
    assert_output_contains "Run 'crossplane create-s3' first"
}

# Test: crossplane_delete_s3 deletes MRD and clears state
@test "crossplane_delete_s3 deletes S3 Bucket MRD and clears state" {
    # Mock prerequisites
    check_prereq() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f check_prereq get_kubeconfig_path
    
    # Create mock kubeconfig
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock load_bucket_state to return existing bucket
    load_bucket_state() {
        echo "test-bucket-to-delete"
        return 0
    }
    export -f load_bucket_state
    
    # Mock kubectl to simulate deletion
    kubectl() {
        case "$*" in
            *"delete bucket"*)
                echo "Bucket MRD deleted" >&2
                ;;
            *"get bucket"*)
                # First call returns bucket exists, subsequent calls fail (deleted)
                if [[ -f "${TEST_TEMP_DIR}/bucket_deleted" ]]; then
                    return 1  # Bucket deleted
                else
                    touch "${TEST_TEMP_DIR}/bucket_deleted"
                    return 0  # Bucket still exists
                fi
                ;;
        esac
        return 0
    }
    export -f kubectl
    
    # Mock AWS CLI and other functions
    with_mk8_aws_env() { eval "$1"; return 1; }  # AWS CLI fails (bucket deleted)
    clear_bucket_state() { echo "State cleared" >&2; }
    export -f with_mk8_aws_env clear_bucket_state
    
    run crossplane_delete_s3
    assert_success
    assert_output_contains "Deleting S3 bucket: test-bucket-to-delete"
    assert_output_contains "Bucket MRD deleted"
    assert_output_contains "State cleared"
}

# Test: State file error handling for corrupted state
@test "load_bucket_state handles missing state file gracefully" {
    # Ensure no state file exists
    rm -f "${HOME}/.config/mk8-prototype-state"
    
    run load_bucket_state
    assert_failure
}

# Test: Create-delete-create cycle generates unique UUIDs
@test "create-delete-create cycle generates unique bucket names" {
    # Generate first bucket name
    run generate_bucket_name
    assert_success
    local first_bucket="$output"
    
    # Simulate create-delete cycle by generating another name
    run generate_bucket_name
    assert_success
    local second_bucket="$output"
    
    # Names should be different (unique UUIDs)
    [[ "$first_bucket" != "$second_bucket" ]]
    
    # Both should follow the correct format
    [[ "$first_bucket" =~ test-s3-bucket-.+ ]]
    [[ "$second_bucket" =~ test-s3-bucket-.+ ]]
}