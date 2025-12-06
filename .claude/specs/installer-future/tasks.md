# Implementation Plan - Future Enhancements

## Platform Detection

- [x] 1. Implement platform detection data models
  - Create `PlatformInfo` dataclass with os, distribution, version, architecture, supported fields
  - Implement `is_linux()` and `is_wsl()` helper methods
  - Write unit tests for data model methods
  - _Requirements: 2.1, 2.5_
  - **Status**: Completed in `mk8/integrations/platform_models.py` with full test coverage

- [ ] 2. Implement OS detection
  - Create `PlatformDetector` class in `mk8/integrations/platform.py`
  - Implement `get_os()` method to detect linux, darwin, windows, wsl
  - Write unit tests mocking `platform.system()` for each OS type
  - _Requirements: 2.1, 2.5_

- [ ] 3. Implement WSL detection
  - Implement `is_wsl()` method by checking `/proc/version` for "microsoft" or "wsl"
  - Handle file not found and permission errors gracefully
  - Write unit tests mocking file reads for WSL and non-WSL environments
  - _Requirements: 2.5, 2.7_

- [ ] 4. Implement Linux distribution detection
  - Implement `get_linux_distribution()` method using `/etc/os-release`
  - Parse NAME or ID field to identify ubuntu, debian, fedora, centos, arch, etc.
  - Return None for non-Linux platforms
  - Write unit tests mocking file reads for various distributions
  - _Requirements: 2.2_

- [ ] 5. Implement platform support check
  - Implement `is_platform_supported()` method checking against supported platforms list
  - Define supported platforms: Linux (all major distros), macOS, WSL2
  - Write unit tests for supported and unsupported platforms
  - _Requirements: 2.4_

- [ ] 6. Implement complete platform detection
  - Implement `detect()` method that orchestrates all detection methods
  - Populate full `PlatformInfo` including architecture from `platform.machine()`
  - Write integration tests for the full detection flow
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

## Advanced Prerequisite Checking

- [ ] 7. Implement version parsing utility
  - Implement `parse_version()` helper method to extract semantic version from string
  - Handle various formats: "v1.28.0", "24.0.5", "Docker version 24.0.5, build xyz"
  - Return tuple of (major, minor, patch)
  - Write unit tests for various version string formats and edge cases
  - _Requirements: 1.1, 1.2_

- [ ] 8. Implement version comparison
  - Extend `PrerequisiteChecker` with version checking
  - Implement `check_tool_version()` method that runs tool's version command
  - Parse output using version parser
  - Compare against minimum required version
  - Return tuple of (meets_requirement, current_version)
  - Write unit tests mocking subprocess calls with various version outputs
  - _Requirements: 1.1, 1.2_

- [x] 9. Update prerequisite status model with version info
  - Add version and version_ok fields to `PrerequisiteStatus`
  - Add path field to store tool executable path
  - Update `is_satisfied()` to check version requirements
  - Write unit tests for version checking logic
  - _Requirements: 1.1, 1.2, 1.3_
  - **Status**: Already implemented in `mk8/integrations/prerequisite_models.py` with full test coverage

## Platform-Specific Installation Instructions

- [ ] 10. Implement platform-aware instruction provider
  - Create `InstructionProvider` class in `mk8/business/installation_instructions.py`
  - Accept `PlatformInfo` in constructor
  - Implement `get_instructions_for_missing()` method that generates instructions for multiple tools
  - Implement `format_instructions()` method that formats dict of instructions for display
  - Write unit tests for instruction provider initialization
  - _Requirements: 3.5, 3.6_

- [ ] 11. Implement Docker installation instructions generator
  - Implement `get_docker_instructions()` method with platform-specific instructions
  - Support Ubuntu/Debian (apt), Fedora/RHEL (dnf/yum), macOS (brew), WSL
  - Format as copy-paste ready commands with clickable URLs where appropriate
  - Write unit tests for each platform type
  - _Requirements: 3.1, 3.2, 3.5, 3.6_

