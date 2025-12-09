# Requirements Document

## Introduction

The prototype feature provides a minimal, transparent bash-based implementation of core mk8 functionality. The primary goal is to create a working reference implementation that Kubernetes experts can easily understand, debug, and modify. Unlike the production Python implementation, this prototype prioritizes readability and visibility of underlying operations over robustness and error handling.

## Glossary

- **Prototype**: A minimal bash-based implementation of mk8 core features
- **MK8_* Environment Variables**: Environment variables prefixed with MK8_ used for configuration
- **Bootstrap Cluster**: A local Kubernetes cluster created with kind for bootstrapping infrastructure
- **Crossplane**: A Kubernetes extension for managing cloud infrastructure
- **Helm Chart**: A package format for Kubernetes applications
- **kind**: Kubernetes IN Docker - a tool for running local Kubernetes clusters

## Requirements

### Requirement 1

**User Story:** As a developer, I want a minimal CLI parser in bash, so that I can invoke prototype commands with a familiar interface.

#### Acceptance Criteria

1. WHEN a user invokes the prototype script with no arguments THEN the system SHALL display usage information showing available commands
2. WHEN a user invokes the prototype script with an unknown command THEN the system SHALL display an error message and exit with a non-zero status
3. WHEN a user invokes the prototype script with a valid command THEN the system SHALL route execution to the appropriate command handler
4. WHEN a user invokes the prototype script with `--help` or `-h` THEN the system SHALL display detailed help information for all commands
5. THE prototype script SHALL support subcommands matching the mk8 CLI structure (version, config, bootstrap, crossplane)

### Requirement 2

**User Story:** As a developer, I want simplified AWS credential management using environment variables, so that I can configure AWS access without complex file operations.

#### Acceptance Criteria

1. WHEN a user runs the config command THEN the system SHALL read AWS credentials from MK8_AWS_ACCESS_KEY_ID environment variable
2. WHEN a user runs the config command THEN the system SHALL read AWS credentials from MK8_AWS_SECRET_ACCESS_KEY environment variable
3. WHEN a user runs the config command THEN the system SHALL read AWS region from MK8_AWS_REGION environment variable
4. WHEN required MK8_* environment variables are missing THEN the system SHALL display an error message listing the missing variables
5. WHEN a user runs the config command with valid environment variables THEN the system SHALL validate the credentials by calling AWS STS get-caller-identity
6. WHEN credential validation succeeds THEN the system SHALL display the AWS account ID and user/role information

### Requirement 3

**User Story:** As a developer, I want a minimal wrapper around kind commands, so that I can create and manage local Kubernetes clusters with transparent operations.

#### Acceptance Criteria

1. WHEN a user runs `bootstrap create` THEN the system SHALL invoke kind create cluster with a predictable cluster name
2. WHEN a user runs `bootstrap create` THEN the system SHALL display the exact kind command being executed
3. WHEN a user runs `bootstrap status` THEN the system SHALL invoke kind get clusters and display cluster information
4. WHEN a user runs `bootstrap delete` THEN the system SHALL invoke kind delete cluster with the bootstrap cluster name
5. WHEN a user runs `bootstrap delete` THEN the system SHALL display the exact kind command being executed
6. THE system SHALL use a consistent cluster name across all bootstrap operations

### Requirement 4

**User Story:** As a developer, I want transparent Crossplane installation using Helm, so that I can understand and debug the installation process.

#### Acceptance Criteria

1. WHEN a user runs `crossplane install` THEN the system SHALL display the Helm repository being added
2. WHEN a user runs `crossplane install` THEN the system SHALL display the exact Helm install command with all parameters
3. WHEN a user runs `crossplane install` THEN the system SHALL install Crossplane using Helm with visible chart values
4. WHEN a user runs `crossplane install` THEN the system SHALL wait for Crossplane pods to be ready and display their status
5. WHEN a user runs `crossplane install` with AWS credentials configured THEN the system SHALL create an AWS ProviderConfig with credentials from MK8_* environment variables
6. WHEN a user runs `crossplane install` with AWS credentials configured THEN the system SHALL verify the AWS Provider is properly configured to manage AWS resources
7. WHEN a user runs `crossplane status` THEN the system SHALL display the status of Crossplane pods and AWS Provider using kubectl

### Requirement 5

**User Story:** As a Kubernetes expert, I want all operations to be transparent and debuggable, so that I can understand what the prototype is doing at each step.

#### Acceptance Criteria

1. WHEN the system executes any external command THEN the system SHALL display the full command before execution
2. WHEN the system applies Kubernetes manifests THEN the system SHALL display the manifest content or file path
3. WHEN the system uses Helm charts THEN the system SHALL display the chart name, version, and values being used
4. WHEN the system encounters an error THEN the system SHALL display the error message and the command that failed
5. THE system SHALL use minimal abstraction layers between user commands and underlying tools (kind, kubectl, helm)

