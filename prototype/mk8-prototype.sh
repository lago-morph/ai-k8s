#!/usr/bin/env bash
# mk8-prototype - Minimal bash-based reference implementation of mk8
# Main entry point with CLI parsing and command routing

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source libraries
source "${SCRIPT_DIR}/lib/common.sh"
source "${SCRIPT_DIR}/lib/config.sh"
source "${SCRIPT_DIR}/lib/bootstrap.sh"
source "${SCRIPT_DIR}/lib/crossplane.sh"

# Version information
readonly VERSION="0.1.0-prototype"

# Display version information
cmd_version() {
    echo "mk8-prototype version ${VERSION}"
    echo "A minimal, transparent bash-based implementation of mk8's core functionality"
}

# Display help information
cmd_help() {
    cat << EOF
mk8-prototype - Minimal bash-based reference implementation of mk8

USAGE:
    ./mk8-prototype.sh <command> [subcommand] [options]

COMMANDS:
    version                    Display version information
    help                       Display this help information

    config                     Validate AWS credentials from environment
                              Requires: MK8_AWS_ACCESS_KEY_ID, MK8_AWS_SECRET_ACCESS_KEY

    bootstrap create           Create local kind cluster with isolated kubeconfig
    bootstrap status           Show bootstrap cluster status
    bootstrap delete           Delete bootstrap cluster

    crossplane install         Install Crossplane via Helm and configure AWS Provider
    crossplane status          Show Crossplane and AWS Provider status
    crossplane create-s3       Create test S3 bucket via Crossplane MRD
    crossplane delete-s3       Delete test S3 bucket

ENVIRONMENT VARIABLES:
    MK8_AWS_ACCESS_KEY_ID       AWS access key (required for AWS operations)
    MK8_AWS_SECRET_ACCESS_KEY   AWS secret access key (required for AWS operations)
    MK8_AWS_REGION              AWS region (default: us-east-1)
    MK8_CLUSTER_NAME            Cluster name (default: mk8-bootstrap)

EXAMPLES:
    # Set up environment (sets KUBECONFIG and sources MK8_* variables)
    source ./env-bootstrap.sh

    # Validate AWS credentials
    ./mk8-prototype.sh config

    # Create bootstrap cluster
    ./mk8-prototype.sh bootstrap create

    # Install Crossplane with AWS Provider
    ./mk8-prototype.sh crossplane install

    # Create S3 bucket via Crossplane
    ./mk8-prototype.sh crossplane create-s3

For more information, see README.md
EOF
}

# Config command - validate AWS credentials (implemented in lib/config.sh)
cmd_config() {
    validate_aws_credentials
}

# Bootstrap commands (implemented in lib/bootstrap.sh)
cmd_bootstrap() {
    local subcommand="${1:-}"

    case "$subcommand" in
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
            log_error "Unknown bootstrap subcommand: '$subcommand'\nValid subcommands: create, status, delete" "$EXIT_INVALID_ARGS"
            ;;
    esac
}

# Crossplane commands (implemented in lib/crossplane.sh)
cmd_crossplane() {
    local subcommand="${1:-}"

    case "$subcommand" in
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
            log_error "Unknown crossplane subcommand: '$subcommand'\nValid subcommands: install, status, create-s3, delete-s3" "$EXIT_INVALID_ARGS"
            ;;
    esac
}

# Main command routing
main() {
    local command="${1:-}"

    # Handle no arguments
    if [[ -z "$command" ]]; then
        echo "Error: No command specified"
        echo ""
        cmd_help
        exit "$EXIT_INVALID_ARGS"
    fi

    # Shift to get subcommand arguments
    shift || true

    # Route to command handler
    case "$command" in
        version|--version|-v)
            cmd_version
            ;;
        help|--help|-h)
            cmd_help
            ;;
        config)
            cmd_config "$@"
            ;;
        bootstrap)
            cmd_bootstrap "$@"
            ;;
        crossplane)
            cmd_crossplane "$@"
            ;;
        *)
            log_error "Unknown command: '$command'\nRun './mk8-prototype.sh help' for usage information" "$EXIT_INVALID_ARGS"
            ;;
    esac
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
