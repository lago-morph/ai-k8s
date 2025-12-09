# Implementation Plan

- [x] 1. Set up project structure and common utilities
  - Create directory structure (lib/, .config/)
  - Implement lib/common.sh with logging functions (log_info, log_success, log_error, log_command)
  - Implement prerequisite checking function (check_prereq)
  - Define exit codes and error handling patterns
  - _Requirements: 6.1, 6.2, 5.1, 5.4_

- [x] 2. Set up testing framework
  - Install BATS (Bash Automated Testing System)
  - Create tests/ directory structure (tests/unit/, tests/integration/)
  - Create test helper functions (setup_test_env, teardown_test_env)
  - Configure shellcheck for static analysis
  - Create test running script (run-tests.sh)
  - _Requirements: Testing infrastructure_

- [x] 3. Unit tests for common utilities
  - Write tests for log_info, log_success, log_error functions
  - Write tests for log_command function
  - Write tests for check_prereq function
  - Write tests for exit code handling
  - Verify all tests pass with BATS
  - Run shellcheck on lib/common.sh
  - _Requirements: 6.1, 6.2, 5.1, 5.4_

- [x] 4. Implement CLI framework and routing
  - Create mk8-prototype.sh main entry point
  - Implement command-line argument parsing
  - Implement command routing logic (version, config, bootstrap, crossplane)
  - Implement help and usage display
  - Handle unknown commands with appropriate error messages
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 5. Unit tests for CLI framework
  - Write tests for CLI argument parsing (no args, help, version)
  - Write tests for command routing (valid and invalid commands)
  - Write tests for help and usage display
  - Write tests for unknown command error handling
  - Verify all tests pass with BATS
  - Run shellcheck on mk8-prototype.sh
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 6. Implement AWS credentials configuration
  - Create .config/env-mk8-aws-template with dummy credentials
  - Implement lib/config.sh module
  - Implement validate_aws_credentials() function
  - Implement with_mk8_aws_env() for temporary AWS_* variable mapping
  - Validate credentials using AWS STS get-caller-identity
  - Display account information on successful validation
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.1-8.8_

- [x] 7. Unit tests for AWS credentials configuration
  - Write tests for missing MK8_* environment variables detection
  - Write tests for with_mk8_aws_env() temporary variable mapping
  - Write tests for AWS variable isolation (verify AWS_* vars not used)
  - Write tests for credential validation error handling
  - Verify all tests pass with BATS
  - Run shellcheck on lib/config.sh
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.1-8.8_

- [x] 8. Implement environment utility script
  - Create env-bootstrap.sh utility script
  - Implement KUBECONFIG environment variable setup
  - Implement AWS credentials file lookup (home directory → template)
  - Source and export MK8_* environment variables
  - Display confirmation messages
  - _Requirements: 7.4, 7.5, 8.9, 8.10, 8.11_

- [x] 9. Unit tests for environment utility script
  - Write tests for KUBECONFIG environment variable setup
  - Write tests for AWS credentials file lookup (home vs template)
  - Write tests for MK8_* variable sourcing and export
  - Write tests for confirmation message display
  - Verify all tests pass with BATS
  - Run shellcheck on env-bootstrap.sh
  - _Requirements: 7.4, 7.5, 8.9, 8.10, 8.11_

- [ ] 10. Implement bootstrap cluster management
  - Create lib/bootstrap.sh module
  - Implement bootstrap_create() with isolated kubeconfig
  - Implement bootstrap_status() using isolated kubeconfig
  - Implement bootstrap_delete()
  - Implement get_kubeconfig_path() helper
  - Ensure consistent cluster naming across operations
  - Log all kind and kubectl commands before execution
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.1, 7.2, 7.3_

- [ ] 11. Unit tests for bootstrap cluster management
  - Write tests for get_kubeconfig_path() helper
  - Write tests for cluster name consistency
  - Write tests for kubeconfig isolation (never modifies ~/.kube/config)
  - Write tests for command logging (kind, kubectl)
  - Write tests for error handling (cluster already exists, cluster not found)
  - Verify all tests pass with BATS
  - Run shellcheck on lib/bootstrap.sh
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.1, 7.2, 7.3_

