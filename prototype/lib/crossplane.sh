#!/usr/bin/env bash
# Crossplane installation and management module
# Provides functions for installing Crossplane, configuring AWS Provider, and managing S3 buckets

set -euo pipefail

# Note: common.sh, config.sh, and bootstrap.sh are sourced by the main script

# Configuration
CROSSPLANE_NAMESPACE="crossplane-system"
CROSSPLANE_RELEASE="crossplane"
CROSSPLANE_CHART="crossplane-stable/crossplane"
CROSSPLANE_VERSION="2.1.3"
AWS_PROVIDER="ghcr.io/crossplane-contrib/provider-aws:v0.55.0"
PROVIDER_CONFIG_NAME="default"
STATE_FILE="${HOME}/.config/mk8-prototype-state"
BUCKET_PREFIX="test-s3-bucket"

# Install Crossplane via Helm
crossplane_install() {
    log_info "Installing Crossplane via Helm..."
    
    # Check prerequisites
    check_prereq "helm" "https://helm.sh/docs/intro/install/"
    check_prereq "kubectl" "https://kubernetes.io/docs/tasks/tools/"
    
    # Get kubeconfig path for isolated cluster access
    local kubeconfig_path
    kubeconfig_path=$(get_kubeconfig_path)
    
    # Check if kubeconfig exists
    if [[ ! -f "$kubeconfig_path" ]]; then
        log_error "Bootstrap cluster kubeconfig not found at: ${kubeconfig_path}\nRun 'bootstrap create' first."
    fi
    
    # Add Crossplane Helm repository
    log_command "helm repo add crossplane-stable https://charts.crossplane.io/stable"
    if ! helm repo add crossplane-stable https://charts.crossplane.io/stable; then
        log_error "Failed to add Crossplane Helm repository"
    fi
    
    # Update Helm repositories
    log_command "helm repo update"
    if ! helm repo update; then
        log_error "Failed to update Helm repositories"
    fi
    
    # Install Crossplane chart
    log_command "helm install ${CROSSPLANE_RELEASE} ${CROSSPLANE_CHART} --namespace ${CROSSPLANE_NAMESPACE} --create-namespace --version ${CROSSPLANE_VERSION} --kubeconfig ${kubeconfig_path}"
    if ! helm install "$CROSSPLANE_RELEASE" "$CROSSPLANE_CHART" \
        --namespace "$CROSSPLANE_NAMESPACE" \
        --create-namespace \
        --version "$CROSSPLANE_VERSION" \
        --kubeconfig "$kubeconfig_path"; then
        log_error "Failed to install Crossplane"
    fi
    
    log_success "Crossplane Helm chart installed successfully"
    
    # Wait for Crossplane pods to be ready
    log_info "Waiting for Crossplane pods to be ready..."
    log_command "kubectl --kubeconfig ${kubeconfig_path} wait --for=condition=ready pod -l app=crossplane -n ${CROSSPLANE_NAMESPACE} --timeout=300s"
    if ! kubectl --kubeconfig "$kubeconfig_path" wait \
        --for=condition=ready pod \
        -l app=crossplane \
        -n "$CROSSPLANE_NAMESPACE" \
        --timeout=300s; then
        log_error "Crossplane pods failed to become ready within timeout"
    fi
    
    # Display Crossplane pod status
    log_info "Crossplane pod status:"
    log_command "kubectl --kubeconfig ${kubeconfig_path} get pods -n ${CROSSPLANE_NAMESPACE}"
    kubectl --kubeconfig "$kubeconfig_path" get pods -n "$CROSSPLANE_NAMESPACE"
    
    log_success "Crossplane installation completed successfully"
    
    # If AWS credentials are configured, set up AWS Provider
    if check_mk8_env_vars 2>/dev/null; then
        log_info "AWS credentials detected, configuring AWS Provider..."
        create_aws_provider_config
        verify_aws_provider
    else
        log_info "No AWS credentials configured. Run 'config' command to set up AWS Provider."
    fi
}

