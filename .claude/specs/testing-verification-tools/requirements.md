# Requirements Document - Testing Verification Tools

**STATUS: DRAFT - NOT REVIEWED**

This document is in draft status and requires review and refinement before proceeding to design phase.

## Introduction

This feature provides read-only verification capabilities for Kubernetes and AWS resources during integration testing of the mk8 CLI tool. By using kubectl and AWS CLI directly, AI agents and test scripts can verify that resources are created correctly, providing multiple independent verification methods to increase confidence in test results.

The primary goal is to augment integration tests with direct API verification, catching issues that might not be visible through mk8's own output or kind commands alone.

## Glossary

- **kubectl**: The official Kubernetes command-line tool for interacting with Kubernetes clusters
- **AWS CLI**: The official Amazon Web Services command-line interface
- **Read-Only Access**: API access limited to read operations (get, list, describe) with no mutation capabilities
- **Integration Test**: Automated test that verifies mk8 functionality against real or simulated infrastructure
- **BATS**: Bash Automated Testing System - shell script testing framework used by mk8
- **IAM**: AWS Identity and Access Management - service for managing AWS permissions
- **RBAC**: Role-Based Access Control - Kubernetes authorization mechanism
- **Kubeconfig**: Configuration file containing Kubernetes cluster credentials and connection information
- **MRD**: Managed Resource Definition - Crossplane custom resource representing cloud infrastructure
- **Ephemeral Account**: Temporary AWS account with limited lifetime (4 hours in mk8's case)

## Requirements

### Requirement 1: kubectl CLI Integration

**User Story:** As an integration test, I want to use kubectl to verify Kubernetes resource state, so that I can confirm resources are created correctly.

#### Acceptance Criteria

1. WHEN an integration test needs to verify cluster state THEN the system SHALL use kubectl with the appropriate kubeconfig
2. WHEN mk8 creates a bootstrap cluster THEN the system SHALL provide the kubeconfig path for kubectl access
3. WHEN using kubectl for verification THEN the system SHALL use read-only operations only (`get`, `list`, `describe`, `logs`)
4. WHEN kubectl commands fail THEN the system SHALL capture and parse error messages for test reporting
5. WHEN multiple clusters exist THEN the system SHALL support specifying kubeconfig via `--kubeconfig` flag or `KUBECONFIG` environment variable

### Requirement 2: AWS CLI Integration

**User Story:** As an integration test, I want to use AWS CLI to verify AWS resource state, so that I can confirm resources are provisioned correctly.

#### Acceptance Criteria

1. WHEN an integration test needs to verify AWS resources THEN the system SHALL use AWS CLI with appropriate credentials
2. WHEN using AWS CLI for verification THEN the system SHALL use read-only operations only (`describe-*`, `get-*`, `list-*`)
3. WHEN AWS CLI commands fail THEN the system SHALL capture and parse error messages for test reporting
4. WHEN checking EKS clusters THEN the system SHALL verify cluster status, version, and configuration
5. WHEN checking Crossplane MRDs THEN the system SHALL verify corresponding AWS resources exist and match expected state

### Requirement 3: Credential Management for Kubernetes

**User Story:** As a developer, I want to easily configure kubectl access to test clusters, so that integration tests can verify cluster state.

#### Acceptance Criteria

1. WHEN mk8 creates a bootstrap cluster THEN the system SHALL generate a kubeconfig file at a known location
2. WHEN integration tests run THEN the system SHALL discover the kubeconfig from mk8 output or standard locations
3. WHEN using kubeconfig THEN the system SHALL verify the credentials are valid before running tests
4. WHEN Crossplane creates a workload cluster THEN the system SHALL provide a command to generate kubeconfig for that cluster
5. WHERE read-only access is required THEN the system SHALL support creating a ServiceAccount with read-only RBAC

### Requirement 4: Credential Management for AWS

**User Story:** As a developer, I want to easily configure AWS CLI access with ephemeral credentials, so that integration tests can verify AWS resources.

#### Acceptance Criteria

1. WHEN using ephemeral AWS accounts THEN the system SHALL support credential configuration via environment variables
2. WHEN AWS credentials are set THEN the system SHALL use `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables
3. WHEN credentials need rotation THEN the system SHALL provide a helper script for easy credential updates
4. WHEN AWS CLI is used THEN the system SHALL verify credentials are valid before running tests
5. WHERE read-only access is required THEN the system SHALL provide an IAM policy template with only read permissions

### Requirement 5: Read-Only IAM Policy

**User Story:** As a developer, I want to create an AWS IAM policy that grants only read permissions, so that test credentials cannot accidentally modify infrastructure.

#### Acceptance Criteria

1. WHEN creating a read-only IAM policy THEN the system SHALL include only `Describe*`, `Get*`, and `List*` actions
2. WHEN the IAM policy is created THEN the system SHALL document each permission with inline comments explaining its purpose
3. WHEN the IAM policy is complex THEN the system SHALL organize permissions by AWS service for readability
4. WHEN applying the IAM policy THEN the system SHALL support creation via AWS CLI for use in ephemeral environments
5. WHERE the IAM policy is used THEN the system SHALL verify it grants sufficient permissions for mk8 testing needs

### Requirement 6: Integration Test Verification Patterns

**User Story:** As an integration test, I want common verification patterns for Kubernetes and AWS resources, so that tests are consistent and maintainable.

#### Acceptance Criteria

1. WHEN verifying a Kubernetes cluster exists THEN the system SHALL check cluster-info and node status
2. WHEN verifying Crossplane installation THEN the system SHALL check Crossplane pods are running and CRDs are installed
3. WHEN verifying AWS EKS cluster THEN the system SHALL check cluster status is ACTIVE and matches expected configuration
4. WHEN verifying Crossplane MRDs THEN the system SHALL check both Kubernetes resource status and corresponding AWS resource existence
5. WHEN verification fails THEN the system SHALL provide detailed error messages indicating what was expected vs. actual state

### Requirement 7: Error Handling and Diagnostics

**User Story:** As a developer, I want clear error messages when verification fails, so that I can quickly diagnose test failures.

#### Acceptance Criteria

1. WHEN kubectl commands fail THEN the system SHALL capture stderr and include it in test output
2. WHEN AWS CLI commands fail THEN the system SHALL capture error codes and messages for debugging
3. WHEN credentials are invalid THEN the system SHALL provide clear instructions for updating credentials
4. WHEN resources are not found THEN the system SHALL distinguish between "not yet created" and "creation failed"
5. WHEN rate limits are hit THEN the system SHALL provide retry guidance or wait times

### Requirement 8: Integration with mk8 Test Framework

**User Story:** As a test developer, I want verification tools to integrate seamlessly with mk8's existing test framework, so that tests are easy to write and maintain.

#### Acceptance Criteria

1. WHEN writing BATS tests THEN the system SHALL provide shell functions for common verification operations
2. WHEN writing pytest tests THEN the system SHALL provide Python helper functions for verification
3. WHEN tests run in CI/CD THEN the system SHALL support credential configuration via environment variables
4. WHEN tests run locally THEN the system SHALL support credential configuration via local files
5. WHEN verification is used THEN the system SHALL log all verification operations for debugging

## Open Questions and Decisions

See `CONTEXT.md` and `SCOPE-DECISIONS.md` in this directory for:
- Detailed context from the initial planning discussion
- Unresolved decisions about integration test framework scope
- Credential management implementation details
- IAM policy creation and management approach
- Future enhancements and considerations

## Notes

**Scope Deferral**: The exact scope of helper functions and integration test framework enhancements is deferred to the design phase. See `SCOPE-DECISIONS.md` for questions that need to be answered before design.

**IAM Policy**: The IAM policy will be created during the design phase. The decision of whether humans or agents create/apply the policy is deferred.

**Credential Rotation**: For ephemeral AWS accounts with 4-hour lifetimes, the credential rotation mechanism must be simple and fast. Environment variables are preferred for this reason.
