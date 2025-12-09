#!/usr/bin/env bash
# AWS credentials configuration module for mk8-prototype
# Provides validation and isolation of AWS credentials using MK8_* environment variables

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Source common utilities
source "${SCRIPT_DIR}/lib/common.sh"

# Required MK8_* environment variables
readonly REQUIRED_MK8_VARS=(
    "MK8_AWS_ACCESS_KEY_ID"
    "MK8_AWS_SECRET_ACCESS_KEY"
)

# Default AWS region if not specified
readonly DEFAULT_AWS_REGION="us-east-1"

# Execute command with MK8_* variables temporarily mapped to AWS_* variables
# This ensures isolation - standard AWS_* variables are only set within a subshell
# Usage: with_mk8_aws_env "aws sts get-caller-identity"
with_mk8_aws_env() {
    local cmd="$*"

    # Execute in subshell to isolate environment variables
    (
        # Temporarily map MK8_* to AWS_* for this command only
        export AWS_ACCESS_KEY_ID="${MK8_AWS_ACCESS_KEY_ID}"
        export AWS_SECRET_ACCESS_KEY="${MK8_AWS_SECRET_ACCESS_KEY}"
        export AWS_REGION="${MK8_AWS_REGION:-$DEFAULT_AWS_REGION}"

        # Execute the command
        eval "$cmd"
    )
    # Standard AWS_* variables automatically unset when subshell exits
}

# Check if all required MK8_* environment variables are set
# Returns 0 if all variables are set, 1 otherwise
check_mk8_env_vars() {
    local missing_vars=()

    for var in "${REQUIRED_MK8_VARS[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        local error_msg="Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            error_msg="${error_msg}\n  - ${var}"
        done
        error_msg="${error_msg}\n\nPlease set these variables or source env-bootstrap.sh:"
        error_msg="${error_msg}\n  source ./env-bootstrap.sh"
        log_error "$error_msg" "$EXIT_AWS_ERROR"
    fi

    return 0
}

# Validate AWS credentials by calling AWS STS get-caller-identity
# Displays account information on success, exits with error on failure
validate_aws_credentials() {
    log_info "Validating AWS credentials..."
    log_separator

    # Check prerequisite
    check_prereq "aws" "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"

    # Check required environment variables
    check_mk8_env_vars

    # Display which variables are being used
    log_info "Using MK8_* environment variables:"
    echo "  MK8_AWS_ACCESS_KEY_ID: ${MK8_AWS_ACCESS_KEY_ID:0:16}***"
    echo "  MK8_AWS_REGION: ${MK8_AWS_REGION:-$DEFAULT_AWS_REGION}"
    echo ""

    # Validate credentials using AWS STS
    log_info "Calling AWS STS to validate credentials..."
    log_command "aws sts get-caller-identity"

    local caller_identity
    if ! caller_identity=$(with_mk8_aws_env "aws sts get-caller-identity" 2>&1); then
        log_error "AWS credential validation failed\nError: ${caller_identity}" "$EXIT_AWS_ERROR"
    fi

    # Extract and display account information
    log_separator
    log_success "AWS credentials are valid!"
    echo ""
    echo "Account Information:"

    # Parse JSON output to display key information
    local account_id
    local user_arn
    account_id=$(echo "$caller_identity" | grep -o '"Account": "[^"]*"' | cut -d'"' -f4 || echo "N/A")
    user_arn=$(echo "$caller_identity" | grep -o '"Arn": "[^"]*"' | cut -d'"' -f4 || echo "N/A")

    echo "  Account ID: ${account_id}"
    echo "  User/Role:  ${user_arn}"
    echo ""

    log_info "Credential validation complete"
    log_separator
}

# Main function when script is run directly
main() {
    validate_aws_credentials
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
