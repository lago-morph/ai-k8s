#!/usr/bin/env bash
#
# Crossplane management module
# Handles Crossplane installation, AWS Provider configuration, and S3 bucket management

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/common.sh"
# shellcheck source=lib/config.sh
source "${SCRIPT_DIR}/config.sh"
# shellcheck source=lib/bootstrap.sh
source "${SCRIPT_DIR}/bootstrap.sh"

# Configuration
readonly CROSSPLANE_NAMESPACE="crossplane-system"
readonly CROSSPLANE_RELEASE="crossplane"
readonly CROSSPLANE_CHART="crossplane-stable/crossplane"
readonly CROSSPLANE_VERSION="1.14.0"
readonly AWS_PROVIDER="upbound/provider-aws-s3"
readonly PROVIDER_CONFIG_NAME="default"
readonly STATE_FILE="${HOME}/.config/mk8-prototype-state"
readonly BUCKET_PREFIX="test-s3-bucket"

#######################################
# Install Crossplane via Helm
# Globals:
#   CROSSPLANE_NAMESPACE
#   CROSSPLANE_RELEASE
#   CROSSPLANE_CHART
#   CROSSPLANE_VERSION
# Outputs:
#   Writes status messages to stdout
# Returns:
#   0 on success, 6 on error
#######################################
crossplane_install() {
    log_info "Installing Crossplane via Helm"
    
    # Check prerequisites
    check_prereq "helm"
    check_prereq "kubectl"
    
    # Get kubeconfig path
    local kubeconfig
    kubeconfig="$(get_kubeconfig_path)"
    
    if [[ ! -f "${kubeconfig}" ]]; then
        log_error "Kubeconfig not found: ${kubeconfig}" \
            "Create bootstrap cluster first with: mk8-prototype.sh bootstrap create"
        return 6
    fi
    
    # Add Helm repository
    log_info "Adding Crossplane Helm repository"
    log_command "helm repo add crossplane-stable https://charts.crossplane.io/stable"
    if ! helm repo add crossplane-stable https://charts.crossplane.io/stable 2>/dev/null; then
        log_info "Repository already exists, updating..."
    fi
    
    log_command "helm repo update"
    helm repo update
    
    # Install Crossplane
    log_info "Installing Crossplane chart (version ${CROSSPLANE_VERSION})"
    log_command "helm install ${CROSSPLANE_RELEASE} ${CROSSPLANE_CHART} \
--namespace ${CROSSPLANE_NAMESPACE} \
--create-namespace \
--version ${CROSSPLANE_VERSION} \
--kubeconfig ${kubeconfig}"
    
    if helm install "${CROSSPLANE_RELEASE}" "${CROSSPLANE_CHART}" \
        --namespace "${CROSSPLANE_NAMESPACE}" \
        --create-namespace \
        --version "${CROSSPLANE_VERSION}" \
        --kubeconfig "${kubeconfig}"; then
        log_success "Crossplane chart installed successfully"
    else
        log_error "Failed to install Crossplane chart"
        return 6
    fi
    
    # Wait for Crossplane pods to be ready
    log_info "Waiting for Crossplane pods to be ready..."
    log_command "kubectl --kubeconfig ${kubeconfig} wait --for=condition=ready pod \
--selector=app=crossplane \
--namespace ${CROSSPLANE_NAMESPACE} \
--timeout=300s"
    
    if kubectl --kubeconfig "${kubeconfig}" wait --for=condition=ready pod \
        --selector=app=crossplane \
        --namespace "${CROSSPLANE_NAMESPACE}" \
        --timeout=300s; then
        log_success "Crossplane pods are ready"
    else
        log_error "Timeout waiting for Crossplane pods to be ready"
        return 6
    fi
    
    # Display pod status
    log_info "Crossplane pod status:"
    kubectl --kubeconfig "${kubeconfig}" get pods \
        --namespace "${CROSSPLANE_NAMESPACE}"
    
    log_success "Crossplane installation complete"
    
    # If AWS credentials are configured, set up AWS Provider
    if [[ -n "${MK8_AWS_ACCESS_KEY_ID:-}" ]] && [[ -n "${MK8_AWS_SECRET_ACCESS_KEY:-}" ]]; then
        log_info "AWS credentials detected, configuring AWS Provider..."
        create_aws_provider_config
    else
        log_info "No AWS credentials configured. To configure AWS Provider, set MK8_AWS_* environment variables and run:"
        log_info "  mk8-prototype.sh crossplane install"
    fi
    
    return 0
}

