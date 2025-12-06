# Requirements Document

## Introduction

The crossplane-bootstrap feature installs and configures Crossplane on the local bootstrap cluster, enabling infrastructure-as-code provisioning of AWS resources. Crossplane extends Kubernetes with custom resources that represent cloud infrastructure, allowing the bootstrap cluster to create and manage AWS resources including the management cluster.

This feature handles the complete Crossplane setup workflow: installation of Crossplane itself, installation of the AWS provider, configuration of AWS credentials, and validation that Crossplane can successfully communicate with AWS APIs.

The goal is to transform the basic kind cluster into a fully functional infrastructure provisioning platform capable of creating AWS resources through Kubernetes manifests.

## Glossary

- **Crossplane**: An open-source Kubernetes extension that enables infrastructure provisioning through Kubernetes APIs
- **Crossplane Provider**: A plugin that enables Crossplane to manage resources in a specific cloud platform (e.g., AWS, Azure, GCP)
- **ProviderConfig**: A Crossplane custom resource that configures authentication and settings for a provider
- **Managed Resource**: A Kubernetes custom resource that represents cloud infrastructure (e.g., VPC, EKS cluster)
- **Reconciliation**: The process by which Crossplane ensures actual infrastructure matches desired state
- **Bootstrap Cluster**: The local kind cluster where Crossplane is installed

## Requirements

### Requirement 1: Crossplane Installation

**User Story:** As a platform engineer, I want Crossplane automatically installed on the bootstrap cluster, so that I can provision AWS infrastructure through Kubernetes APIs.

#### Acceptance Criteria

1. WHEN the bootstrap cluster is ready THEN the system SHALL install Crossplane using Helm or kubectl manifests
2. WHEN installing Crossplane THEN the system SHALL use a specific, tested version of Crossplane
3. WHEN Crossplane is installing THEN the system SHALL monitor the deployment status and wait for Crossplane pods to be ready
4. IF Crossplane installation fails THEN the system SHALL display clear error messages including pod status and events
5. WHEN Crossplane installation times out THEN the system SHALL provide diagnostic information and suggestions
6. WHEN Crossplane is ready THEN the system SHALL verify the Crossplane API server is responding

### Requirement 2: Crossplane Version Management

**User Story:** As a platform engineer, I want to specify which version of Crossplane to install, so that I can use tested versions or upgrade when needed.

#### Acceptance Criteria

1. WHEN installing Crossplane THEN the system SHALL support a configurable version via CLI option or configuration file
2. IF no version is specified THEN the system SHALL use a tested default version
3. WHEN a specific version is requested THEN the system SHALL validate the version exists and is compatible
4. IF an invalid version is specified THEN the system SHALL display an error with available versions
5. WHEN Crossplane is already installed THEN the system SHALL detect this and offer to skip, upgrade, or reinstall

### Requirement 3: AWS Provider Installation

**User Story:** As a platform engineer, I want the AWS provider for Crossplane automatically installed, so that I can create AWS resources.

#### Acceptance Criteria

1. WHEN Crossplane is ready THEN the system SHALL install the AWS provider for Crossplane
2. WHEN installing the AWS provider THEN the system SHALL use a version compatible with the installed Crossplane version
3. WHEN the AWS provider is installing THEN the system SHALL monitor the provider pod status
4. WHEN the AWS provider pod is ready THEN the system SHALL verify the provider is healthy and ready to reconcile resources
5. IF AWS provider installation fails THEN the system SHALL display pod logs and events with diagnostic information
6. IF image pull errors occur THEN the system SHALL provide suggestions for resolving registry access issues

### Requirement 4: AWS Credentials Configuration

**User Story:** As a platform engineer, I want AWS credentials automatically configured in Crossplane, so that it can authenticate to AWS APIs.

#### Acceptance Criteria

1. WHEN the AWS provider is ready THEN the system SHALL retrieve AWS credentials from the mk8 configuration file
2. IF AWS credentials are not configured THEN the system SHALL halt and instruct the user to run `mk8 config` first
3. WHEN AWS credentials are available THEN the system SHALL create a Kubernetes secret in the Crossplane namespace containing the credentials
4. WHEN the credentials secret is created THEN the system SHALL set appropriate permissions on the secret
5. WHEN credentials are updated THEN the system SHALL update the existing secret rather than creating duplicates

### Requirement 5: ProviderConfig Creation

**User Story:** As a platform engineer, I want a ProviderConfig resource automatically created, so that Crossplane knows how to authenticate to AWS.

#### Acceptance Criteria

1. WHEN the credentials secret exists THEN the system SHALL create a ProviderConfig resource that references the secret
2. WHEN the ProviderConfig is created THEN the system SHALL specify the AWS region from configuration or use a default
3. WHEN the ProviderConfig is created THEN the system SHALL verify it is accepted by the AWS provider
4. WHEN the ProviderConfig is ready THEN the system SHALL confirm the provider can use it for authentication
5. IF the ProviderConfig fails validation THEN the system SHALL display the validation errors with suggestions

### Requirement 6: AWS Connectivity Validation

**User Story:** As a platform engineer, I want to verify that Crossplane can successfully communicate with AWS, so that I know the setup is working before attempting to provision resources.

#### Acceptance Criteria

1. WHEN the ProviderConfig is ready THEN the system SHALL test AWS API connectivity
2. WHEN testing connectivity THEN the system SHALL make a simple AWS API call to verify authentication
3. IF AWS API calls succeed THEN the system SHALL confirm that Crossplane is ready to provision AWS resources
4. IF AWS API calls fail THEN the system SHALL display AWS error codes and messages
5. IF authentication fails THEN the system SHALL suggest checking IAM permissions and credential validity
6. WHEN connectivity validation completes THEN the system SHALL provide a summary of the Crossplane setup status