# Create AWS Provider configuration with credentials from MK8_* env vars
create_aws_provider_config() {
    log_info "Creating AWS Provider configuration..."
    
    # Check that MK8_* environment variables are set
    check_mk8_env_vars
    
    # Get kubeconfig path
    local kubeconfig_path
    kubeconfig_path=$(get_kubeconfig_path)
    
    # Create Kubernetes secret with AWS credentials
    log_info "Creating AWS credentials secret..."
    log_command "kubectl --kubeconfig ${kubeconfig_path} create secret generic aws-secret -n ${CROSSPLANE_NAMESPACE} --from-literal=credentials='[default]\naws_access_key_id = ${MK8_AWS_ACCESS_KEY_ID}\naws_secret_access_key = ${MK8_AWS_SECRET_ACCESS_KEY}'"
    
    # Use with_mk8_aws_env to temporarily set AWS_* variables for kubectl
    with_mk8_aws_env "kubectl --kubeconfig '$kubeconfig_path' create secret generic aws-secret -n '$CROSSPLANE_NAMESPACE' --from-literal=credentials='[default]
aws_access_key_id = $MK8_AWS_ACCESS_KEY_ID
aws_secret_access_key = $MK8_AWS_SECRET_ACCESS_KEY'"
    
    # Install AWS Provider
    log_info "Installing AWS Provider..."
    local provider_manifest="/tmp/aws-provider.yaml"
    cat > "$provider_manifest" <<EOF
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws
spec:
  package: ${AWS_PROVIDER}
EOF
    
    log_command "kubectl --kubeconfig ${kubeconfig_path} apply -f ${provider_manifest}"
    kubectl --kubeconfig "$kubeconfig_path" apply -f "$provider_manifest"
    
    # Wait for Provider to be installed
    log_info "Waiting for AWS Provider to be installed..."
    log_command "kubectl --kubeconfig ${kubeconfig_path} wait --for=condition=Installed provider.pkg.crossplane.io/provider-aws --timeout=300s"
    kubectl --kubeconfig "$kubeconfig_path" wait \
        --for=condition=Installed \
        provider.pkg.crossplane.io/provider-aws \
        --timeout=300s
    
    # Create ProviderConfig
    log_info "Creating ProviderConfig..."
    local providerconfig_manifest="/tmp/aws-providerconfig.yaml"
    cat > "$providerconfig_manifest" <<EOF
apiVersion: aws.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: ${PROVIDER_CONFIG_NAME}
  namespace: ${CROSSPLANE_NAMESPACE}
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: ${CROSSPLANE_NAMESPACE}
      name: aws-secret
      key: credentials
EOF
    
    log_command "kubectl --kubeconfig ${kubeconfig_path} apply -f ${providerconfig_manifest}"
    kubectl --kubeconfig "$kubeconfig_path" apply -f "$providerconfig_manifest"
    
    # Clean up temporary files
    rm -f "$provider_manifest" "$providerconfig_manifest"
    
    log_success "AWS Provider configuration completed"
}

# Verify AWS Provider is ready and configured
verify_aws_provider() {
    log_info "Verifying AWS Provider configuration..."
    
    # Get kubeconfig path
    local kubeconfig_path
    kubeconfig_path=$(get_kubeconfig_path)
    
    # Wait for Provider to be healthy
    log_info "Waiting for AWS Provider to be healthy..."
    log_command "kubectl --kubeconfig ${kubeconfig_path} wait --for=condition=Healthy provider.pkg.crossplane.io/provider-aws --timeout=300s"
    if ! kubectl --kubeconfig "$kubeconfig_path" wait \
        --for=condition=Healthy \
        provider.pkg.crossplane.io/provider-aws \
        --timeout=300s; then
        log_error "AWS Provider failed to become healthy within timeout"
    fi
    
    # Check ProviderConfig status
    log_info "Checking ProviderConfig status..."
    log_command "kubectl --kubeconfig ${kubeconfig_path} get providerconfig ${PROVIDER_CONFIG_NAME} -o wide"
    kubectl --kubeconfig "$kubeconfig_path" get providerconfig "$PROVIDER_CONFIG_NAME" -o wide
    
    log_success "AWS Provider is ready to manage AWS resources"
}

# Generate unique bucket name with UUID
generate_bucket_name() {
    # Generate a UUID-like string using /proc/sys/kernel/random/uuid if available
    if [[ -r /proc/sys/kernel/random/uuid ]]; then
        local uuid
        uuid=$(cat /proc/sys/kernel/random/uuid)
        echo "${BUCKET_PREFIX}-${uuid}"
    else
        # Fallback: use timestamp and random number
        local timestamp
        timestamp=$(date +%s)
        local random
        random=$((RANDOM * RANDOM))
        echo "${BUCKET_PREFIX}-${timestamp}-${random}"
    fi
}

