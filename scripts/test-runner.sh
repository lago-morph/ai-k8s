#!/usr/bin/env bash
# Universal test runner that works on Linux and Windows (via WSL)
# This script detects the platform and runs tests appropriately
#
# Usage:
#   ./scripts/test-runner.sh [test-file]
#   ./scripts/test-runner.sh --shellcheck
#   ./scripts/test-runner.sh --setup-wsl

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${PROJECT_ROOT}/.test-config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Load configuration
load_config() {
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        echo -e "${RED}ERROR: Configuration file not found: ${CONFIG_FILE}${NC}"
        exit 1
    fi
    
    # Parse JSON (requires jq, but we'll provide fallback)
    if command -v jq &> /dev/null; then
        WSL_INSTANCE=$(jq -r '.wsl.instanceName' "${CONFIG_FILE}")
        WSL_DISTRO=$(jq -r '.wsl.distribution' "${CONFIG_FILE}")
        SETUP_SCRIPT=$(jq -r '.wsl.setupScript' "${CONFIG_FILE}")
        TEST_FRAMEWORK=$(jq -r '.testing.framework' "${CONFIG_FILE}")
        TEST_DIR=$(jq -r '.testing.testDirectory' "${CONFIG_FILE}")
    else
        # Fallback: hardcoded defaults
        WSL_INSTANCE="mk8-test"
        WSL_DISTRO="Ubuntu-24.04"
        SETUP_SCRIPT="prototype/setup-wsl-test-env.sh"
        TEST_FRAMEWORK="bats"
        TEST_DIR="prototype/tests/unit"
    fi
}

# Detect platform
detect_platform() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        PLATFORM="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        PLATFORM="windows"
    elif grep -qi microsoft /proc/version 2>/dev/null; then
        # Running inside WSL
        PLATFORM="wsl"
    else
        PLATFORM="unknown"
    fi
}

# Check if we're in the correct WSL instance
check_wsl_instance() {
    if [[ "${PLATFORM}" == "wsl" ]]; then
        # Check if we're in the correct instance
        local current_instance
        current_instance=$(cat /proc/sys/kernel/hostname 2>/dev/null || echo "unknown")
        
        # WSL instance name is typically the hostname
        if [[ "${current_instance}" != "${WSL_INSTANCE}" ]]; then
            echo -e "${YELLOW}WARNING: Running in WSL instance '${current_instance}', expected '${WSL_INSTANCE}'${NC}"
            echo -e "${YELLOW}This may not be the isolated testing environment${NC}"
        fi
    fi
}

# Run tests natively (Linux/macOS or inside correct WSL)
run_tests_native() {
    local test_file="${1:-}"
    
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}Running tests natively on ${PLATFORM}${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    
    # Check prerequisites
    if ! command -v "${TEST_FRAMEWORK}" &> /dev/null; then
        echo -e "${RED}ERROR: ${TEST_FRAMEWORK} not found${NC}"
        echo -e "${YELLOW}Install it with: sudo apt-get install ${TEST_FRAMEWORK}${NC}"
        exit 1
    fi
    
    cd "${PROJECT_ROOT}"
    
    if [[ -n "${test_file}" ]]; then
        echo -e "${BLUE}Running test file: ${test_file}${NC}"
        "${TEST_FRAMEWORK}" "${TEST_DIR}/${test_file}"
    else
        echo -e "${BLUE}Running all tests in: ${TEST_DIR}${NC}"
        "${TEST_FRAMEWORK}" "${TEST_DIR}/"
    fi
}

# Run shellcheck natively
run_shellcheck_native() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}Running shellcheck on ${PLATFORM}${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    
    if ! command -v shellcheck &> /dev/null; then
        echo -e "${RED}ERROR: shellcheck not found${NC}"
        echo -e "${YELLOW}Install it with: sudo apt-get install shellcheck${NC}"
        exit 1
    fi
    
    cd "${PROJECT_ROOT}"
    
    # Get shellcheck paths from config or use default
    local shellcheck_paths
    if command -v jq &> /dev/null; then
        shellcheck_paths=$(jq -r '.testing.shellcheckPaths[]' "${CONFIG_FILE}" 2>/dev/null || echo "prototype/lib/*.sh")
    else
        shellcheck_paths="prototype/lib/*.sh prototype/*.sh"
    fi
    
    echo -e "${BLUE}Checking: ${shellcheck_paths}${NC}"
    # shellcheck disable=SC2086
    shellcheck ${shellcheck_paths}
}

# Show usage
show_usage() {
    cat << EOF
Universal Test Runner

USAGE:
    ./scripts/test-runner.sh [options] [test-file]

OPTIONS:
    --shellcheck        Run shellcheck on bash scripts
    --setup-wsl         Set up WSL testing environment (Windows only)
    --help              Show this help message

ARGUMENTS:
    test-file           Optional: specific test file to run (e.g., test_crossplane.bats)

EXAMPLES:
    # Run all tests
    ./scripts/test-runner.sh

    # Run specific test
    ./scripts/test-runner.sh test_crossplane.bats

    # Run shellcheck
    ./scripts/test-runner.sh --shellcheck

    # Set up WSL (Windows only)
    ./scripts/test-runner.sh --setup-wsl

PLATFORM DETECTION:
    - Linux/macOS: Runs tests natively
    - Windows: Automatically uses WSL instance (${WSL_INSTANCE})
    - WSL: Runs natively if in correct instance

CONFIGURATION:
    Edit .test-config.json to customize WSL instance name and test paths
EOF
}

# Main execution
main() {
    load_config
    detect_platform
    
    local command="${1:-}"
    
    # Handle special commands
    case "${command}" in
        --help|-h)
            show_usage
            exit 0
            ;;
        --shellcheck)
            if [[ "${PLATFORM}" == "linux" ]] || [[ "${PLATFORM}" == "macos" ]] || [[ "${PLATFORM}" == "wsl" ]]; then
                run_shellcheck_native
            else
                echo -e "${RED}ERROR: This script must be run from WSL on Windows${NC}"
                echo -e "${YELLOW}Use: wsl -d ${WSL_INSTANCE} bash scripts/test-runner.sh --shellcheck${NC}"
                exit 1
            fi
            exit 0
            ;;
        --setup-wsl)
            echo -e "${RED}ERROR: WSL setup must be run from PowerShell${NC}"
            echo -e "${YELLOW}Use: .\\scripts\\setup-wsl.ps1${NC}"
            exit 1
            ;;
    esac
    
    # Run tests based on platform
    if [[ "${PLATFORM}" == "linux" ]] || [[ "${PLATFORM}" == "macos" ]] || [[ "${PLATFORM}" == "wsl" ]]; then
        check_wsl_instance
        run_tests_native "$@"
    else
        echo -e "${RED}ERROR: This script must be run from a Unix-like environment${NC}"
        echo -e "${YELLOW}On Windows, use: .\\scripts\\run-tests.ps1${NC}"
        exit 1
    fi
}

# Run main
main "$@"