#######################################
# Create AWS ProviderConfig with credentials
# Globals:
#   MK8_AWS_ACCESS_KEY_ID
#   MK8_AWS_SECRET_ACCESS_KEY
#   MK8_AWS_REGION
#   CROSSPLANE_NAMESPACE
#   AWS_PROVIDER
#   PROVIDER_CONFIG_NAME
# Outputs:
#   Writes status messages to stdout
# Returns:
#   0 on success, 6 on error
#######################################
create_aws_provider_config() {
    log_info "Creating AWS ProviderConfig"
    
    # Check prerequisites
    check_prereq "kubectl"
    
    # Get kubeconfig path
    local kubeconfig
    kubeconfig="$(get_kubeconfig_path)"
    
    # Check for required environment variables
    if [[ -z "${MK8_AWS_ACCESS_KEY_ID:-}" ]] || [[ -z "${MK8_AWS_SECRET_ACCESS_KEY:-}" ]]; then
        log_error "AWS credentials not configured" \
            "Set MK8_AWS_ACCESS_KEY_ID and MK8_AWS_SECRET_ACCESS_KEY environment variables"
        return 6
    fi
    
    local aws_region="${MK8_AWS_REGION:-us-east-1}"
    
    # Create Kubernetes secret with AWS credentials
    log_info "Creating Kubernetes secret with AWS credentials"
    log_command "kubectl --kubeconfig ${kubeconfig} create secret generic aws-creds \
--namespace ${CROSSPLANE_NAMESPACE} \
--from-literal=aws_access_key_id=\${MK8_AWS_ACCESS_KEY_ID} \
--from-literal=aws_secret_access_key=\${MK8_AWS_SECRET_ACCESS_KEY}"
    
    if kubectl --kubeconfig "${kubeconfig}" create secret generic aws-creds \
        --namespace "${CROSSPLANE_NAMESPACE}" \
        --from-literal=aws_access_key_id="${MK8_AWS_ACCESS_KEY_ID}" \
        --from-literal=aws_secret_access_key="${MK8_AWS_SECRET_ACCESS_KEY}" \
        --dry-run=client -o yaml | kubectl --kubeconfig "${kubeconfig}" apply -f -; then
        log_success "AWS credentials secret created"
    else
        log_error "Failed to create AWS credentials secret"
        return 6
    fi
    
    # Install AWS Provider
    log_info "Installing AWS S3 Provider: ${AWS_PROVIDER}"
    log_command "kubectl --kubeconfig ${kubeconfig} apply -f -"
    
    cat <<EOF | kubectl --kubeconfig "${kubeconfig}" apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws-s3
spec:
  package: ${AWS_PROVIDER}:v0.47.0
EOF
    
    if [[ $? -eq 0 ]]; then
        log_success "AWS Provider installed"
    else
        log_error "Failed to install AWS Provider"
        return 6
    fi
    
    # Wait for provider to be ready
    log_info "Waiting for AWS Provider to be ready..."
    local max_wait=120
    local waited=0
    while [[ $waited -lt $max_wait ]]; do
        if kubectl --kubeconfig "${kubeconfig}" get provider provider-aws-s3 -o jsonpath='{.status.conditions[?(@.type=="Healthy")].status}' 2>/dev/null | grep -q "True"; then
            log_success "AWS Provider is healthy"
            break
        fi
        sleep 5
        waited=$((waited + 5))
    done
    
    if [[ $waited -ge $max_wait ]]; then
        log_error "Timeout waiting for AWS Provider to be ready"
        return 6
    fi
    
    # Create ProviderConfig
    log_info "Creating ProviderConfig: ${PROVIDER_CONFIG_NAME}"
    log_command "kubectl --kubeconfig ${kubeconfig} apply -f -"
    
    cat <<EOF | kubectl --kubeconfig "${kubeconfig}" apply -f -
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: ${PROVIDER_CONFIG_NAME}
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: ${CROSSPLANE_NAMESPACE}
      name: aws-creds
      key: aws_access_key_id
  region: ${aws_region}
EOF
    
    if [[ $? -eq 0 ]]; then
        log_success "ProviderConfig created"
    else
        log_error "Failed to create ProviderConfig"
        return 6
    fi
    
    # Verify AWS Provider
    verify_aws_provider
    
    return 0
}