### Requirement 6

**User Story:** As a developer, I want the prototype to be self-contained and minimal, so that I can easily understand and modify the entire codebase.

#### Acceptance Criteria

1. THE prototype SHALL be implemented as a single bash script or a small collection of bash scripts
2. THE prototype SHALL have minimal external dependencies beyond kind, kubectl, helm, and aws CLI
3. THE prototype SHALL not require installation or complex setup procedures
4. WHEN a user views the prototype source code THEN the system SHALL be readable and well-commented
5. THE prototype SHALL prioritize simplicity over error handling and edge case coverage

### Requirement 7

**User Story:** As a developer, I want isolated kubeconfig management, so that the prototype does not interfere with my existing Kubernetes configurations.

#### Acceptance Criteria

1. WHEN the system creates a bootstrap cluster THEN the system SHALL store the kubeconfig in a dedicated directory separate from ~/.kube/config
2. THE system SHALL never merge kubeconfig into ~/.kube/config
3. WHEN the system executes kubectl commands THEN the system SHALL use the isolated kubeconfig via --kubeconfig flag or KUBECONFIG environment variable
4. THE system SHALL provide a utility script that can be sourced to set KUBECONFIG environment variable
5. WHEN a user sources the utility script THEN the system SHALL set KUBECONFIG to point to the bootstrap cluster kubeconfig

### Requirement 8

**User Story:** As a developer, I want strict AWS environment variable isolation, so that the prototype does not interfere with my existing AWS CLI configuration.

#### Acceptance Criteria

1. THE system SHALL only read AWS credentials from MK8_AWS_ACCESS_KEY_ID environment variable
2. THE system SHALL only read AWS credentials from MK8_AWS_SECRET_ACCESS_KEY environment variable
3. THE system SHALL only read AWS region from MK8_AWS_REGION environment variable
4. THE system SHALL never read from standard AWS_ACCESS_KEY_ID environment variable
5. THE system SHALL never read from standard AWS_SECRET_ACCESS_KEY environment variable
6. THE system SHALL never read from standard AWS_REGION environment variable
7. WHEN the system needs to call AWS CLI THEN the system SHALL temporarily map MK8_* variables to AWS_* variables within a subshell
8. WHEN the AWS CLI call completes THEN the system SHALL ensure standard AWS_* variables are unset
9. THE system SHALL provide a template file with dummy AWS credentials at .config/env-mk8-aws-template
10. WHEN the env-bootstrap.sh utility is sourced THEN the system SHALL load credentials from ~/.config/env-mk8-aws if it exists
11. WHEN ~/.config/env-mk8-aws does not exist THEN the system SHALL load credentials from .config/env-mk8-aws-template

### Requirement 9

**User Story:** As a developer, I want to create test S3 buckets via Crossplane, so that I can verify Crossplane is properly managing AWS resources.

#### Acceptance Criteria

1. WHEN a user runs `crossplane create-s3` THEN the system SHALL generate a unique bucket name with format test-s3-bucket-<uuid>
2. WHEN a user runs `crossplane create-s3` THEN the system SHALL apply a Crossplane S3 Bucket MRD with the generated name
3. WHEN a user runs `crossplane create-s3` THEN the system SHALL wait for the MRD to be ready and display its status
4. WHEN a user runs `crossplane create-s3` THEN the system SHALL verify bucket creation using AWS CLI
5. WHEN a user runs `crossplane create-s3` THEN the system SHALL save the bucket name to ~/.config/mk8-prototype-state
6. WHEN a user runs `crossplane create-s3` and a bucket already exists THEN the system SHALL display an error message
7. THE system SHALL support only one S3 bucket at a time

### Requirement 10

**User Story:** As a developer, I want to delete test S3 buckets created via Crossplane, so that I can clean up test resources.

#### Acceptance Criteria

1. WHEN a user runs `crossplane delete-s3` THEN the system SHALL read the bucket name from ~/.config/mk8-prototype-state
2. WHEN a user runs `crossplane delete-s3` THEN the system SHALL delete the Crossplane S3 Bucket MRD
3. WHEN a user runs `crossplane delete-s3` THEN the system SHALL verify bucket deletion using AWS CLI
4. WHEN a user runs `crossplane delete-s3` THEN the system SHALL clear the state file ~/.config/mk8-prototype-state
5. WHEN a user runs `crossplane delete-s3` and no bucket exists THEN the system SHALL display an error message
6. WHEN a user creates, deletes, then creates again THEN the system SHALL generate a new UUID for the new bucket
