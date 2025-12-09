#!/usr/bin/env bash
# Common utilities for mk8-prototype
# Provides logging functions, prerequisite checking, and error handling

set -euo pipefail

# Prevent re-sourcing this file
if [[ -n "${_COMMON_SH_LOADED:-}" ]]; then
    return 0
fi
readonly _COMMON_SH_LOADED=1

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_GENERAL_ERROR=1
readonly EXIT_MISSING_PREREQ=2
readonly EXIT_INVALID_ARGS=3
readonly EXIT_AWS_ERROR=4
readonly EXIT_CLUSTER_ERROR=5
readonly EXIT_CROSSPLANE_ERROR=6

# Color codes for output
readonly COLOR_RESET='\033[0m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_YELLOW='\033[0;33m'

# Log informational message (blue)
log_info() {
    local message="$1"
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} ${message}"
}

# Log success message (green)
log_success() {
    local message="$1"
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} ${message}"
}

# Log error message and exit (red)
log_error() {
    local message="$1"
    local exit_code="${2:-$EXIT_GENERAL_ERROR}"
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} ${message}" >&2
    exit "$exit_code"
}

# Log command before execution (yellow)
log_command() {
    local command="$1"
    echo -e "${COLOR_YELLOW}[CMD]${COLOR_RESET} ${command}"
}

# Check if required command exists in PATH
# Usage: check_prereq "command_name" ["installation_url"]
check_prereq() {
    local cmd="$1"
    local install_url="${2:-}"

    if ! command -v "$cmd" &> /dev/null; then
        local error_msg="Required command '$cmd' not found in PATH"
        if [[ -n "$install_url" ]]; then
            error_msg="${error_msg}\nPlease install $cmd: $install_url"
        fi
        log_error "$error_msg" "$EXIT_MISSING_PREREQ"
    fi
}

# Check if a variable is set and non-empty
# Usage: check_var "VAR_NAME" "error_message"
check_var() {
    local var_name="$1"
    local error_msg="${2:-Variable $var_name is not set}"
    local var_value="${!var_name:-}"

    if [[ -z "$var_value" ]]; then
        log_error "$error_msg" "$EXIT_GENERAL_ERROR"
    fi
}

# Display a separator line for visual clarity
log_separator() {
    echo "================================================================"
}
