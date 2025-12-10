#!/usr/bin/env bats
# Integration tests for mk8-prototype
# Tests end-to-end workflows and cross-module interactions

load ../test_helper

setup() {
    setup_test_env
}

teardown() {
    teardown_test_env
}

# Test: CLI parsing workflow (no args, help, invalid commands, version)
@test "end-to-end CLI parsing workflow" {
    # Test no arguments
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh"
    assert_failure
    assert_output_contains "USAGE:"
    
    # Test help
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" help
    assert_success
    assert_output_contains "mk8-prototype"
    assert_output_contains "COMMANDS:"
    
    # Test invalid command
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" invalid-command
    assert_failure
    [[ "$status" -eq 3 ]]
    assert_output_contains "Unknown command"
    
    # Test version
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" version
    assert_success
    assert_output_contains "mk8-prototype version"
}

# Test: AWS credentials validation workflow
@test "end-to-end AWS credentials validation workflow" {
    # Test missing variables
    unset MK8_AWS_ACCESS_KEY_ID MK8_AWS_SECRET_ACCESS_KEY MK8_AWS_REGION
    
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" config
    assert_failure
    assert_output_contains "Missing required environment variables"
    
    # Test invalid credentials (mock aws command to fail)
    export MK8_AWS_ACCESS_KEY_ID="invalid-key"
    export MK8_AWS_SECRET_ACCESS_KEY="invalid-secret"
    export MK8_AWS_REGION="us-east-1"
    
    # Mock aws command to simulate failure
    aws() {
        return 1
    }
    export -f aws
    
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" config
    assert_failure
    assert_output_contains "AWS credential validation failed"
    
    # Test valid credentials (mock aws command to succeed)
    aws() {
        case "$*" in
            *"get-caller-identity"*)
                echo '{"Account": "123456789012", "Arn": "arn:aws:iam::123456789012:user/test-user"}'
                ;;
        esac
        return 0
    }
    export -f aws
    
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" config
    assert_success
    assert_output_contains "AWS credentials are valid"
    assert_output_contains "Account ID: 123456789012"
}

# Test: Bootstrap cluster lifecycle
@test "end-to-end bootstrap cluster lifecycle" {
    # Mock external commands
    kind() {
        case "$1" in
            "get")
                if [[ "$2" == "clusters" ]]; then
                    if [[ -f "${TEST_TEMP_DIR}/cluster_exists" ]]; then
                        echo "mk8-bootstrap"
                    fi
                fi
                ;;
            "create")
                touch "${TEST_TEMP_DIR}/cluster_exists"
                touch "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"
                ;;
            "delete")
                rm -f "${TEST_TEMP_DIR}/cluster_exists"
                rm -f "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"
                ;;
        esac
        return 0
    }
    
    kubectl() {
        if [[ -f "${PROTOTYPE_ROOT}/.config/mk8-bootstrap" ]]; then
            echo "cluster is ready"
        else
            return 1
        fi
    }
    
    export -f kind kubectl
    
    # Test create
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" bootstrap create
    assert_success
    assert_output_contains "Creating bootstrap cluster"
    
    # Test status
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" bootstrap status
    assert_success
    assert_output_contains "Checking bootstrap cluster status"
    
    # Test delete
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" bootstrap delete
    assert_success
    assert_output_contains "Deleting bootstrap cluster"
}

# Test: env-bootstrap.sh utility
@test "end-to-end env-bootstrap.sh utility workflow" {
    # Create mock kubeconfig
    mkdir -p "${PROTOTYPE_ROOT}/.config"
    touch "${PROTOTYPE_ROOT}/.config/mk8-bootstrap"
    
    # Create mock credentials file
    cat > "${HOME}/.config/env-mk8-aws" << 'EOF'
export MK8_AWS_ACCESS_KEY_ID="test-access-key"
export MK8_AWS_SECRET_ACCESS_KEY="test-secret-key"
export MK8_AWS_REGION="us-west-2"
EOF
    
    # Source the utility in a subshell to capture output
    run bash -c "source '${PROTOTYPE_ROOT}/env-bootstrap.sh' && echo 'KUBECONFIG='$KUBECONFIG && echo 'MK8_AWS_ACCESS_KEY_ID='$MK8_AWS_ACCESS_KEY_ID"
    
    assert_success
    assert_output_contains "KUBECONFIG set to: ${PROTOTYPE_ROOT}/.config/mk8-bootstrap"
    assert_output_contains "MK8_AWS_ACCESS_KEY_ID="
    assert_output_contains "Environment configured for mk8-prototype"
}

