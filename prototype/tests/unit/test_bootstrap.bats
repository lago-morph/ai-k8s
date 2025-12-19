#!/usr/bin/env bats
# Unit tests for lib/bootstrap.sh
# Tests bootstrap cluster management functions

# Load test helpers
load ../test_helper

# Source the bootstrap library
setup() {
    setup_test_env
    
    # Source required libraries
    source "${PROTOTYPE_ROOT}/lib/common.sh"
    source "${PROTOTYPE_ROOT}/lib/bootstrap.sh"
    
    # Set up test config directory
    export CONFIG_DIR="${TEST_TEMP_DIR}/.config"
    mkdir -p "${CONFIG_DIR}"
    
    # Override KUBECONFIG_FILE for testing
    export KUBECONFIG_FILE="${CONFIG_DIR}/mk8-bootstrap"
}

teardown() {
    teardown_test_env
}

# Test: get_kubeconfig_path returns correct path
@test "get_kubeconfig_path returns path to isolated kubeconfig" {
    run get_kubeconfig_path
    assert_success
    assert_output_contains ".config"
    assert_output_contains "mk8-bootstrap"
}

# Test: get_kubeconfig_path uses consistent cluster name
@test "get_kubeconfig_path uses consistent cluster name across calls" {
    local path1
    local path2
    path1="$(get_kubeconfig_path)"
    path2="$(get_kubeconfig_path)"
    
    [ "$path1" = "$path2" ]
}

# Test: get_kubeconfig_path respects MK8_CLUSTER_NAME environment variable
@test "get_kubeconfig_path respects MK8_CLUSTER_NAME when set" {
    export MK8_CLUSTER_NAME="custom-cluster"
    # Need to re-source to pick up new cluster name
    source "${PROTOTYPE_ROOT}/lib/bootstrap.sh"
    
    run get_kubeconfig_path
    assert_success
    assert_output_contains "custom-cluster"
}

# Test: bootstrap_create checks for kind prerequisite
@test "bootstrap_create fails when kind command not found" {
    # Don't mock kind - let it fail naturally
    run bootstrap_create
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kind"
}

# Test: bootstrap_create checks for kubectl prerequisite
@test "bootstrap_create fails when kubectl command not found" {
    # Mock kind but not kubectl
    mock_command "kind" "mock kind output" 0
    
    run bootstrap_create
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kubectl"
}

# Test: bootstrap_create creates config directory if it doesn't exist
@test "bootstrap_create creates config directory if missing" {
    # Mock prerequisites
    mock_command "kind" "" 0
    mock_command "kubectl" "" 0
    
    # Remove config directory
    rm -rf "${CONFIG_DIR}"
    
    # Mock kind get clusters to return no clusters
    mock_command "kind" "" 0
    
    run bootstrap_create
    # Will fail because kind create will fail, but directory should be created
    assert_dir_exists "${CONFIG_DIR}"
}

# Test: bootstrap_create fails if cluster already exists
@test "bootstrap_create fails when cluster already exists" {
    # Mock prerequisites
    mock_command "kubectl" "" 0
    
    # Mock kind to show cluster exists
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    echo "mk8-bootstrap"
    exit 0
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run bootstrap_create
    [ "$status" -eq 5 ]  # EXIT_CLUSTER_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "already exists"
}

# Test: bootstrap_create logs kind command before execution
@test "bootstrap_create logs kind create command with parameters" {
    # Mock prerequisites
    mock_command "kubectl" "" 0
    
    # Mock kind to show no clusters exist, then fail on create
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    exit 0  # No clusters
fi
if [[ "$1" == "create" ]]; then
    exit 1  # Fail create
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run bootstrap_create
    assert_output_contains "[CMD]"
    assert_output_contains "kind create cluster"
    assert_output_contains "--name"
    assert_output_contains "--kubeconfig"
}

# Test: bootstrap_create uses isolated kubeconfig path
@test "bootstrap_create uses isolated kubeconfig not ~/.kube/config" {
    # Mock prerequisites
    mock_command "kubectl" "" 0
    
    # Mock kind
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    exit 0  # No clusters
fi
if [[ "$1" == "create" ]]; then
    # Check that kubeconfig is NOT ~/.kube/config
    for arg in "$@"; do
        if [[ "$arg" == *".kube/config"* ]]; then
            echo "ERROR: Using ~/.kube/config" >&2
            exit 1
        fi
    done
    exit 1  # Fail for test purposes
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run bootstrap_create
    assert_output_not_contains ".kube/config"
    assert_output_contains ".config"
}

# Test: bootstrap_status checks for kind prerequisite
@test "bootstrap_status fails when kind command not found" {
    run bootstrap_status
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kind"
}

# Test: bootstrap_status checks for kubectl prerequisite
@test "bootstrap_status fails when kubectl command not found" {
    mock_command "kind" "" 0
    
    run bootstrap_status
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kubectl"
}

# Test: bootstrap_status fails when cluster not found
@test "bootstrap_status fails when cluster does not exist" {
    # Mock prerequisites
    mock_command "kubectl" "" 0
    
    # Mock kind to show no clusters
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    exit 0  # No output = no clusters
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run bootstrap_status
    [ "$status" -eq 5 ]  # EXIT_CLUSTER_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "not found"
}