- [ ] 12. Implement kind installation instructions generator
  - Implement `get_kind_instructions()` method with platform-specific instructions
  - Support direct binary download for Linux, brew for macOS, go install as alternative
  - Include verification step in instructions
  - Write unit tests for each platform
  - _Requirements: 3.1, 3.3, 3.5, 3.6_

- [ ] 13. Implement kubectl installation instructions generator
  - Implement `get_kubectl_instructions()` method with platform-specific instructions
  - Support package managers and direct downloads
  - Include PATH setup instructions if needed
  - Write unit tests for each platform
  - _Requirements: 3.1, 3.3, 3.5, 3.6_

## Installation Management

- [ ] 14. Implement installation result model
  - Create `InstallationResult` dataclass with success, previous_version, new_version, prerequisites_satisfied, verification_passed, messages, errors fields
  - Implement `is_upgrade()` helper method
  - Write unit tests for data model
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 15. Implement existing installation detection
  - Create `InstallationManager` class in `mk8/business/installer.py`
  - Implement `detect_existing_installation()` method checking for mk8 in PATH
  - Run `mk8 --version` to get current version if installed
  - Return version string or None
  - Write unit tests for: not installed, installed, installed but broken
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 16. Implement virtual environment detection
  - Implement helper method `is_virtual_env()` checking sys.real_prefix and sys.base_prefix
  - Implement helper method `get_venv_info()` returning venv path and type
  - Write unit tests mocking sys attributes for venv, virtualenv, and no venv
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 17. Implement prerequisite handling for interactive mode
  - Implement `handle_missing_prerequisites()` method for interactive mode
  - Display instructions using `InstructionProvider`
  - Prompt user to install manually or automatically
  - Wait for user confirmation
  - Re-check prerequisites after user confirms
  - Write unit tests mocking user input
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 18. Implement prerequisite handling for non-interactive mode
  - Extend `handle_missing_prerequisites()` to handle non-interactive mode
  - Raise `PrerequisiteError` with installation instructions in suggestions
  - Write unit tests for non-interactive mode with missing prerequisites
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 19. Implement Python package installation with error handling
  - Implement `install_package()` method using subprocess to run pip
  - Detect if in virtual environment and adjust pip command accordingly
  - Handle common installation errors: permission denied, network issues, disk space
  - Provide specific error messages with suggestions for each error type
  - Write unit tests mocking subprocess for success and various failure modes
  - _Requirements: 8.1, 8.2, 8.6_

- [ ] 20. Implement installation orchestration
  - Implement `install()` method that orchestrates the full installation flow
  - Detect existing installation and determine if upgrade/downgrade/reinstall
  - Check prerequisites and handle missing ones based on interactive flag
  - Install package
  - Verify installation
  - Preserve configuration during updates
  - Return `InstallationResult` with complete information
  - Write integration tests for: fresh install, upgrade, prerequisites missing
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3_

- [ ] 21. Implement installation logging
  - Add detailed logging throughout installation process
  - Log all subprocess commands and their outputs
  - Log all file operations
  - Add timestamps to all log entries
  - Mask sensitive information in logs
  - Save logs to temporary file and inform user of location on error
  - Write unit tests verifying log entries for key operations
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

## Automatic Installation

- [ ] 22. Implement auto-installer capability detection
  - Create `AutoInstaller` class in `mk8/business/auto_installer.py`
  - Accept `PlatformInfo` in constructor
  - Implement `can_auto_install()` method checking if tool can be installed automatically
  - Check for package manager availability (apt, dnf, brew, etc.)
  - Write unit tests for various platforms
  - _Requirements: 4.2, 4.3_

- [ ] 23. Implement automatic kind installation
  - Implement `install_kind()` method for automatic installation
  - Download kind binary for Linux
  - Use brew for macOS
  - Handle installation failures gracefully
  - Write unit tests mocking downloads and package managers
  - _Requirements: 4.2, 4.3, 4.4_

- [ ] 24. Implement automatic kubectl installation
  - Implement `install_kubectl()` method for automatic installation
  - Use package managers where available
  - Fall back to direct download
  - Write unit tests for various platforms
  - _Requirements: 4.2, 4.3, 4.4_