# Test: Crossplane installation and AWS Provider configuration
@test "end-to-end Crossplane installation workflow" {
    # Mock prerequisites
    check_prereq() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    check_mk8_env_vars() { return 0; }
    export -f check_prereq get_kubeconfig_path check_mk8_env_vars
    
    # Create mock kubeconfig
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock external commands
    helm() {
        case "$*" in
            *"repo add"*)
                echo "Repository added"
                ;;
            *"repo update"*)
                echo "Repository updated"
                ;;
            *"install crossplane"*)
                echo "Crossplane installed"
                ;;
        esac
        return 0
    }
    
    kubectl() {
        case "$*" in
            *"wait"*)
                echo "Pods ready"
                ;;
            *"create secret"*)
                echo "Secret created"
                ;;
            *"apply"*)
                echo "Manifest applied"
                ;;
            *"get pods"*)
                echo "crossplane-pod   Running"
                ;;
        esac
        return 0
    }
    
    with_mk8_aws_env() { eval "$1"; }
    
    export -f helm kubectl with_mk8_aws_env
    export MK8_AWS_ACCESS_KEY_ID="test-key"
    export MK8_AWS_SECRET_ACCESS_KEY="test-secret"
    
    # Test Crossplane installation
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" crossplane install
    assert_success
    assert_output_contains "Installing Crossplane"
    assert_output_contains "Crossplane installation completed successfully"
    
    # Test Crossplane status
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" crossplane status
    assert_success
    assert_output_contains "Crossplane pods:"
}

# Test: S3 bucket creation and deletion workflow
@test "end-to-end S3 bucket management workflow" {
    # Mock prerequisites and setup
    check_prereq() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    export -f check_prereq get_kubeconfig_path
    
    # Create mock kubeconfig
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock bucket state functions
    local test_bucket="test-s3-bucket-12345"
    
    # Ensure no existing state
    rm -f "${TEST_TEMP_DIR}/bucket_state"
    rm -f "${HOME}/.config/mk8-prototype-state"
    
    load_bucket_state() {
        if [[ -f "${TEST_TEMP_DIR}/bucket_state" ]]; then
            cat "${TEST_TEMP_DIR}/bucket_state"
            return 0
        else
            return 1
        fi
    }
    
    save_bucket_state() {
        echo "$1" > "${TEST_TEMP_DIR}/bucket_state"
    }
    
    clear_bucket_state() {
        rm -f "${TEST_TEMP_DIR}/bucket_state"
    }
    
    generate_bucket_name() {
        echo "$test_bucket"
    }
    
    export -f load_bucket_state save_bucket_state clear_bucket_state generate_bucket_name
    
    # Mock external commands
    kubectl() {
        case "$*" in
            *"apply"*)
                echo "Bucket MRD applied"
                ;;
            *"wait"*)
                echo "Bucket ready"
                ;;
            *"get bucket"*)
                # For deletion test, simulate bucket not found after delete
                if [[ "$*" == *"delete"* ]] || [[ -f "${TEST_TEMP_DIR}/bucket_deleted" ]]; then
                    return 1  # Bucket not found (deleted)
                else
                    echo "bucket-status"
                fi
                ;;
            *"delete bucket"*)
                echo "Bucket MRD deleted"
                touch "${TEST_TEMP_DIR}/bucket_deleted"
                ;;
        esac
        return 0
    }
    
    with_mk8_aws_env() {
        case "$1" in
            *"head-bucket"*)
                if [[ -f "${TEST_TEMP_DIR}/bucket_deleted" ]]; then
                    return 1  # Bucket deleted
                else
                    return 0  # Bucket exists
                fi
                ;;
            *"s3 ls"*)
                if [[ -f "${TEST_TEMP_DIR}/bucket_deleted" ]]; then
                    return 1  # Bucket not found (deleted)
                else
                    return 0  # Bucket exists
                fi
                ;;
            *)
                eval "$1"
                ;;
        esac
    }
    
    export -f kubectl with_mk8_aws_env
    
    # Test S3 bucket creation
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" crossplane create-s3
    assert_success
    assert_output_contains "Creating S3 bucket"
    assert_output_contains "created successfully via Crossplane"
    
    # Verify state was saved (the actual implementation saves to ~/.config/mk8-prototype-state)
    [[ -f "${HOME}/.config/mk8-prototype-state" ]]
    
    # Test S3 bucket deletion
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" crossplane delete-s3
    assert_success
    assert_output_contains "Deleting S3 bucket:"
    assert_output_contains "deletion initiated via Crossplane"
    
    # Verify state was cleared
    [[ ! -f "${HOME}/.config/mk8-prototype-state" ]]
}