- [ ] 12. Implement Crossplane installation
  - Create lib/crossplane.sh module
  - Implement crossplane_install() function
  - Add Helm repository with logging
  - Install Crossplane chart with visible parameters
  - Wait for Crossplane pods to be ready
  - Display pod status
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 13. Implement AWS Provider configuration
  - Implement create_aws_provider_config() function
  - Create Kubernetes secret with AWS credentials from MK8_* env vars
  - Install AWS Provider (upbound/provider-aws-s3)
  - Implement verify_aws_provider() function
  - Check Provider and ProviderConfig status
  - Verify Provider is ready to manage AWS resources
  - _Requirements: 4.5, 4.6_

- [ ] 14. Implement Crossplane status command
  - Implement crossplane_status() function
  - Display Crossplane pod status
  - Display AWS Provider status
  - Display ProviderConfig status
  - _Requirements: 4.7_

- [ ] 15. Unit tests for Crossplane modules
  - Write tests for crossplane_install() function
  - Write tests for create_aws_provider_config() credentials handling
  - Write tests for verify_aws_provider() status checks
  - Write tests for crossplane_status() display functions
  - Write tests for Helm command logging
  - Verify all tests pass with BATS
  - Run shellcheck on lib/crossplane.sh
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [ ] 16. Implement S3 bucket creation
  - Implement generate_bucket_name() with UUID generation
  - Implement crossplane_create_s3() function
  - Create S3 Bucket MRD manifest
  - Apply MRD to cluster
  - Wait for MRD to be ready
  - Display MRD status
  - Verify bucket creation with AWS CLI
  - Implement save_bucket_state() to store bucket name
  - Check for existing bucket before creation
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 17. Implement S3 bucket deletion
  - Implement load_bucket_state() function
  - Implement crossplane_delete_s3() function
  - Read bucket name from state file
  - Delete S3 Bucket MRD
  - Verify deletion with AWS CLI
  - Implement clear_bucket_state() to clear state file
  - Handle case when no bucket exists
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [ ] 18. Unit tests for S3 bucket management
  - Write tests for generate_bucket_name() UUID generation
  - Write tests for save_bucket_state() and load_bucket_state()
  - Write tests for clear_bucket_state()
  - Write tests for bucket existence checking
  - Write tests for state file error handling (missing, corrupted)
  - Write tests for create-delete-create cycle (unique UUIDs)
  - Verify all tests pass with BATS
  - _Requirements: 9.1-9.7, 10.1-10.6_

- [ ] 19. Create documentation
  - Create README.md with usage instructions
  - Document all commands and subcommands
  - Provide examples for each workflow
  - Document environment variable requirements
  - Document prerequisite tools (kind, kubectl, helm, aws)
  - Document how to run tests (BATS and shellcheck)
  - Include troubleshooting section
  - _Requirements: 6.3, 6.4_

- [ ] 20. Comprehensive integration tests
  - Write end-to-end test: CLI parsing workflow (no args, help, invalid commands, version)
  - Write end-to-end test: AWS credentials validation workflow (missing vars, invalid creds, valid creds)
  - Write end-to-end test: Bootstrap cluster lifecycle (create, status, delete)
  - Write end-to-end test: env-bootstrap.sh utility (KUBECONFIG setup, credentials sourcing)
  - Write end-to-end test: Crossplane installation and AWS Provider configuration
  - Write end-to-end test: S3 bucket creation and deletion workflow
  - Write end-to-end test: create-delete-create cycle for unique UUIDs
  - Write integration test: Verify all commands are logged before execution
  - Write integration test: Verify kubeconfig isolation (never touches ~/.kube/config)
  - Write integration test: Verify AWS environment variable isolation (MK8_* only)
  - Run all integration tests and ensure they pass
  - Generate test coverage report
  - _Requirements: All_

- [ ] 21. Final validation and cleanup
  - Run all unit tests with BATS and verify 100% pass rate
  - Run all integration tests and verify 100% pass rate
  - Run shellcheck on all bash scripts (zero violations)
  - Verify test coverage meets requirements
  - Review and update documentation based on test results
  - Clean up any temporary test files or artifacts
  - Final smoke test of all commands
  - _Requirements: All_
