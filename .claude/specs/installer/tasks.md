# Implementation Plan

## Core Data Models

- [x] 1. Implement prerequisite status data model
  - Create `PrerequisiteStatus` dataclass with name, installed, daemon_running, error fields
  - Implement `is_satisfied()` method to check if prerequisite is met
  - Write unit tests for satisfaction logic
  - _Requirements: 1.1, 1.2, 1.5, 1.6_
  - **Note**: Implementation includes version and path fields from future spec

- [~] 2. Implement prerequisite results aggregate model
  - Create `PrerequisiteResults` dataclass with docker, kind, kubectl fields
  - Implement `all_satisfied()` method to check all prerequisites
  - Implement `get_missing()` method to return list of missing tool names
  - Write unit tests for aggregate logic
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - **Status**: Tests written but implementation missing in `mk8/integrations/prerequisite_models.py`

- [ ] 3. Implement verification result model
  - Create `VerificationResult` dataclass with mk8_installed, prerequisites_ok, prerequisite_results, messages fields
  - Implement `is_verified()` method
  - Write unit tests for data model
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 4. Implement verification error class
  - Create `VerificationError` exception class extending `MK8Error`
  - Write unit tests for error formatting with suggestions
  - _Requirements: 6.1, 6.2, 6.3_

## Prerequisite Checking

- [ ] 5. Implement tool executable checking
  - Create `PrerequisiteChecker` class in `mk8/integrations/prerequisites.py`
  - Implement helper method to check if tool exists in PATH using `shutil.which()`
  - Write unit tests mocking `shutil.which()` for found and not found scenarios
  - _Requirements: 1.1, 1.3, 1.4_

- [ ] 6. Implement Docker daemon check
  - Implement `is_docker_daemon_running()` method using `docker info` command
  - Check exit code to determine if daemon is accessible
  - Handle timeout scenarios
  - Write unit tests mocking subprocess for running and not running daemon
  - _Requirements: 1.2, 1.6_

- [ ] 7. Implement Docker prerequisite check
  - Implement `check_docker()` method that checks installation and daemon
  - Return `PrerequisiteStatus` with all relevant fields populated
  - Include suggestions in error field when checks fail
  - Write unit tests for: installed with daemon running, installed without daemon, not installed
  - _Requirements: 1.1, 1.2, 1.5, 1.6_

- [ ] 8. Implement kind prerequisite check
  - Implement `check_kind()` method that checks installation
  - Return `PrerequisiteStatus` with relevant fields
  - Write unit tests for: installed, not installed
  - _Requirements: 1.4, 1.5_

- [ ] 9. Implement kubectl prerequisite check
  - Implement `check_kubectl()` method that checks installation
  - Return `PrerequisiteStatus` with relevant fields
  - Write unit tests for: installed, not installed
  - _Requirements: 1.3, 1.5_

- [ ] 10. Implement aggregate prerequisite checking
  - Implement `check_all()` method that runs all prerequisite checks
  - Return `PrerequisiteResults` with all check results
  - Write unit tests for: all satisfied, some missing, all missing
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

## Installation Instructions

- [ ] 11. Implement basic installation instructions
  - Create `VerificationManager` class in `mk8/business/verification.py`
  - Implement `get_installation_instructions()` method with simple instructions
  - Provide Docker installation link
  - Provide kind installation command for Linux
  - Provide kubectl installation link
  - Write unit tests for instruction generation
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

## Verification

- [ ] 12. Implement mk8 installation check
  - Implement `verify_mk8_installed()` method using `shutil.which("mk8")`
  - Write unit tests for: command found, command not in PATH
  - _Requirements: 3.2, 3.3, 4.1_

- [ ] 13. Implement complete verification flow
  - Implement `verify()` method that runs all verification checks
  - Check if mk8 is installed
  - Check prerequisites using `PrerequisiteChecker`
  - Return complete `VerificationResult` with all check results
  - Write integration tests for full verification flow
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

## CLI Integration

- [ ] 14. Implement verify command
  - Create verify command handler in `mk8/cli/commands/verify.py`
  - Add verify command to main CLI group in `mk8/cli/main.py`
  - Accept --verbose flag for detailed output
  - Instantiate `VerificationManager` and run verification
  - Display results using `OutputFormatter`
  - Show installation instructions for missing prerequisites
  - Exit with appropriate exit code based on results
  - Write unit tests using CliRunner
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.3_

## Integration Testing

- [ ] 15. Implement end-to-end verification test
  - Create integration test that runs full verification flow
  - Mock all external dependencies (subprocess, shutil.which)
  - Test scenario: all prerequisites satisfied, mk8 installed
  - Test scenario: missing prerequisites
  - Verify correct `VerificationResult` is returned
  - _Requirements: 4.1, 4.2, 4.3, 4.4_
