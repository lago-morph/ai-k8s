# Implementation Plan: GitOps Repository Setup

## Overview

This implementation plan follows the layered architecture: data models → integrations → business logic → CLI.

---

## Tasks

- [ ] 1. Create data models and configuration
  - [ ] 1.1 Create GitOps data models
    - Create `mk8/business/gitops_models.py` with GitOpsRepository, GitOpsStatus, ValidationResult, ValidationError, DirectoryStructure dataclasses
    - Include type hints and docstrings
    - _Requirements: 7.1, 7.2, 7.3, 13.1, 13.2_
  - [ ]* 1.2 Write property test for data models
    - **Property 13: Configuration File Completeness**
    - Test that GitOpsRepository contains all required fields
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [ ] 2. Implement Git client integration
  - [ ] 2.1 Create GitClient class
    - Create `mk8/integrations/git_client.py`
    - Implement init_repository, is_git_repository, add_remote, commit, push, create_branch, get_current_branch, get_last_commit
    - Use subprocess with shell=False for security
    - _Requirements: 2.1, 8.3, 9.1, 9.2, 9.4, 10.4_
  - [ ]* 2.2 Write property tests for GitClient
    - **Property 1: Path Validation** - Valid Git repos pass validation
    - **Property 2: Repository Initialization** - Init creates valid Git repo
    - **Property 15: Git Remote Addition** - Remote appears in config after add
    - **Validates: Requirements 1.4, 2.1, 2.2, 8.3**
  - [ ]* 2.3 Write unit tests for GitClient
    - Test error handling for missing Git
    - Test error handling for invalid paths
    - Test subprocess command construction
    - _Requirements: 14.1, 14.2_

- [ ] 3. Implement file generator
  - [ ] 3.1 Create FileGenerator class
    - Create `mk8/business/file_generator.py`
    - Implement create_directory_structure, generate_crossplane_templates, generate_helm_chart, generate_argocd_application, generate_readme
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 6.1, 12.1_
  - [ ] 3.2 Create template content
    - Create Crossplane EKS cluster, VPC, IAM templates with placeholders
    - Create Helm Chart.yaml and values.yaml templates
    - Create ArgoCD Application template
    - Create README templates for each directory
    - _Requirements: 4.4, 4.5, 5.4, 6.2, 6.3, 6.4, 6.5, 12.2, 12.3, 12.4, 12.5_
  - [ ]* 3.3 Write property tests for FileGenerator
    - **Property 4: Complete Directory Structure** - All required directories exist
    - **Property 5: Directory Documentation** - Each directory has README
    - **Property 6: Crossplane Template Completeness** - All templates exist
    - **Property 7: Template Placeholder Presence** - Templates have placeholders
    - **Property 9: Helm Chart Structure Validity** - Valid Chart.yaml, templates/, values.yaml
    - **Property 10: Environment Values Files** - values-dev.yaml, values-prod.yaml exist
    - **Validates: Requirements 3.1-3.5, 4.1-4.4, 5.1-5.4**
  - [ ]* 3.4 Write unit tests for FileGenerator
    - Test directory creation
    - Test template content correctness
    - Test README content
    - _Requirements: 3.5, 4.5, 12.2, 12.3, 12.4, 12.5_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement GitOps validator
  - [ ] 5.1 Create GitOpsValidator class
    - Create `mk8/business/gitops_validator.py`
    - Implement validate_directory_structure, validate_helm_charts, validate_yaml_files, validate_crossplane_manifests, validate_argocd_applications
    - Return ValidationResult with detailed errors
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  - [ ]* 5.2 Write property tests for GitOpsValidator
    - **Property 11: YAML Syntax Validity** - All generated YAML is parseable
    - **Property 23: Structure Validation Completeness** - Validation checks all components
    - **Validates: Requirements 5.5, 11.1, 11.2, 11.3, 11.4**
  - [ ]* 5.3 Write unit tests for GitOpsValidator
    - Test validation of valid structure
    - Test detection of missing directories
    - Test detection of invalid YAML
    - Test error message formatting
    - _Requirements: 11.5, 14.1, 14.2_

