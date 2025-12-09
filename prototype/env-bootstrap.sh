#!/usr/bin/env bash
# Environment utility script for mk8-prototype
# Sets KUBECONFIG and sources MK8_* AWS credentials
#
# USAGE:
#   source ./env-bootstrap.sh
#   # or
#   . ./env-bootstrap.sh
#
# This script must be SOURCED (not executed) to set environment variables in the current shell

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script must be sourced, not executed directly"
    echo "Usage: source ./env-bootstrap.sh"
    echo "   or: . ./env-bootstrap.sh"
    exit 1
fi

# Get script directory
_ENV_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes for output
_COLOR_RESET='\033[0m'
_COLOR_BLUE='\033[0;34m'
_COLOR_YELLOW='\033[0;33m'

# Log function for this utility
_env_log_info() {
    echo -e "${_COLOR_BLUE}[INFO]${_COLOR_RESET} $1"
}

_env_log_warning() {
    echo -e "${_COLOR_YELLOW}[WARN]${_COLOR_RESET} $1"
}

# ==============================================================================
# KUBECONFIG Setup
# ==============================================================================

# Set KUBECONFIG to point to isolated bootstrap cluster config
_KUBECONFIG_PATH="${_ENV_SCRIPT_DIR}/.config/mk8-bootstrap"

if [[ -f "$_KUBECONFIG_PATH" ]]; then
    export KUBECONFIG="$_KUBECONFIG_PATH"
    _env_log_info "KUBECONFIG set to: ${KUBECONFIG}"
else
    _env_log_warning "KUBECONFIG file not found: ${_KUBECONFIG_PATH}"
    _env_log_warning "You may need to create the bootstrap cluster first:"
    _env_log_warning "  ./mk8-prototype.sh bootstrap create"
    # Still export the path so it's ready when cluster is created
    export KUBECONFIG="$_KUBECONFIG_PATH"
fi

# ==============================================================================
# AWS Credentials Setup
# ==============================================================================

# Configuration file lookup priority:
# 1. ~/.config/env-mk8-aws (user's home directory - for real credentials)
# 2. .config/env-mk8-aws-template (local template - for dummy values)

_AWS_ENV_HOME="${HOME}/.config/env-mk8-aws"
_AWS_ENV_TEMPLATE="${_ENV_SCRIPT_DIR}/.config/env-mk8-aws-template"
_AWS_ENV_FILE=""

# Determine which credentials file to use
if [[ -f "$_AWS_ENV_HOME" ]]; then
    _AWS_ENV_FILE="$_AWS_ENV_HOME"
    _env_log_info "Loading AWS credentials from: ${_AWS_ENV_FILE}"
elif [[ -f "$_AWS_ENV_TEMPLATE" ]]; then
    _AWS_ENV_FILE="$_AWS_ENV_TEMPLATE"
    _env_log_info "Loading AWS credentials from template: ${_AWS_ENV_FILE}"
    _env_log_warning "Using TEMPLATE credentials (dummy values)"
    _env_log_warning "For real credentials, copy template to home directory:"
    _env_log_warning "  cp .config/env-mk8-aws-template ~/.config/env-mk8-aws"
    _env_log_warning "  chmod 600 ~/.config/env-mk8-aws"
    _env_log_warning "  # Edit ~/.config/env-mk8-aws with your real AWS credentials"
else
    _env_log_warning "No AWS credentials file found!"
    _env_log_warning "Checked:"
    _env_log_warning "  1. ${_AWS_ENV_HOME}"
    _env_log_warning "  2. ${_AWS_ENV_TEMPLATE}"
    _env_log_warning "MK8_AWS_* environment variables will NOT be set"
fi

# Source the credentials file if found
if [[ -n "$_AWS_ENV_FILE" ]] && [[ -f "$_AWS_ENV_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$_AWS_ENV_FILE"
    _env_log_info "MK8_AWS_* environment variables configured"

    # Display what was loaded (masked for security)
    if [[ -n "${MK8_AWS_ACCESS_KEY_ID:-}" ]]; then
        echo "  MK8_AWS_ACCESS_KEY_ID: ${MK8_AWS_ACCESS_KEY_ID:0:16}***"
    fi
    if [[ -n "${MK8_AWS_REGION:-}" ]]; then
        echo "  MK8_AWS_REGION: ${MK8_AWS_REGION}"
    fi
fi

# ==============================================================================
# Completion Message
# ==============================================================================

echo ""
_env_log_info "Environment configured for mk8-prototype"

if [[ -f "$_KUBECONFIG_PATH" ]]; then
    _env_log_info "kubectl now points to mk8-bootstrap cluster"
    echo "  Try: kubectl get nodes"
else
    _env_log_info "After creating bootstrap cluster, kubectl will work automatically"
fi

if [[ -n "${MK8_AWS_ACCESS_KEY_ID:-}" ]]; then
    _env_log_info "AWS credentials loaded (MK8_* variables)"
    echo "  Try: ./mk8-prototype.sh config"
fi

echo ""

# Clean up temporary variables
unset _ENV_SCRIPT_DIR
unset _KUBECONFIG_PATH
unset _AWS_ENV_HOME
unset _AWS_ENV_TEMPLATE
unset _AWS_ENV_FILE
unset _COLOR_RESET
unset _COLOR_BLUE
unset _COLOR_YELLOW
unset -f _env_log_info
unset -f _env_log_warning