- [ ] 25. Implement automatic Docker installation
  - Implement `install_docker()` method for automatic installation
  - Use package managers for Linux distributions
  - Provide guidance for macOS (Docker Desktop)
  - Write unit tests for various scenarios
  - _Requirements: 4.2, 4.3, 4.4_

## Uninstallation

- [ ] 26. Implement uninstall result model
  - Create `UninstallResult` dataclass with success, package_removed, config_removed, verified_removed, errors fields
  - Write unit tests for data model
  - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [ ] 27. Implement package removal
  - Create `UninstallManager` class in `mk8/business/uninstaller.py`
  - Implement `remove_package()` method using pip uninstall
  - Handle errors gracefully and provide manual removal instructions
  - Write unit tests mocking subprocess for success and failure cases
  - _Requirements: 9.1, 9.6_

- [ ] 28. Implement configuration removal
  - Implement `remove_configuration()` method to delete ~/.config/mk8
  - Prompt user for confirmation if in interactive mode
  - Skip prompt if --yes flag or non-interactive mode
  - Handle directory not existing gracefully
  - Write unit tests for: directory exists, directory doesn't exist, permission denied
  - _Requirements: 9.2, 9.3_

- [ ] 29. Implement uninstall verification
  - Implement `verify_removal()` method to confirm mk8 is no longer in PATH
  - Check that `shutil.which("mk8")` returns None
  - Return True if fully removed, False otherwise
  - Write unit tests for verified and not verified scenarios
  - _Requirements: 9.5_

- [ ] 30. Implement complete uninstallation flow
  - Implement `uninstall()` method orchestrating package and config removal
  - Handle interactive vs non-interactive modes
  - Verify removal after uninstall
  - Return `UninstallResult` with complete status
  - Provide manual removal instructions if uninstall fails
  - Write integration tests for: complete removal, partial removal, failures
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

## CLI Integration

- [ ] 31. Implement uninstall command
  - Create uninstall command handler in `mk8/cli/commands/uninstall.py`
  - Add uninstall command to main CLI group
  - Accept --remove-config flag to remove configuration
  - Accept --yes/-y flag to skip confirmations
  - Instantiate `UninstallManager` and run uninstallation
  - Display results and any errors
  - Write unit tests using CliRunner for interactive and non-interactive modes
  - _Requirements: 9.1, 9.2, 9.3, 9.5, 9.6_

## Standalone Installation Script

- [ ] 32. Implement standalone installation script
  - Create `scripts/install.sh` bash script
  - Check for Python 3.8+ availability
  - Install mk8 via pip
  - Run verification
  - Handle errors with clear messages
  - Write integration tests for script execution
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

## PATH Configuration

- [ ] 33. Implement shell detection
  - Implement helper to detect user's shell (bash, zsh, fish, etc.)
  - Check SHELL environment variable
  - Write unit tests for various shells
  - _Requirements: 12.1_

- [ ] 34. Implement PATH configuration
  - Implement method to add mk8 to shell profile
  - Support .bashrc, .zshrc, .config/fish/config.fish
  - Create backup before modifying
  - Prompt user for confirmation
  - Write unit tests mocking file operations
  - _Requirements: 12.2, 12.3, 12.4, 12.5_

## Integration Testing

- [ ] 35. Implement end-to-end installation test with all features
  - Create integration test for full installation with all features
  - Test platform detection
  - Test interactive mode with prompts
  - Test automatic installation
  - Test upgrade scenario
  - _Requirements: Multiple_

- [ ] 36. Implement end-to-end uninstallation test
  - Create integration test for full uninstallation
  - Test with and without config removal
  - Test interactive and non-interactive modes
  - Verify correct `UninstallResult` is returned
  - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [ ] 37. Implement platform-specific instruction test
  - Create integration test verifying correct instructions for each platform
  - Test Ubuntu, Debian, Fedora, macOS, WSL platforms
  - Verify instructions contain appropriate package manager commands
  - Verify all missing tools get instructions
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_