#######################################
# Verify AWS Provider is ready and configured
# Globals:
#   PROVIDER_CONFIG_NAME
# Outputs:
#   Writes status messages to stdout
# Returns:
#   0 on success, 6 on error
#######################################
verify_aws_provider() {
    log_info "Verifying AWS Provider configuration"
    
    # Check prerequisites
    check_prereq "kubectl"
    
    # Get kubeconfig path
    local kubeconfig
    kubeconfig="$(get_kubeconfig_path)"
    
    # Check Provider status
    log_info "Checking Provider status:"
    if kubectl --kubeconfig "${kubeconfig}" get provider provider-aws-s3 2>/dev/null; then
        log_success "AWS Provider found"
    else
        log_error "AWS Provider not found" \
            "Install it with: mk8-prototype.sh crossplane install"
        return 6
    fi
    
    # Check ProviderConfig status
    log_info "Checking ProviderConfig status:"
    if kubectl --kubeconfig "${kubeconfig}" get providerconfig "${PROVIDER_CONFIG_NAME}" 2>/dev/null; then
        log_success "ProviderConfig '${PROVIDER_CONFIG_NAME}' found"
    else
        log_error "ProviderConfig '${PROVIDER_CONFIG_NAME}' not found" \
            "Configure it with: mk8-prototype.sh crossplane install"
        return 6
    fi
    
    log_success "AWS Provider is properly configured and ready to manage AWS resources"
    return 0
}

#######################################
# Show Crossplane and AWS Provider status
# Globals:
#   CROSSPLANE_NAMESPACE
# Outputs:
#   Writes status information to stdout
# Returns:
#   0 on success, 6 on error
#######################################
crossplane_status() {
    log_info "Checking Crossplane status"
    
    # Check prerequisites
    check_prereq "kubectl"
    
    # Get kubeconfig path
    local kubeconfig
    kubeconfig="$(get_kubeconfig_path)"
    
    if [[ ! -f "${kubeconfig}" ]]; then
        log_error "Kubeconfig not found: ${kubeconfig}" \
            "Create bootstrap cluster first with: mk8-prototype.sh bootstrap create"
        return 6
    fi
    
    # Check if Crossplane namespace exists
    if ! kubectl --kubeconfig "${kubeconfig}" get namespace "${CROSSPLANE_NAMESPACE}" &>/dev/null; then
        log_error "Crossplane namespace '${CROSSPLANE_NAMESPACE}' not found" \
            "Install Crossplane first with: mk8-prototype.sh crossplane install"
        return 6
    fi
    
    # Show Crossplane pods
    log_info "Crossplane pods:"
    kubectl --kubeconfig "${kubeconfig}" get pods \
        --namespace "${CROSSPLANE_NAMESPACE}"
    
    # Show Providers if any exist
    log_info "Crossplane Providers:"
    if kubectl --kubeconfig "${kubeconfig}" get providers 2>/dev/null; then
        log_success "Providers found"
    else
        log_info "No providers installed yet"
    fi
    
    # Show ProviderConfigs if any exist
    log_info "Crossplane ProviderConfigs:"
    if kubectl --kubeconfig "${kubeconfig}" get providerconfigs 2>/dev/null; then
        log_success "ProviderConfigs found"
    else
        log_info "No provider configs created yet"
    fi
    
    return 0
}