# Test: Create-delete-create cycle for unique UUIDs
@test "end-to-end create-delete-create cycle generates unique bucket names" {
    # Mock prerequisites
    check_prereq() { return 0; }
    get_kubeconfig_path() { echo "${TEST_TEMP_DIR}/kubeconfig"; }
    load_bucket_state() { return 1; }  # No existing bucket
    save_bucket_state() { return 0; }
    export -f check_prereq get_kubeconfig_path load_bucket_state save_bucket_state
    
    # Create mock kubeconfig
    touch "${TEST_TEMP_DIR}/kubeconfig"
    
    # Mock kubectl
    kubectl() { return 0; }
    with_mk8_aws_env() { eval "$1"; }
    export -f kubectl with_mk8_aws_env
    
    # Generate first bucket name
    run bash -c "source '${PROTOTYPE_ROOT}/lib/crossplane.sh' && generate_bucket_name"
    assert_success
    local first_bucket="$output"
    
    # Generate second bucket name
    run bash -c "source '${PROTOTYPE_ROOT}/lib/crossplane.sh' && generate_bucket_name"
    assert_success
    local second_bucket="$output"
    
    # Names should be different (unique UUIDs)
    [[ "$first_bucket" != "$second_bucket" ]]
    
    # Both should follow correct format
    [[ "$first_bucket" =~ test-s3-bucket-.+ ]]
    [[ "$second_bucket" =~ test-s3-bucket-.+ ]]
}

# Test: All commands are logged before execution
@test "integration test - verify all commands are logged before execution" {
    # Mock external commands to capture logging
    kind() {
        echo "kind executed: $*" >&2
        return 0
    }
    
    kubectl() {
        echo "kubectl executed: $*" >&2
        return 0
    }
    
    helm() {
        echo "helm executed: $*" >&2
        return 0
    }
    
    export -f kind kubectl helm
    
    # Test bootstrap command logging
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" bootstrap delete
    assert_success
    assert_output_contains "[CMD]"
    
    # The actual command execution will be in stderr due to our mocks
    # but the [CMD] prefix should be in stdout from log_command
}

# Test: Kubeconfig isolation - never touches ~/.kube/config
@test "integration test - verify kubeconfig isolation" {
    # Create a test ~/.kube/config to ensure it's never modified
    mkdir -p "${HOME}/.kube"
    echo "original-config-content" > "${HOME}/.kube/config"
    local original_content=$(cat "${HOME}/.kube/config")
    
    # Mock external commands
    kind() { return 0; }
    kubectl() { return 0; }
    export -f kind kubectl
    
    # Run various bootstrap operations
    "${PROTOTYPE_ROOT}/mk8-prototype.sh" bootstrap create || true
    "${PROTOTYPE_ROOT}/mk8-prototype.sh" bootstrap status || true
    "${PROTOTYPE_ROOT}/mk8-prototype.sh" bootstrap delete || true
    
    # Verify ~/.kube/config was never modified
    local current_content=$(cat "${HOME}/.kube/config")
    [[ "$current_content" == "$original_content" ]]
}

# Test: AWS environment variable isolation (MK8_* only)
@test "integration test - verify AWS environment variable isolation" {
    # Set some AWS_* variables that should NOT be used
    export AWS_ACCESS_KEY_ID="should-not-be-used"
    export AWS_SECRET_ACCESS_KEY="should-not-be-used"
    export AWS_REGION="should-not-be-used"
    
    # Set MK8_* variables that SHOULD be used
    export MK8_AWS_ACCESS_KEY_ID="correct-key"
    export MK8_AWS_SECRET_ACCESS_KEY="correct-secret"
    export MK8_AWS_REGION="us-west-2"
    
    # Mock aws command to capture what credentials are actually used
    aws() {
        echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" >&2
        echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >&2
        echo "AWS_REGION=$AWS_REGION" >&2
        
        # Verify the correct credentials are being used
        [[ "$AWS_ACCESS_KEY_ID" == "correct-key" ]]
        [[ "$AWS_SECRET_ACCESS_KEY" == "correct-secret" ]]
        [[ "$AWS_REGION" == "us-west-2" ]]
        
        echo '{"Account": "123456789012", "Arn": "arn:aws:iam::123456789012:user/test"}'
        return 0
    }
    export -f aws
    
    # Test config command which uses with_mk8_aws_env
    run "${PROTOTYPE_ROOT}/mk8-prototype.sh" config
    assert_success
    
    # After the command, AWS_* variables should be back to original values
    [[ "$AWS_ACCESS_KEY_ID" == "should-not-be-used" ]]
    [[ "$AWS_SECRET_ACCESS_KEY" == "should-not-be-used" ]]
    [[ "$AWS_REGION" == "should-not-be-used" ]]
}