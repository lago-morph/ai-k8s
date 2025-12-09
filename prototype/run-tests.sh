#!/usr/bin/env bash
# Test runner script for mk8-prototype
# Runs both unit tests (BATS) and static analysis (shellcheck)

set -euo pipefail

# Color codes for output
readonly COLOR_RESET='\033[0m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_YELLOW='\033[0;33m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Test configuration
TESTS_DIR="${SCRIPT_DIR}/tests"
UNIT_TESTS_DIR="${TESTS_DIR}/unit"
INTEGRATION_TESTS_DIR="${TESTS_DIR}/integration"

# Track test results
TESTS_PASSED=true

# Log functions
log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1" >&2
}

log_section() {
    echo ""
    echo "================================================================"
    echo -e "${COLOR_YELLOW}$1${COLOR_RESET}"
    echo "================================================================"
}

# Run shellcheck on all bash scripts
run_shellcheck() {
    log_section "Running ShellCheck Static Analysis"

    local files_to_check=()

    # Find all .sh files
    while IFS= read -r -d '' file; do
        files_to_check+=("$file")
    done < <(find "$SCRIPT_DIR" -type f -name "*.sh" -not -path "*/tests/*" -print0)

    # Find all files in lib/ (no extension)
    while IFS= read -r -d '' file; do
        files_to_check+=("$file")
    done < <(find "$SCRIPT_DIR/lib" -type f -print0 2>/dev/null || true)

    if [[ ${#files_to_check[@]} -eq 0 ]]; then
        log_info "No shell scripts found to check"
        return 0
    fi

    log_info "Checking ${#files_to_check[@]} shell script(s)..."

    local shellcheck_failed=false
    for file in "${files_to_check[@]}"; do
        echo "  Checking: $file"
        if ! shellcheck "$file"; then
            shellcheck_failed=true
        fi
    done

    if [[ "$shellcheck_failed" == "true" ]]; then
        log_error "ShellCheck found issues"
        TESTS_PASSED=false
        return 1
    else
        log_success "ShellCheck passed - no issues found"
        return 0
    fi
}

# Run BATS unit tests
run_unit_tests() {
    log_section "Running Unit Tests (BATS)"

    if [[ ! -d "$UNIT_TESTS_DIR" ]]; then
        log_info "No unit tests directory found: $UNIT_TESTS_DIR"
        return 0
    fi

    local test_files=()
    while IFS= read -r -d '' file; do
        test_files+=("$file")
    done < <(find "$UNIT_TESTS_DIR" -type f -name "*.bats" -print0)

    if [[ ${#test_files[@]} -eq 0 ]]; then
        log_info "No unit test files found"
        return 0
    fi

    log_info "Running ${#test_files[@]} unit test file(s)..."

    if bats "${test_files[@]}"; then
        log_success "All unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        TESTS_PASSED=false
        return 1
    fi
}

# Run BATS integration tests
run_integration_tests() {
    log_section "Running Integration Tests (BATS)"

    if [[ ! -d "$INTEGRATION_TESTS_DIR" ]]; then
        log_info "No integration tests directory found: $INTEGRATION_TESTS_DIR"
        return 0
    fi

    local test_files=()
    while IFS= read -r -d '' file; do
        test_files+=("$file")
    done < <(find "$INTEGRATION_TESTS_DIR" -type f -name "*.bats" -print0)

    if [[ ${#test_files[@]} -eq 0 ]]; then
        log_info "No integration test files found"
        return 0
    fi

    log_info "Running ${#test_files[@]} integration test file(s)..."

    if bats "${test_files[@]}"; then
        log_success "All integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        TESTS_PASSED=false
        return 1
    fi
}

# Main execution
main() {
    local run_type="${1:-all}"

    log_info "mk8-prototype Test Runner"
    log_info "Working directory: $SCRIPT_DIR"

    case "$run_type" in
        shellcheck)
            run_shellcheck
            ;;
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        all)
            run_shellcheck || true
            run_unit_tests || true
            run_integration_tests || true
            ;;
        *)
            echo "Usage: $0 [all|shellcheck|unit|integration]"
            echo ""
            echo "  all          Run all tests (default)"
            echo "  shellcheck   Run only shellcheck static analysis"
            echo "  unit         Run only unit tests"
            echo "  integration  Run only integration tests"
            exit 1
            ;;
    esac

    # Final summary
    echo ""
    log_section "Test Summary"

    if [[ "$TESTS_PASSED" == "true" ]]; then
        log_success "All tests passed!"
        exit 0
    else
        log_error "Some tests failed"
        exit 1
    fi
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