### Requirement 7: IAM Permissions Verification

**User Story:** As a platform engineer, I want to verify that AWS credentials have appropriate IAM permissions, so that I can provision the management cluster without permission errors.

#### Acceptance Criteria

1. WHEN validating AWS connectivity THEN the system SHALL check for required IAM permissions
2. WHEN checking permissions THEN the system SHALL verify the credentials can create EKS clusters, VPCs, and related resources
3. IF required permissions are missing THEN the system SHALL list the missing permissions with IAM policy examples
4. WHEN permissions are sufficient THEN the system SHALL confirm the credentials are ready for management cluster provisioning
5. IF permission checks fail THEN the system SHALL provide suggestions for updating IAM policies

### Requirement 8: Crossplane Status Reporting

**User Story:** As a platform engineer, I want to check the status of Crossplane at any time, so that I can verify it's functioning correctly and troubleshoot issues.

#### Acceptance Criteria

1. WHEN checking Crossplane status THEN the system SHALL display the installed Crossplane version
2. WHEN Crossplane is installed THEN the system SHALL display pod status for all Crossplane components
3. WHEN the AWS provider is installed THEN the system SHALL display provider version and pod status
4. WHEN credentials are configured THEN the system SHALL display ProviderConfig status
5. WHEN AWS connectivity has been tested THEN the system SHALL display the last connectivity test result
6. IF any component is unhealthy THEN the system SHALL highlight the issue and suggest remediation steps
7. WHEN status check completes THEN the system SHALL indicate if Crossplane is ready to provision AWS resources

### Requirement 9: Error Detection and Diagnosis

**User Story:** As a platform engineer, I want detailed error messages with actionable suggestions when Crossplane setup fails, so that I can quickly resolve issues.

#### Acceptance Criteria

1. WHEN any operation fails THEN the system SHALL display a clear, human-readable error message
2. WHEN displaying errors THEN the system SHALL include specific suggestions for resolving the issue
3. IF Crossplane installation fails THEN the system SHALL include pod logs, events, and image pull status
4. IF AWS API calls fail THEN the system SHALL include AWS error codes and suggested IAM permissions
5. IF Crossplane managed resources fail to provision THEN the system SHALL display resource status and conditions
6. WHEN network connectivity issues are detected THEN the system SHALL distinguish between cluster issues and AWS connectivity problems
7. WHEN operations time out THEN the system SHALL provide timeout context and suggest checking underlying issues

### Requirement 10: Progressive Status Display

**User Story:** As a platform engineer, I want to see progress updates during Crossplane installation, so that I know the system is working.

#### Acceptance Criteria

1. WHEN installing Crossplane THEN the system SHALL display progress messages for major steps
2. WHEN waiting for pods to be ready THEN the system SHALL display periodic status updates
3. WHEN operations take longer than expected THEN the system SHALL inform the user that the operation is still in progress
4. WHEN verbose mode is enabled THEN the system SHALL display detailed progress including pod events and resource states
5. WHEN operations complete THEN the system SHALL provide a clear success message with next steps

### Requirement 11: Idempotent Operations

**User Story:** As a platform engineer, I want Crossplane setup operations to be idempotent, so that I can safely re-run commands without causing errors.

#### Acceptance Criteria

1. WHEN Crossplane is already installed THEN the system SHALL detect this and skip installation or offer to upgrade
2. WHEN the AWS provider is already installed THEN the system SHALL detect this and skip or update
3. WHEN AWS credentials are already configured THEN the system SHALL detect this and skip or update the configuration
4. WHEN operations are interrupted THEN the system SHALL be able to resume or cleanly restart on subsequent invocation
5. WHEN re-running status commands THEN the system SHALL always provide current, accurate information

### Requirement 12: Cleanup Support

**User Story:** As a platform engineer, I want to cleanly remove Crossplane when deleting the bootstrap cluster, so that no orphaned resources remain.

#### Acceptance Criteria

1. WHEN the bootstrap cluster is deleted THEN the system SHALL remove all Crossplane resources
2. WHEN Crossplane is removed THEN the system SHALL verify all Crossplane pods are terminated
3. WHEN cleanup completes THEN the system SHALL confirm all Crossplane components are removed
4. IF cleanup encounters errors THEN the system SHALL log the errors but continue with remaining cleanup steps
5. WHEN Crossplane is removed THEN the system SHALL inform the user that AWS credentials in the mk8 config file are preserved

## Edge Cases and Constraints

### Edge Cases
- Crossplane installation succeeds but pods crash-loop due to resource constraints
- AWS provider installation fails due to image pull errors or registry issues
- ProviderConfig creation succeeds but Crossplane cannot authenticate to AWS
- AWS credentials change externally after Crossplane is configured
- Network connectivity loss during Crossplane installation or AWS API calls
- Insufficient IAM permissions for specific AWS resources needed by management cluster
- Crossplane managed resources enter a degraded state requiring manual intervention
- Multiple Crossplane installation attempts creating duplicate resources
- Crossplane version incompatibility with AWS provider version
- AWS API rate limiting during connectivity validation

### Constraints
- Crossplane must be installed on an existing Kubernetes cluster (the bootstrap cluster)
- AWS credentials must be configured in mk8 before Crossplane setup
- The system requires internet connectivity to pull Crossplane and provider images
- Crossplane version compatibility with AWS provider must be maintained
- AWS credentials must have sufficient IAM permissions for EKS and VPC creation
- Only one ProviderConfig should exist for the AWS provider
- Crossplane installation uses default resource limits suitable for a local cluster
- The bootstrap cluster must have sufficient resources to run Crossplane components
