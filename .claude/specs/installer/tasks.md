# Implementation Plan

## Core Data Models and Infrastructure

- [x] 1. Implement platform detection data models
  - Create `PlatformInfo` dataclass with os, distribution, version, architecture, supported fields
  - Implement `is_linux()` and `is_wsl()` helper methods
  - Write unit tests for data model methods
  - _Requirements: 2.1, 2.5_

- [x] 2. Implement prerequisite status data models
  - Create `PrerequisiteStatus` dataclass with name, installed, version, version_ok, daemon_running, path, error fields
  - Implement `is_satisfied()` method to check if prerequisite is fully met
  - Write unit tests for satisfaction logic with various scenarios
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [ ] 3. Implement prerequisite results aggregate model
  - Create `PrerequisiteResults` dataclass with docker, kind, kubectl fields
  - Implement `all_satisfied()` method to check all prerequisites
  - Implement `get_missing()` method to return list of missing tool names
  - Implement `get_status_summary()` method to generate human-readable summary
  - Write unit tests for aggregate logic and summary formatting
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

- [ ] 4. Implement installation and verification result models
  - Create `InstallationResult` dataclass with success, previous_version, new_version, prerequisites_satisfied, verification_passed, messages, errors fields
  - Implement `is_upgrade()` helper method
  - Create `VerificationResult` dataclass with command_available, command_path, imports_ok, import_errors, prerequisites_ok, prerequisite_results fields
  - Implement `is_fully_verified()` method
  - Create `UninstallResult` dataclass with success, package_removed, config_removed, verified_removed, errors fields
  - Write unit tests for all data models and helper methods
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 5. Implement custom error classes for installer
  - Create `InstallationError` exception class extending `MK8Error`
  - Create `VerificationError` exception class extending `MK8Error`
  - Create `UninstallError` exception class extending `MK8Error`
  - Write unit tests for error formatting with suggestions
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

## Platform Detection

- [ ] 6. Implement OS detection
  - Create `PlatformDetector` class in `mk8/integrations/platform.py`
  - Implement `get_os()` method to detect linux, darwin, windows, wsl
  - Write unit tests mocking `platform.system()` for each OS type
  - _Requirements: 2.1, 2.5_

- [ ] 7. Implement WSL detection
  - Implement `is_wsl()` method by checking `/proc/version` for "microsoft" or "wsl"
  - Handle file not found and permission errors gracefully
  - Write unit tests mocking file reads for WSL and non-WSL environments
  - _Requirements: 2.5_

- [ ] 8. Implement Linux distribution detection
  - Implement `get_linux_distribution()` method using `/etc/os-release`
  - Parse NAME or ID field to identify ubuntu, debian, fedora, centos, arch, etc.
  - Return None for non-Linux platforms
  - Write unit tests mocking file reads for various distributions
  - _Requirements: 2.2_

- [ ] 9. Implement platform support check
  - Implement `is_platform_supported()` method checking against supported platforms list
  - Define supported platforms: Linux (all major distros), macOS, WSL2
  - Write unit tests for supported and unsupported platforms
  - _Requirements: 2.4_

- [ ] 10. Implement complete platform detection
  - Implement `detect()` method that orchestrates all detection methods
  - Populate full `PlatformInfo` including architecture from `platform.machine()`
  - Write integration tests for the full detection flow
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

## Prerequisite Checking

- [ ] 11. Implement tool executable checking
  - Create `PrerequisiteChecker` class in `mk8/integrations/prerequisites.py`
  - Implement helper method to check if tool exists in PATH using `shutil.which()`
  - Write unit tests mocking `shutil.which()` for found and not found scenarios
  - _Requirements: 1.1, 1.3, 1.4_

- [ ] 12. Implement version parsing utility
  - Implement `parse_version()` helper method to extract semantic version from string
  - Handle various formats: "v1.28.0", "24.0.5", "Docker version 24.0.5, build xyz"
  - Return tuple of (major, minor, patch)
  - Write unit tests for various version string formats and edge cases
  - _Requirements: 1.5, 1.7_

- [ ] 13. Implement version comparison
  - Implement `check_tool_version()` method that runs tool's version command
  - Parse output using version parser
  - Compare against minimum required version
  - Return tuple of (meets_requirement, current_version)
  - Write unit tests mocking subprocess calls with various version outputs
  - _Requirements: 1.5, 1.7_

- [ ] 14. Implement Docker daemon check
  - Implement `is_docker_daemon_running()` method using `docker info` command
  - Check exit code to determine if daemon is accessible
  - Handle timeout scenarios (daemon not responding)
  - Write unit tests mocking subprocess for running and not running daemon
  - _Requirements: 1.2_

- [ ] 15. Implement Docker prerequisite check
  - Implement `check_docker()` method that checks installation, version, and daemon
  - Return `PrerequisiteStatus` with all relevant fields populated
  - Include suggestions in error field when checks fail
  - Write unit tests for: installed with daemon running, installed without daemon, not installed, old version
  - _Requirements: 1.1, 1.2, 1.5, 1.7_

