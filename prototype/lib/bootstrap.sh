#!/usr/bin/env bash
# Bootstrap cluster management module
# Provides functions for creating, managing, and deleting kind clusters with isolated kubeconfig

set -euo pipefail

# Source common utilities (relative to this file's directory)
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${LIB_DIR}/common.sh"

# Configuration
CLUSTER_NAME="${MK8_CLUSTER_NAME:-mk8-bootstrap}"
CONFIG_DIR="${LIB_DIR}/../.config"
KUBECONFIG_FILE="${CONFIG_DIR}/mk8-bootstrap"

# Ensure config directory exists
mkdir -p "$CONFIG_DIR"

# Get the path to the isolated kubeconfig file
get_kubeconfig_path() {
    echo "$KUBECONFIG_FILE"
}

# Create bootstrap cluster with isolated kubeconfig
bootstrap_create() {
    log_info "Creating bootstrap cluster with isolated kubeconfig..."
    
    # Check prerequisites
    check_prereq "kind" "https://kind.sigs.k8s.io/docs/user/quick-start/"
    check_prereq "kubectl" "https://kubernetes.io/docs/tasks/tools/"
    
    # Check if cluster already exists
    if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        log_error "Cluster '${CLUSTER_NAME}' already exists. Use 'bootstrap delete' first."
    fi
    
    # Create cluster with isolated kubeconfig
    log_command "kind create cluster --name ${CLUSTER_NAME} --kubeconfig ${KUBECONFIG_FILE}"
    if kind create cluster --name "$CLUSTER_NAME" --kubeconfig "$KUBECONFIG_FILE"; then
        log_success "Bootstrap cluster '${CLUSTER_NAME}' created successfully"
        log_info "Kubeconfig stored at: ${KUBECONFIG_FILE}"
        log_info "To use kubectl with this cluster, run: source ./env-bootstrap.sh"
    else
        log_error "Failed to create bootstrap cluster"
    fi
}

# Show bootstrap cluster status
bootstrap_status() {
    log_info "Checking bootstrap cluster status..."
    
    # Check prerequisites
    check_prereq "kind" "https://kind.sigs.k8s.io/docs/user/quick-start/"
    check_prereq "kubectl" "https://kubernetes.io/docs/tasks/tools/"
    
    # Check if cluster exists
    if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        log_error "Bootstrap cluster '${CLUSTER_NAME}' not found. Use 'bootstrap create' first."
    fi
    
    # Check if kubeconfig file exists
    if [[ ! -f "$KUBECONFIG_FILE" ]]; then
        log_error "Kubeconfig file not found at: ${KUBECONFIG_FILE}"
    fi
    
    # Display cluster information using isolated kubeconfig
    log_command "kubectl --kubeconfig ${KUBECONFIG_FILE} cluster-info"
    kubectl --kubeconfig "$KUBECONFIG_FILE" cluster-info
    
    echo
    log_command "kubectl --kubeconfig ${KUBECONFIG_FILE} get nodes"
    kubectl --kubeconfig "$KUBECONFIG_FILE" get nodes
    
    echo
    log_info "Cluster '${CLUSTER_NAME}' is running"
    log_info "Kubeconfig: ${KUBECONFIG_FILE}"
}

# Delete bootstrap cluster
bootstrap_delete() {
    log_info "Deleting bootstrap cluster..."
    
    # Check prerequisites
    check_prereq "kind" "https://kind.sigs.k8s.io/docs/user/quick-start/"
    
    # Check if cluster exists
    if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        log_info "Cluster '${CLUSTER_NAME}' not found (already deleted or never created)"
        return 0
    fi
    
    # Delete cluster
    log_command "kind delete cluster --name ${CLUSTER_NAME}"
    if kind delete cluster --name "$CLUSTER_NAME"; then
        log_success "Bootstrap cluster '${CLUSTER_NAME}' deleted successfully"
        
        # Clean up kubeconfig file
        if [[ -f "$KUBECONFIG_FILE" ]]; then
            log_info "Removing kubeconfig file: ${KUBECONFIG_FILE}"
            rm -f "$KUBECONFIG_FILE"
        fi
    else
        log_error "Failed to delete bootstrap cluster"
    fi
}

# Main function for direct script execution
main() {
    case "${1:-}" in
        create)
            bootstrap_create
            ;;
        status)
            bootstrap_status
            ;;
        delete)
            bootstrap_delete
            ;;
        *)
            echo "Usage: $0 {create|status|delete}"
            echo ""
            echo "Commands:"
            echo "  create    Create bootstrap cluster with isolated kubeconfig"
            echo "  status    Show bootstrap cluster status"
            echo "  delete    Delete bootstrap cluster"
            exit 3
            ;;
    esac
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
