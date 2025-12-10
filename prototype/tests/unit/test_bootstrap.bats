#!/usr/bin/env bats
# Unit tests for lib/bootstrap.sh
# Tests bootstrap cluster management functions

load ../test_helper

# Bootstrap module path
BOOTSTRAP_MODULE=""

setup() {
    setup_test_env
    BOOTSTRAP_MODULE="${PROTOTYPE_ROOT}/lib/bootstrap.sh"
    
    # Source the bootstrap module for testing
    source "$BOOTSTRAP_MODULE"
}

teardown() {
    teardown_test_env
}

# Test: get_kubeconfig_path returns correct path
@test "get_kubeconfig_path returns correct isolated kubeconfig path" {
    run get_kubeconfig_path
    assert_success
    assert_output_contains ".config/mk8-bootstrap"
    # Should be an absolute path
    [[ "$output" == /* ]]
}

# Test: Cluster name consistency
@test "bootstrap functions use consistent cluster name" {
    # Mock kind command to capture cluster name
    kind() {
        echo "kind called with: $*" >&2
        case "$1" in
            "get")
                echo "mk8-bootstrap"
                ;;
            "create"|"delete")
                # Extract cluster name from arguments
                local prev_arg=""
                for arg in "$@"; do
                    if [[ "$prev_arg" == "--name" ]]; then
                        echo "cluster-name: $arg" >&2
                        break
                    fi
                    prev_arg="$arg"
                done
                ;;
        esac
        return 0
    }
    export -f kind
    
    # Test that all functions use the same cluster name
    run bootstrap_delete
    assert_success
    assert_output_contains "cluster-name: mk8-bootstrap"
}

# Test: Kubeconfig isolation - never modifies ~/.kube/config
@test "bootstrap functions never modify ~/.kube/config" {
    # Create a mock ~/.kube/config to ensure it's never touched
    mkdir -p "${HOME}/.kube"
    echo "original-config" > "${HOME}/.kube/config"
    original_content=$(cat "${HOME}/.kube/config")
    
    # Create the kubeconfig file that bootstrap_status expects
    kubeconfig_path=$(get_kubeconfig_path)
    mkdir -p "$(dirname "$kubeconfig_path")"
    touch "$kubeconfig_path"
    
    # Mock kubectl to capture kubeconfig usage
    kubectl() {
        echo "kubectl called with: $*" >&2
        # Check that --kubeconfig is used and not ~/.kube/config
        local prev_arg=""
        for arg in "$@"; do
            if [[ "$prev_arg" == "--kubeconfig" ]]; then
                echo "kubeconfig-used: $arg" >&2
                [[ "$arg" != "${HOME}/.kube/config" ]]
                return 0
            fi
            prev_arg="$arg"
        done
        return 0
    }
    export -f kubectl
    
    # Mock kind to avoid actual cluster operations
    kind() {
        case "$1" in
            "get")
                echo "mk8-bootstrap"
                ;;
            *)
                return 0
                ;;
        esac
    }
    export -f kind
    
    # Test bootstrap_status which uses kubectl
    run bootstrap_status
    assert_success
    assert_output_contains "kubeconfig-used:"
    assert_output_contains ".config/mk8-bootstrap"
    
    # Verify ~/.kube/config was never modified
    current_content=$(cat "${HOME}/.kube/config")
    [[ "$current_content" == "$original_content" ]]
}

# Test: Command logging - all external commands are logged
@test "bootstrap functions log all external commands before execution" {
    # Mock kind to return that cluster exists so delete command runs
    kind() {
        case "$1" in
            "get")
                if [[ "$2" == "clusters" ]]; then
                    echo "mk8-bootstrap"
                    return 0
                fi
                ;;
            "delete")
                echo "kind executed: $*" >&2
                return 0
                ;;
        esac
        return 0
    }
    export -f kind
    
    # Test bootstrap_delete (should log kind command)
    run bootstrap_delete
    assert_success
    assert_output_contains "[CMD]"
    assert_output_contains "kind delete cluster"
}

# Test: Error handling - cluster already exists
@test "bootstrap_create handles cluster already exists error" {
    # Mock kind get clusters to return existing cluster
    kind() {
        case "$1" in
            "get")
                if [[ "$2" == "clusters" ]]; then
                    echo "mk8-bootstrap"
                    return 0
                fi
                ;;
        esac
        return 0
    }
    export -f kind
    
    run bootstrap_create
    assert_failure
    assert_output_contains "already exists"
    assert_output_contains "Use 'bootstrap delete' first"
}

# Test: Error handling - cluster not found for status
@test "bootstrap_status handles cluster not found error" {
    # Mock kind get clusters to return no clusters
    kind() {
        case "$1" in
            "get")
                if [[ "$2" == "clusters" ]]; then
                    return 0  # No output means no clusters
                fi
                ;;
        esac
        return 0
    }
    export -f kind
    
    run bootstrap_status
    assert_failure
    assert_output_contains "not found"
    assert_output_contains "Use 'bootstrap create' first"
}

# Test: Error handling - missing kubeconfig file
@test "bootstrap_status handles missing kubeconfig file" {
    # Mock kind to return cluster exists
    kind() {
        case "$1" in
            "get")
                if [[ "$2" == "clusters" ]]; then
                    echo "mk8-bootstrap"
                    return 0
                fi
                ;;
        esac
        return 0
    }
    export -f kind
    
    # Ensure kubeconfig file doesn't exist
    kubeconfig_path=$(get_kubeconfig_path)
    rm -f "$kubeconfig_path"
    
    run bootstrap_status
    assert_failure
    assert_output_contains "Kubeconfig file not found"
}

# Test: bootstrap_delete handles non-existent cluster gracefully
@test "bootstrap_delete handles non-existent cluster gracefully" {
    # Mock kind get clusters to return no clusters
    kind() {
        case "$1" in
            "get")
                if [[ "$2" == "clusters" ]]; then
                    return 0  # No output means no clusters
                fi
                ;;
        esac
        return 0
    }
    export -f kind
    
    run bootstrap_delete
    assert_success
    assert_output_contains "not found"
    assert_output_contains "already deleted or never created"
}

# Test: Prerequisite checking
@test "bootstrap functions check for required prerequisites" {
    # Mock check_prereq to capture prerequisite checks
    check_prereq() {
        echo "checking prerequisite: $1" >&2
        case "$1" in
            "kind"|"kubectl")
                return 0
                ;;
            *)
                return 1
                ;;
        esac
    }
    export -f check_prereq
    
    # Mock kind to return no existing clusters so create can proceed
    kind() {
        case "$1" in
            "get")
                if [[ "$2" == "clusters" ]]; then
                    return 0  # No output means no clusters
                fi
                ;;
            "create")
                return 0
                ;;
        esac
        return 0
    }
    export -f kind
    
    run bootstrap_create
    assert_output_contains "checking prerequisite: kind"
    assert_output_contains "checking prerequisite: kubectl"
}

# Test: Config directory creation
@test "bootstrap module creates config directory if it doesn't exist" {
    # Remove config directory
    rm -rf "${PROTOTYPE_ROOT}/.config"
    
    # Source the module again to trigger directory creation
    source "$BOOTSTRAP_MODULE"
    
    # Verify directory was created
    [[ -d "${PROTOTYPE_ROOT}/.config" ]]
}

# Test: Environment variable usage
@test "bootstrap functions respect MK8_CLUSTER_NAME environment variable" {
    # Set custom cluster name and re-source the module
    export MK8_CLUSTER_NAME="custom-cluster-name"
    source "$BOOTSTRAP_MODULE"
    
    # Mock kind to capture cluster name and return that cluster exists
    kind() {
        echo "kind called with: $*" >&2
        case "$1" in
            "get")
                if [[ "$2" == "clusters" ]]; then
                    echo "custom-cluster-name"
                    return 0
                fi
                ;;
            "delete")
                # Extract cluster name from arguments
                local prev_arg=""
                for arg in "$@"; do
                    if [[ "$prev_arg" == "--name" ]]; then
                        echo "cluster-name: $arg" >&2
                        break
                    fi
                    prev_arg="$arg"
                done
                return 0
                ;;
        esac
        return 0
    }
    export -f kind
    
    run bootstrap_delete
    assert_success
    assert_output_contains "cluster-name: custom-cluster-name"
    
    unset MK8_CLUSTER_NAME
}

# Test: Script can be executed directly
@test "bootstrap.sh can be executed directly with subcommands" {
    # Mock external commands
    kind() { return 0; }
    kubectl() { return 0; }
    export -f kind kubectl
    
    run "$BOOTSTRAP_MODULE" delete
    assert_success
    assert_output_contains "Deleting bootstrap cluster"
}

# Test: Script shows usage when executed with invalid arguments
@test "bootstrap.sh shows usage for invalid subcommands" {
    run "$BOOTSTRAP_MODULE" invalid-command
    assert_failure
    [[ "$status" -eq 3 ]]  # EXIT_INVALID_ARGS
    assert_output_contains "Usage:"
    assert_output_contains "create|status|delete"
}