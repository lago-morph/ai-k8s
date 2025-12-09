#!/usr/bin/env bash
#
# Bootstrap cluster management module
# Handles kind cluster lifecycle with isolated kubeconfig

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/common.sh"

# Configuration
readonly CLUSTER_NAME="${MK8_CLUSTER_NAME:-mk8-bootstrap}"
readonly CONFIG_DIR="${SCRIPT_DIR}/../.config"
readonly KUBECONFIG_FILE="${CONFIG_DIR}/${CLUSTER_NAME}"

#######################################
# Get the path to the isolated kubeconfig file
# Globals:
#   KUBECONFIG_FILE
# Returns:
#   Path to kubeconfig file
#######################################
get_kubeconfig_path() {
    echo "${KUBECONFIG_FILE}"
}

#######################################
# Create bootstrap cluster with isolated kubeconfig
# Globals:
#   CLUSTER_NAME
#   KUBECONFIG_FILE
#   CONFIG_DIR
# Outputs:
#   Writes status messages to stdout
# Returns:
#   0 on success, 5 on error
#######################################
bootstrap_create() {
    log_info "Creating bootstrap cluster: ${CLUSTER_NAME}"
    
    # Check prerequisites
    check_prereq "kind"
    check_prereq "kubectl"
    
    # Create config directory if it doesn't exist
    if [[ ! -d "${CONFIG_DIR}" ]]; then
        mkdir -p "${CONFIG_DIR}"
    fi
    
    # Check if cluster already exists
    if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        log_error "Cluster '${CLUSTER_NAME}' already exists" \
            "Delete it first with: mk8-prototype.sh bootstrap delete"
        return 5
    fi
    
    # Create cluster with isolated kubeconfig
    log_command "kind create cluster --name ${CLUSTER_NAME} --kubeconfig ${KUBECONFIG_FILE}"
    if kind create cluster --name "${CLUSTER_NAME}" --kubeconfig "${KUBECONFIG_FILE}"; then
        log_success "Cluster '${CLUSTER_NAME}' created successfully"
        log_info "Kubeconfig stored at: ${KUBECONFIG_FILE}"
        log_info "To use kubectl with this cluster, run: source ./env-bootstrap.sh"
        return 0
    else
        log_error "Failed to create cluster '${CLUSTER_NAME}'"
        return 5
    fi
}

#######################################
# Show bootstrap cluster status
# Globals:
#   CLUSTER_NAME
#   KUBECONFIG_FILE
# Outputs:
#   Writes status information to stdout
# Returns:
#   0 on success, 5 on error
#######################################
bootstrap_status() {
    log_info "Checking status of cluster: ${CLUSTER_NAME}"
    
    # Check prerequisites
    check_prereq "kind"
    check_prereq "kubectl"
    
    # Check if cluster exists
    log_command "kind get clusters"
    if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        log_error "Cluster '${CLUSTER_NAME}' not found" \
            "Create it first with: mk8-prototype.sh bootstrap create"
        return 5
    fi
    
    log_success "Cluster '${CLUSTER_NAME}' exists"
    
    # Check if kubeconfig file exists
    if [[ ! -f "${KUBECONFIG_FILE}" ]]; then
        log_error "Kubeconfig file not found: ${KUBECONFIG_FILE}" \
            "The cluster exists but kubeconfig is missing"
        return 5
    fi
    
    log_info "Kubeconfig: ${KUBECONFIG_FILE}"
    
    # Get cluster info using isolated kubeconfig
    log_command "kubectl --kubeconfig ${KUBECONFIG_FILE} cluster-info"
    if kubectl --kubeconfig "${KUBECONFIG_FILE}" cluster-info 2>/dev/null; then
        log_success "Cluster is running and accessible"
        
        # Show node status
        log_info "Node status:"
        kubectl --kubeconfig "${KUBECONFIG_FILE}" get nodes
        
        return 0
    else
        log_error "Failed to connect to cluster '${CLUSTER_NAME}'"
        return 5
    fi
}

#######################################
# Delete bootstrap cluster
# Globals:
#   CLUSTER_NAME
#   KUBECONFIG_FILE
# Outputs:
#   Writes status messages to stdout
# Returns:
#   0 on success, 5 on error
#######################################
bootstrap_delete() {
    log_info "Deleting bootstrap cluster: ${CLUSTER_NAME}"
    
    # Check prerequisites
    check_prereq "kind"
    
    # Check if cluster exists
    if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        log_error "Cluster '${CLUSTER_NAME}' not found" \
            "Nothing to delete"
        return 5
    fi
    
    # Delete cluster
    log_command "kind delete cluster --name ${CLUSTER_NAME}"
    if kind delete cluster --name "${CLUSTER_NAME}"; then
        log_success "Cluster '${CLUSTER_NAME}' deleted successfully"
        
        # Remove kubeconfig file if it exists
        if [[ -f "${KUBECONFIG_FILE}" ]]; then
            log_info "Removing kubeconfig file: ${KUBECONFIG_FILE}"
            rm -f "${KUBECONFIG_FILE}"
        fi
        
        return 0
    else
        log_error "Failed to delete cluster '${CLUSTER_NAME}'"
        return 5
    fi
}