# Test: bootstrap_status logs kind get clusters command
@test "bootstrap_status logs kind get clusters command" {
    # Mock prerequisites
    mock_command "kubectl" "" 0
    
    # Mock kind to show no clusters
    mock_command "kind" "" 0
    
    run bootstrap_status
    assert_output_contains "[CMD]"
    assert_output_contains "kind get clusters"
}

# Test: bootstrap_status fails when kubeconfig file missing
@test "bootstrap_status fails when kubeconfig file does not exist" {
    # Mock prerequisites
    mock_command "kubectl" "" 0
    
    # Mock kind to show cluster exists
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    echo "mk8-bootstrap"
    exit 0
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    # Ensure kubeconfig doesn't exist
    rm -f "${KUBECONFIG_FILE}"
    
    run bootstrap_status
    [ "$status" -eq 5 ]  # EXIT_CLUSTER_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "Kubeconfig file not found"
}

# Test: bootstrap_status uses isolated kubeconfig
@test "bootstrap_status uses isolated kubeconfig with kubectl" {
    # Mock prerequisites
    mock_command "kind" "mk8-bootstrap" 0
    
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    
    # Mock kubectl to check for --kubeconfig flag
    cat > "${TEST_TEMP_DIR}/bin/kubectl" <<'EOF'
#!/usr/bin/env bash
# Check that --kubeconfig is used and NOT ~/.kube/config
has_kubeconfig_flag=false
for arg in "$@"; do
    if [[ "$arg" == "--kubeconfig" ]]; then
        has_kubeconfig_flag=true
    fi
    if [[ "$arg" == *".kube/config"* ]]; then
        echo "ERROR: Using ~/.kube/config" >&2
        exit 1
    fi
done
if [[ "$has_kubeconfig_flag" == "false" ]]; then
    echo "ERROR: Missing --kubeconfig flag" >&2
    exit 1
fi
exit 1  # Fail for test purposes
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kubectl"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run bootstrap_status
    assert_output_contains "[CMD]"
    assert_output_contains "--kubeconfig"
    assert_output_not_contains ".kube/config"
}

# Test: bootstrap_delete checks for kind prerequisite
@test "bootstrap_delete fails when kind command not found" {
    run bootstrap_delete
    [ "$status" -eq 2 ]  # EXIT_MISSING_PREREQ
    assert_output_contains "[ERROR]"
    assert_output_contains "kind"
}

# Test: bootstrap_delete fails when cluster not found
@test "bootstrap_delete fails when cluster does not exist" {
    # Mock kind to show no clusters
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    exit 0  # No output = no clusters
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run bootstrap_delete
    [ "$status" -eq 5 ]  # EXIT_CLUSTER_ERROR
    assert_output_contains "[ERROR]"
    assert_output_contains "not found"
}

# Test: bootstrap_delete logs kind delete command
@test "bootstrap_delete logs kind delete cluster command" {
    # Mock kind to show cluster exists, then fail on delete
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    echo "mk8-bootstrap"
    exit 0
fi
if [[ "$1" == "delete" ]]; then
    exit 1  # Fail for test purposes
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run bootstrap_delete
    assert_output_contains "[CMD]"
    assert_output_contains "kind delete cluster"
    assert_output_contains "--name"
}

# Test: bootstrap_delete removes kubeconfig file
@test "bootstrap_delete removes kubeconfig file after deletion" {
    # Create kubeconfig file
    touch "${KUBECONFIG_FILE}"
    assert_file_exists "${KUBECONFIG_FILE}"
    
    # Mock kind to show cluster exists and succeed on delete
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    echo "mk8-bootstrap"
    exit 0
fi
if [[ "$1" == "delete" ]]; then
    exit 0  # Success
fi
exit 0
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run bootstrap_delete
    assert_success
    
    # Kubeconfig should be removed
    if [[ -f "${KUBECONFIG_FILE}" ]]; then
        echo "Expected kubeconfig to be removed: ${KUBECONFIG_FILE}" >&2
        return 1
    fi
}

# Test: Cluster name consistency across all operations
@test "all bootstrap operations use same cluster name" {
    # Mock prerequisites
    mock_command "kubectl" "" 0
    
    # Track cluster names used
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
# Log all cluster names to a file
for arg in "$@"; do
    if [[ "$prev_arg" == "--name" ]]; then
        echo "$arg" >> /tmp/cluster_names.txt
    fi
    prev_arg="$arg"
done

if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    exit 0  # No clusters for create test
fi
exit 1  # Fail for test purposes
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    # Try create (will fail but will log cluster name)
    bootstrap_create 2>/dev/null || true
    
    # Check that cluster name is consistent (mk8-bootstrap)
    if [[ -f /tmp/cluster_names.txt ]]; then
        local cluster_name
        cluster_name=$(cat /tmp/cluster_names.txt | head -1)
        [ "$cluster_name" = "mk8-bootstrap" ]
        rm -f /tmp/cluster_names.txt
    fi
}

# Test: Error handling for command logging
@test "bootstrap functions log commands even when operations fail" {
    # Mock prerequisites
    mock_command "kubectl" "" 0
    
    # Mock kind to fail
    cat > "${TEST_TEMP_DIR}/bin/kind" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "get" ]] && [[ "$2" == "clusters" ]]; then
    exit 0  # No clusters
fi
exit 1  # Fail all other operations
EOF
    chmod +x "${TEST_TEMP_DIR}/bin/kind"
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    
    run bootstrap_create
    # Should still log the command even though it fails
    assert_output_contains "[CMD]"
    assert_output_contains "kind create cluster"
}