- [ ] 6. Implement GitOps configuration manager
  - [ ] 6.1 Create GitOpsConfigManager class
    - Create `mk8/business/gitops_config.py`
    - Implement save_config, load_config, config_exists
    - Store in ~/.config/mk8/gitops.yaml
    - Set file permissions to 0600
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - [ ]* 6.2 Write property tests for GitOpsConfigManager
    - **Property 14: Configuration File Permissions** - File has 0600 permissions
    - **Validates: Requirements 7.5**
  - [ ]* 6.3 Write unit tests for GitOpsConfigManager
    - Test config save and load round-trip
    - Test handling of missing config
    - Test permission setting
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement GitOps manager (business logic orchestrator)
  - [ ] 8.1 Create GitOpsManager class
    - Create `mk8/business/gitops_manager.py`
    - Implement initialize_repository (new and existing), get_status, validate_repository
    - Orchestrate GitClient, FileGenerator, GitOpsValidator, GitOpsConfigManager
    - Handle user prompts for repository type selection
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5_
  - [ ] 8.2 Implement existing repository integration
    - Check for conflicts with existing directories
    - Create new branch for GitOps structure
    - Preserve existing files
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  - [ ] 8.3 Implement Git remote configuration
    - Prompt for remote URL
    - Add remote to repository
    - Verify remote accessibility
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - [ ] 8.4 Implement commit and push workflow
    - Stage all generated files
    - Create commit with descriptive message
    - Prompt for push confirmation
    - Push to remote if confirmed
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  - [ ]* 8.5 Write property tests for GitOpsManager
    - **Property 3: Git Configuration Preservation** - Existing Git config unchanged
    - **Property 17: Complete File Staging** - All files staged after setup
    - **Property 18: Commit Creation** - Commit exists with message
    - **Property 20: Conflict Detection** - Conflicts detected before changes
    - **Property 21: File Preservation** - Existing files unchanged
    - **Property 22: Branch Creation for Existing Repos** - New branch created
    - **Validates: Requirements 2.3, 9.1, 9.2, 10.1, 10.3, 10.4**
  - [ ]* 8.6 Write unit tests for GitOpsManager
    - Test new repository initialization flow
    - Test existing repository integration flow
    - Test error handling and suggestions
    - _Requirements: 1.1-1.5, 2.1-2.5, 10.1-10.5_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement CLI commands
  - [ ] 10.1 Create gitops command group
    - Create `mk8/cli/commands/gitops.py`
    - Implement `mk8 gitops` command group
    - Register with main CLI
    - _Requirements: 1.1_
  - [ ] 10.2 Implement gitops init command
    - Add --path option for repository path
    - Add --remote option for remote URL
    - Add --existing flag for existing repositories
    - Display progress and results
    - _Requirements: 1.1, 1.2, 1.3, 2.4, 8.1, 8.2_
  - [ ] 10.3 Implement gitops status command
    - Display repository path and type
    - Display remote URL if configured
    - Display last commit information
    - Display validation status
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  - [ ] 10.4 Implement gitops validate command
    - Run full validation
    - Display errors with file paths and line numbers
    - Display suggestions for fixing issues
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  - [ ]* 10.5 Write property tests for CLI commands
    - **Property 25: Status Information Completeness** - Status shows all required info
    - **Property 26: Error Message Quality** - Errors are human-readable with suggestions
    - **Validates: Requirements 13.1-13.5, 14.1, 14.2**
  - [ ]* 10.6 Write unit tests for CLI commands
    - Test gitops init with various options
    - Test gitops status output
    - Test gitops validate output
    - Test error handling and exit codes
    - _Requirements: 1.1-1.5, 13.1-13.5, 14.1-14.5_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Integration and documentation
  - [ ] 12.1 Integration testing
    - Test full workflow: init → validate → status
    - Test with new repository
    - Test with existing repository
    - Test error scenarios
    - _Requirements: All_
  - [ ] 12.2 Update mk8 documentation
    - Add gitops commands to README
    - Document GitOps workflow
    - Add troubleshooting guide
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 13. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