# Save bucket name to state file
save_bucket_state() {
    local bucket_name="$1"
    
    # Ensure state directory exists
    mkdir -p "$(dirname "$STATE_FILE")"
    
    # Save bucket name to state file
    echo "$bucket_name" > "$STATE_FILE"
    
    log_info "Bucket state saved to: ${STATE_FILE}"
}

# Load bucket name from state file
load_bucket_state() {
    if [[ -f "$STATE_FILE" ]]; then
        cat "$STATE_FILE"
    else
        return 1
    fi
}

# Clear bucket state file
clear_bucket_state() {
    if [[ -f "$STATE_FILE" ]]; then
        rm -f "$STATE_FILE"
        log_info "Bucket state cleared"
    fi
}

# Create S3 bucket via Crossplane MRD
crossplane_create_s3() {
    log_info "Creating S3 bucket via Crossplane..."
    
    # Check prerequisites
    check_prereq "kubectl" "https://kubernetes.io/docs/tasks/tools/"
    
    # Get kubeconfig path
    local kubeconfig_path
    kubeconfig_path=$(get_kubeconfig_path)
    
    # Check if kubeconfig exists
    if [[ ! -f "$kubeconfig_path" ]]; then
        log_error "Bootstrap cluster kubeconfig not found at: ${kubeconfig_path}\nRun 'bootstrap create' first."
    fi
    
    # Check if bucket already exists
    if load_bucket_state >/dev/null 2>&1; then
        local existing_bucket
        existing_bucket=$(load_bucket_state)
        log_error "S3 bucket already exists: ${existing_bucket}\nRun 'crossplane delete-s3' first to delete it."
    fi
    
    # Generate unique bucket name
    local bucket_name
    bucket_name=$(generate_bucket_name)
    log_info "Generated bucket name: ${bucket_name}"
    
    # Create S3 Bucket MRD manifest
    local bucket_manifest="/tmp/s3-bucket.yaml"
    cat > "$bucket_manifest" <<EOF
apiVersion: s3.aws.crossplane.io/v1beta1
kind: Bucket
metadata:
  namespace: default
  name: ${bucket_name}
spec:
  forProvider:
    locationConstraint: ${MK8_AWS_REGION:-us-east-1}
  providerConfigRef:
    name: ${PROVIDER_CONFIG_NAME}
EOF
    
    # Apply MRD to cluster
    log_command "kubectl --kubeconfig ${kubeconfig_path} apply -f ${bucket_manifest}"
    if ! kubectl --kubeconfig "$kubeconfig_path" apply -f "$bucket_manifest"; then
        rm -f "$bucket_manifest"
        log_error "Failed to apply S3 Bucket MRD"
    fi
    
    # Wait for MRD to be ready
    log_info "Waiting for S3 bucket to be ready..."
    log_command "kubectl --kubeconfig ${kubeconfig_path} wait --for=condition=Ready bucket.s3.aws.crossplane.io/${bucket_name} --timeout=300s"
    if ! kubectl --kubeconfig "$kubeconfig_path" wait \
        --for=condition=Ready \
        "bucket.s3.aws.crossplane.io/${bucket_name}" \
        --timeout=300s; then
        rm -f "$bucket_manifest"
        log_error "S3 bucket failed to become ready within timeout"
    fi
    
    # Display MRD status
    log_info "S3 Bucket MRD status:"
    log_command "kubectl --kubeconfig ${kubeconfig_path} get bucket.s3.aws.crossplane.io/${bucket_name} -o wide"
    kubectl --kubeconfig "$kubeconfig_path" get "bucket.s3.aws.crossplane.io/${bucket_name}" -o wide
    
    # Verify bucket creation with AWS CLI
    log_info "Verifying bucket creation with AWS CLI..."
    log_command "aws s3 ls s3://${bucket_name}"
    if with_mk8_aws_env "aws s3 ls s3://${bucket_name}"; then
        log_success "S3 bucket verified via AWS CLI"
    else
        log_info "Note: AWS CLI verification failed, but MRD is ready. This may be due to eventual consistency."
    fi
    
    # Save bucket state
    save_bucket_state "$bucket_name"
    
    # Clean up temporary files
    rm -f "$bucket_manifest"
    
    log_success "S3 bucket '${bucket_name}' created successfully via Crossplane"
}