#######################################
# Generate unique bucket name with UUID
# Globals:
#   BUCKET_PREFIX
# Outputs:
#   Writes bucket name to stdout
# Returns:
#   0 on success
#######################################
generate_bucket_name() {
    # Generate a short UUID (8 characters)
    local uuid
    uuid=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 8 | head -n 1)
    echo "${BUCKET_PREFIX}-${uuid}"
}

#######################################
# Save bucket name to state file
# Arguments:
#   $1 - Bucket name
# Globals:
#   STATE_FILE
# Returns:
#   0 on success, 6 on error
#######################################
save_bucket_state() {
    local bucket_name="$1"
    
    # Create directory if it doesn't exist
    local state_dir
    state_dir="$(dirname "${STATE_FILE}")"
    if [[ ! -d "${state_dir}" ]]; then
        mkdir -p "${state_dir}"
    fi
    
    # Save bucket name
    echo "${bucket_name}" > "${STATE_FILE}"
    log_info "Bucket name saved to state file: ${STATE_FILE}"
}

#######################################
# Load bucket name from state file
# Globals:
#   STATE_FILE
# Outputs:
#   Writes bucket name to stdout
# Returns:
#   0 on success, 6 if state file doesn't exist
#######################################
load_bucket_state() {
    if [[ ! -f "${STATE_FILE}" ]]; then
        return 6
    fi
    
    cat "${STATE_FILE}"
}

#######################################
# Clear bucket state file
# Globals:
#   STATE_FILE
# Returns:
#   0 on success
#######################################
clear_bucket_state() {
    if [[ -f "${STATE_FILE}" ]]; then
        rm -f "${STATE_FILE}"
        log_info "Bucket state file cleared: ${STATE_FILE}"
    fi
}

#######################################
# Create test S3 bucket via Crossplane MRD
# Globals:
#   STATE_FILE
# Outputs:
#   Writes status messages to stdout
# Returns:
#   0 on success, 6 on error
#######################################
crossplane_create_s3() {
    log_info "Creating S3 bucket via Crossplane"
    
    # Check if bucket already exists
    if [[ -f "${STATE_FILE}" ]]; then
        local existing_bucket
        existing_bucket="$(load_bucket_state)"
        log_error "Bucket already exists: ${existing_bucket}" \
            "Delete it first with: mk8-prototype.sh crossplane delete-s3"
        return 6
    fi
    
    # Generate bucket name
    local bucket_name
    bucket_name="$(generate_bucket_name)"
    log_info "Generated bucket name: ${bucket_name}"
    
    # TODO: Implement MRD creation and verification
    log_error "S3 bucket creation not yet fully implemented" \
        "This requires AWS Provider configuration (task 13)"
    return 6
}

#######################################
# Delete test S3 bucket
# Globals:
#   STATE_FILE
# Outputs:
#   Writes status messages to stdout
# Returns:
#   0 on success, 6 on error
#######################################
crossplane_delete_s3() {
    log_info "Deleting S3 bucket via Crossplane"
    
    # Check if bucket exists
    if [[ ! -f "${STATE_FILE}" ]]; then
        log_error "No bucket found in state file" \
            "Create a bucket first with: mk8-prototype.sh crossplane create-s3"
        return 6
    fi
    
    local bucket_name
    bucket_name="$(load_bucket_state)"
    log_info "Deleting bucket: ${bucket_name}"
    
    # TODO: Implement MRD deletion and verification
    log_error "S3 bucket deletion not yet fully implemented" \
            "This requires AWS Provider configuration (task 13)"
    return 6
}