- [ ] 16. Implement kind prerequisite check
  - Implement `check_kind()` method that checks installation and version
  - Return `PrerequisiteStatus` with relevant fields
  - Write unit tests for: installed with good version, installed with old version, not installed
  - _Requirements: 1.4, 1.5, 1.7_

- [ ] 17. Implement kubectl prerequisite check
  - Implement `check_kubectl()` method that checks installation and version
  - Return `PrerequisiteStatus` with relevant fields
  - Write unit tests for various installation states
  - _Requirements: 1.3, 1.5, 1.7_

- [ ] 18. Implement aggregate prerequisite checking
  - Implement `check_all()` method that runs all prerequisite checks
  - Return `PrerequisiteResults` with all check results
  - Write unit tests for: all satisfied, some missing, all missing, version issues
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

## Installation Instructions

- [ ] 19. Implement Docker installation instructions generator
  - Create `InstructionProvider` class in `mk8/business/installation_instructions.py`
  - Implement `get_docker_instructions()` method with platform-specific instructions
  - Support Ubuntu/Debian (apt), Fedora/RHEL (dnf/yum), macOS (brew), WSL
  - Format as copy-paste ready commands with clickable URLs where appropriate
  - Write unit tests for each platform type
  - _Requirements: 3.1, 3.2, 3.4, 3.6, 3.7_

- [ ] 20. Implement kind installation instructions generator
  - Implement `get_kind_instructions()` method with platform-specific instructions
  - Support direct binary download for Linux, brew for macOS, go install as alternative
  - Include verification step in instructions
  - Write unit tests for each platform
  - _Requirements: 3.1, 3.3, 3.4, 3.6, 3.7_

- [ ] 21. Implement kubectl installation instructions generator
  - Implement `get_kubectl_instructions()` method with platform-specific instructions
  - Support package managers and direct downloads
  - Include PATH setup instructions if needed
  - Write unit tests for each platform
  - _Requirements: 3.1, 3.3, 3.4, 3.6, 3.7_

- [ ] 22. Implement bulk instruction formatting
  - Implement `get_instructions_for_missing()` method that generates instructions for multiple tools
  - Implement `format_instructions()` method that formats dict of instructions for display
  - Create clear sections for each tool with headers and command blocks
  - Write unit tests for single tool, multiple tools, and formatting
  - _Requirements: 3.5, 3.6, 3.7_

## Verification

- [ ] 23. Implement mk8 command verification
  - Create `VerificationManager` class in `mk8/business/verification.py`
  - Implement `verify_mk8_command()` method using `shutil.which("mk8")`
  - Test command execution with `mk8 --version`
  - Write unit tests for: command found and working, command not in PATH, command fails to execute
  - _Requirements: 4.2, 4.3, 5.2, 5.6_

- [ ] 24. Implement Python imports verification
  - Implement `verify_imports()` method that attempts to import all mk8 modules
  - Try importing: mk8.cli, mk8.core, mk8.business, mk8.integrations
  - Return list of import errors (empty if all successful)
  - Write unit tests mocking import failures
  - _Requirements: 5.3_

- [ ] 25. Implement PATH verification
  - Implement helper method to check if mk8 is in PATH and provide instructions if not
  - Detect shell type (bash, zsh, fish) from SHELL environment variable
  - Generate appropriate PATH addition instructions for detected shell
  - Write unit tests for various shell types
  - _Requirements: 4.4_

- [ ] 26. Implement complete verification flow
  - Implement `verify()` method that runs all verification checks
  - Re-check prerequisites using `PrerequisiteChecker`
  - Return complete `VerificationResult` with all check results
  - Write integration tests for full verification flow
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

## Installation Management

- [ ] 27. Implement existing installation detection
  - Create `InstallationManager` class in `mk8/business/installer.py`
  - Implement `detect_existing_installation()` method checking for mk8 in PATH
  - Run `mk8 --version` to get current version if installed
  - Return version string or None
  - Write unit tests for: not installed, installed, installed but broken
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 28. Implement virtual environment detection
  - Implement helper method `is_virtual_env()` checking sys.real_prefix and sys.base_prefix
  - Implement helper method `get_venv_info()` returning venv path and type
  - Write unit tests mocking sys attributes for venv, virtualenv, and no venv
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 29. Implement prerequisite handling for interactive mode
  - Implement `handle_missing_prerequisites()` method for interactive mode
  - Display instructions using `InstructionProvider`
  - Prompt user to install manually (automatic installation not in MVP)
  - Wait for user confirmation that prerequisites are installed
  - Re-check prerequisites after user confirms
  - Write unit tests mocking user input
  - _Requirements: 6.1, 6.2, 6.5, 6.6_