# Delete S3 bucket via Crossplane MRD
crossplane_delete_s3() {
    log_info "Deleting S3 bucket via Crossplane..."
    
    # Check prerequisites
    check_prereq "kubectl" "https://kubernetes.io/docs/tasks/tools/"
    
    # Get kubeconfig path
    local kubeconfig_path
    kubeconfig_path=$(get_kubeconfig_path)
    
    # Check if kubeconfig exists
    if [[ ! -f "$kubeconfig_path" ]]; then
        log_error "Bootstrap cluster kubeconfig not found at: ${kubeconfig_path}\nRun 'bootstrap create' first."
    fi
    
    # Load bucket name from state file
    local bucket_name
    if ! bucket_name=$(load_bucket_state); then
        log_error "No S3 bucket found in state file.\nRun 'crossplane create-s3' first to create a bucket."
    fi
    
    log_info "Deleting S3 bucket: ${bucket_name}"
    
    # Delete S3 Bucket MRD
    log_command "kubectl --kubeconfig ${kubeconfig_path} delete bucket.s3.aws.crossplane.io/${bucket_name}"
    if ! kubectl --kubeconfig "$kubeconfig_path" delete "bucket.s3.aws.crossplane.io/${bucket_name}"; then
        log_error "Failed to delete S3 Bucket MRD"
    fi
    
    # Wait for MRD to be deleted (with timeout)
    log_info "Waiting for S3 bucket to be deleted..."
    local timeout=300
    local elapsed=0
    local interval=5
    
    while kubectl --kubeconfig "$kubeconfig_path" get "bucket.s3.aws.crossplane.io/${bucket_name}" >/dev/null 2>&1; do
        if [[ $elapsed -ge $timeout ]]; then
            log_info "Timeout waiting for bucket deletion, but continuing..."
            break
        fi
        
        log_info "Waiting for bucket deletion... (${elapsed}s/${timeout}s)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    # Verify bucket deletion with AWS CLI
    log_info "Verifying bucket deletion with AWS CLI..."
    log_command "aws s3 ls s3://${bucket_name}"
    if with_mk8_aws_env "aws s3 ls s3://${bucket_name}" >/dev/null 2>&1; then
        log_info "Note: Bucket still exists in AWS (may take time for deletion to propagate)"
    else
        log_success "S3 bucket deletion verified via AWS CLI"
    fi
    
    # Clear bucket state
    clear_bucket_state
    
    log_success "S3 bucket '${bucket_name}' deletion initiated via Crossplane"
}

# Display Crossplane and AWS Provider status
crossplane_status() {
    log_info "Checking Crossplane status..."
    
    # Get kubeconfig path
    local kubeconfig_path
    kubeconfig_path=$(get_kubeconfig_path)
    
    # Check if kubeconfig exists
    if [[ ! -f "$kubeconfig_path" ]]; then
        log_error "Bootstrap cluster kubeconfig not found at: ${kubeconfig_path}\nRun 'bootstrap create' first."
    fi
    
    # Display Crossplane pod status
    log_info "Crossplane pods:"
    log_command "kubectl --kubeconfig ${kubeconfig_path} get pods -n ${CROSSPLANE_NAMESPACE}"
    if ! kubectl --kubeconfig "$kubeconfig_path" get pods -n "$CROSSPLANE_NAMESPACE" 2>/dev/null; then
        log_info "Crossplane not installed. Run 'crossplane install' first."
        return 0
    fi
    
    echo
    
    # Display Provider status
    log_info "Crossplane Providers:"
    log_command "kubectl --kubeconfig ${kubeconfig_path} get providers"
    kubectl --kubeconfig "$kubeconfig_path" get providers 2>/dev/null || log_info "No Providers installed"
    
    echo
    
    # Display ProviderConfig status
    log_info "ProviderConfigs:"
    log_command "kubectl --kubeconfig ${kubeconfig_path} get providerconfigs"
    kubectl --kubeconfig "$kubeconfig_path" get providerconfigs 2>/dev/null || log_info "No ProviderConfigs found"
}

# Main function for direct script execution
main() {
    case "${1:-}" in
        install)
            crossplane_install
            ;;
        status)
            crossplane_status
            ;;
        create-s3)
            crossplane_create_s3
            ;;
        delete-s3)
            crossplane_delete_s3
            ;;
        *)
            echo "Usage: $0 {install|status|create-s3|delete-s3}"
            echo ""
            echo "Commands:"
            echo "  install     Install Crossplane via Helm and configure AWS Provider"
            echo "  status      Show Crossplane and AWS Provider status"
            echo "  create-s3   Create test S3 bucket via Crossplane MRD"
            echo "  delete-s3   Delete test S3 bucket"
            exit 3
            ;;
    esac
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
