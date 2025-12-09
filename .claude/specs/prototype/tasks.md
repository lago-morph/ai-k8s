# Implementation Plan

- [ ] 1. Set up project structure and common utilities
  - Create directory structure (lib/, .config/)
  - Implement lib/common.sh with logging functions (log_info, log_success, log_error, log_command)
  - Implement prerequisite checking function (check_prereq)
  - Define exit codes and error handling patterns
  - _Requirements: 6.1, 6.2, 5.1, 5.4_

- [ ] 2. Implement CLI framework and routing
  - Create mk8-prototype.sh main entry point
  - Implement command-line argument parsing
  - Implement command routing logic (version, config, bootstrap, crossplane)
  - Implement help and usage display
  - Handle unknown commands with appropriate error messages
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 3. Implement AWS credentials configuration
  - Create .config/env-mk8-aws-template with dummy credentials
  - Implement lib/config.sh module
  - Implement validate_aws_credentials() function
  - Implement with_mk8_aws_env() for temporary AWS_* variable mapping
  - Validate credentials using AWS STS get-caller-identity
  - Display account information on successful validation
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.1-8.8_

- [ ] 4. Implement environment utility script
  - Create env-bootstrap.sh utility script
  - Implement KUBECONFIG environment variable setup
  - Implement AWS credentials file lookup (home directory → template)
  - Source and export MK8_* environment variables
  - Display confirmation messages
  - _Requirements: 7.4, 7.5, 8.9, 8.10, 8.11_

- [ ] 5. Implement bootstrap cluster management
  - Create lib/bootstrap.sh module
  - Implement bootstrap_create() with isolated kubeconfig
  - Implement bootstrap_status() using isolated kubeconfig
  - Implement bootstrap_delete()
  - Implement get_kubeconfig_path() helper
  - Ensure consistent cluster naming across operations
  - Log all kind and kubectl commands before execution
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.1, 7.2, 7.3_

- [ ] 6. Implement Crossplane installation
  - Create lib/crossplane.sh module
  - Implement crossplane_install() function
  - Add Helm repository with logging
  - Install Crossplane chart with visible parameters
  - Wait for Crossplane pods to be ready
  - Display pod status
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 7. Implement AWS Provider configuration
  - Implement create_aws_provider_config() function
  - Create Kubernetes secret with AWS credentials from MK8_* env vars
  - Install AWS Provider (upbound/provider-aws-s3)
  - Implement verify_aws_provider() function
  - Check Provider and ProviderConfig status
  - Verify Provider is ready to manage AWS resources
  - _Requirements: 4.5, 4.6_

- [ ] 8. Implement Crossplane status command
  - Implement crossplane_status() function
  - Display Crossplane pod status
  - Display AWS Provider status
  - Display ProviderConfig status
  - _Requirements: 4.7_

- [ ] 9. Implement S3 bucket creation
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

- [ ] 10. Implement S3 bucket deletion
  - Implement load_bucket_state() function
  - Implement crossplane_delete_s3() function
  - Read bucket name from state file
  - Delete S3 Bucket MRD
  - Verify deletion with AWS CLI
  - Implement clear_bucket_state() to clear state file
  - Handle case when no bucket exists
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [ ] 11. Create documentation
  - Create README.md with usage instructions
  - Document all commands and subcommands
  - Provide examples for each workflow
  - Document environment variable requirements
  - Document prerequisite tools (kind, kubectl, helm, aws)
  - Include troubleshooting section
  - _Requirements: 6.3, 6.4_

- [ ] 12. Integration testing checkpoint
  - Test CLI parsing (no args, help, invalid commands)
  - Test AWS credentials validation
  - Test bootstrap cluster lifecycle (create, status, delete)
  - Test env-bootstrap.sh utility
  - Test Crossplane installation and status
  - Test S3 bucket creation and deletion
  - Test create-delete-create cycle for unique UUIDs
  - Verify all commands are logged before execution
  - Verify kubeconfig isolation
  - Verify AWS environment variable isolation
  - Ensure all tests pass, ask the user if questions arise
  - _Requirements: All_