- [ ] 30. Implement prerequisite handling for non-interactive mode
  - Extend `handle_missing_prerequisites()` to handle non-interactive mode
  - Raise `PrerequisiteError` with installation instructions in suggestions
  - Write unit tests for non-interactive mode with missing prerequisites
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 31. Implement Python package installation
  - Implement `install_package()` method using subprocess to run pip
  - Detect if in virtual environment and adjust pip command accordingly
  - Handle common installation errors: permission denied, network issues, disk space
  - Provide specific error messages with suggestions for each error type
  - Write unit tests mocking subprocess for success and various failure modes
  - _Requirements: 4.1, 4.5, 4.6, 10.3_

- [ ] 32. Implement installation orchestration
  - Implement `install()` method that orchestrates the full installation flow
  - Detect existing installation and determine if upgrade/downgrade/reinstall
  - Check prerequisites and handle missing ones based on interactive flag
  - Install package
  - Verify installation
  - Return `InstallationResult` with complete information
  - Write integration tests for: fresh install, upgrade, prerequisites missing
  - _Requirements: 4.1, 5.1, 5.5, 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3_

- [ ] 33. Implement installation logging
  - Add detailed logging throughout installation process
  - Log all subprocess commands and their outputs
  - Log all file operations
  - Add timestamps to all log entries
  - Mask sensitive information in logs
  - Save logs to temporary file and inform user of location on error
  - Write unit tests verifying log entries for key operations
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

## Uninstallation

- [ ] 34. Implement package removal
  - Create `UninstallManager` class in `mk8/business/uninstaller.py`
  - Implement `remove_package()` method using pip uninstall
  - Handle errors gracefully and provide manual removal instructions
  - Write unit tests mocking subprocess for success and failure cases
  - _Requirements: 11.1, 11.6_

- [ ] 35. Implement configuration removal
  - Implement `remove_configuration()` method to delete ~/.config/mk8
  - Prompt user for confirmation if in interactive mode
  - Skip prompt if --yes flag or non-interactive mode
  - Handle directory not existing gracefully
  - Write unit tests for: directory exists, directory doesn't exist, permission denied
  - _Requirements: 11.2, 11.3_

- [ ] 36. Implement uninstall verification
  - Implement `verify_removal()` method to confirm mk8 is no longer in PATH
  - Check that `shutil.which("mk8")` returns None
  - Return True if fully removed, False otherwise
  - Write unit tests for verified and not verified scenarios
  - _Requirements: 11.5_

- [ ] 37. Implement complete uninstallation flow
  - Implement `uninstall()` method orchestrating package and config removal
  - Handle interactive vs non-interactive modes
  - Verify removal after uninstall
  - Return `UninstallResult` with complete status
  - Provide manual removal instructions if uninstall fails
  - Write integration tests for: complete removal, partial removal, failures
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

## CLI Integration

- [ ] 38. Implement verify command
  - Create verify command handler in `mk8/cli/commands/verify.py`
  - Add verify command to main CLI group in `mk8/cli/main.py`
  - Accept --verbose flag for detailed output
  - Instantiate `VerificationManager` and run verification
  - Display results using `OutputFormatter`
  - Exit with appropriate exit code based on results
  - Write unit tests using CliRunner
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 39. Implement uninstall command
  - Create uninstall command handler in `mk8/cli/commands/uninstall.py`
  - Add uninstall command to main CLI group
  - Accept --remove-config flag to remove configuration
  - Accept --yes/-y flag to skip confirmations
  - Instantiate `UninstallManager` and run uninstallation
  - Display results and any errors
  - Write unit tests using CliRunner for interactive and non-interactive modes
  - _Requirements: 11.1, 11.2, 11.3, 11.5, 11.6_

## Integration Testing

- [ ] 40. Implement end-to-end verification test
  - Create integration test that runs full verification flow
  - Mock all external dependencies (subprocess, file system)
  - Test scenario: all prerequisites satisfied, mk8 installed
  - Verify correct `VerificationResult` is returned
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 41. Implement end-to-end installation test with prerequisites met
  - Create integration test for fresh installation scenario
  - Mock all prerequisites as satisfied
  - Mock pip install as successful
  - Mock verification as successful
  - Verify correct `InstallationResult` is returned
  - _Requirements: 4.1, 5.1, 5.5_

- [ ] 42. Implement end-to-end installation test with missing prerequisites
  - Create integration test for installation with missing Docker
  - Test interactive mode: display instructions and re-check
  - Test non-interactive mode: raise error with suggestions
  - Verify appropriate error handling
  - _Requirements: 6.1, 6.5, 6.6, 7.1, 7.3_

- [ ] 43. Implement end-to-end uninstallation test
  - Create integration test for full uninstallation
  - Test with and without config removal
  - Test interactive and non-interactive modes
  - Verify correct `UninstallResult` is returned
  - _Requirements: 11.1, 11.2, 11.3, 11.5_

- [ ] 44. Implement platform-specific instruction test
  - Create integration test verifying correct instructions for each platform
  - Test Ubuntu, Debian, Fedora, macOS, WSL platforms
  - Verify instructions contain appropriate package manager commands
  - Verify all missing tools get instructions
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5_
