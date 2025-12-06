# Requirements Document

## ⚠️ DEPRECATED - This Spec Has Been Split

This specification has been broken down into smaller, more manageable specs for easier implementation and testing:

1. **local-kind-cluster** - Basic kind cluster lifecycle (create, delete, status) + kubeconfig handling
2. **crossplane-bootstrap** - Crossplane + AWS provider installation, credential configuration, and AWS connectivity testing
3. **gitops-repository-setup** - Create/configure Git repository with proper structure for GitOps
4. **argocd-bootstrap** - Install ArgoCD in bootstrap cluster and configure it to manage management cluster provisioning via GitOps

Please refer to these individual specs instead of this document.

---

## Original Introduction (For Reference)

The local-bootstrap-cluster feature creates a temporary local Kubernetes cluster running in kind that serves as a bootstrap environment for provisioning infrastructure on AWS using Crossplane. This bootstrap cluster is a critical first step in a multi-tier cluster architecture where infrastructure is managed as code through Kubernetes custom resources.

The overall architecture follows this pattern:
1. **Bootstrap Cluster** (local kind cluster) - Temporary cluster on the developer's local machine that installs Crossplane with AWS credentials
2. **Management Cluster** (AWS) - Provisioned by the bootstrap cluster via Crossplane, this cluster manages the lifecycle of workload clusters
3. **Workload Clusters** (AWS) - Application clusters created and managed by the management cluster

The bootstrap cluster is **temporary and single-purpose**. Once the AWS management cluster is successfully provisioned, the bootstrap cluster is no longer needed and can be destroyed.

This feature is accessed through the `mk8 bootstrap` command, part of the mk8 CLI tool. This specification focuses specifically on the lifecycle management of the bootstrap cluster itself: creation, status monitoring, and deletion.

## Requirements

### Requirement 1: Bootstrap Command Structure
**User Story:** As a platform engineer, I want dedicated commands for bootstrap cluster operations, so that I can manage the bootstrap cluster lifecycle.

#### Acceptance Criteria
1. WHEN the user executes `mk8 bootstrap` THEN the system SHALL provide a help message listing available bootstrap subcommands (create, delete, status)
2. WHEN the user executes `mk8 bootstrap create` THEN the system SHALL initiate the bootstrap cluster creation workflow
3. WHEN the user executes `mk8 bootstrap delete` THEN the system SHALL remove the bootstrap cluster and all associated resources
4. WHEN the user executes `mk8 bootstrap status` THEN the system SHALL display the current state of the bootstrap cluster and Crossplane installation
5. WHEN the user requests help for any bootstrap subcommand THEN the system SHALL display contextual help for that specific subcommand

### Requirement 2: Prerequisites Validation
**User Story:** As a platform engineer, I want comprehensive prerequisite checking before bootstrap operations begin, so that I receive clear guidance on what needs to be installed or configured.

#### Acceptance Criteria
1. WHEN validating prerequisites THEN the system SHALL check for Docker installation and verify the Docker daemon is running
2. WHEN validating prerequisites THEN the system SHALL check for kind binary installation and verify it is executable
3. WHEN validating prerequisites THEN the system SHALL check for kubectl installation and verify it is in the system PATH
4. IF any prerequisite is missing THEN the system SHALL display a clear error message identifying the missing component with installation instructions
5. IF Docker daemon is not running THEN the system SHALL provide platform-specific instructions to start Docker
6. WHEN all prerequisites are satisfied THEN the system SHALL proceed with the requested operation

### Requirement 3: Bootstrap Cluster Creation
**User Story:** As a platform engineer, I want to create a local kind cluster optimized for Crossplane and AWS provisioning, so that I have a reliable bootstrap environment.

#### Acceptance Criteria
1. WHEN the user executes `mk8 bootstrap create` THEN the system SHALL create a kind cluster with a deterministic name (e.g., "mk8-bootstrap")
2. WHEN creating the kind cluster THEN the system SHALL use a configuration that enables necessary features for Crossplane operation
3. WHEN the kind cluster is created THEN the system SHALL verify cluster readiness by checking node status
4. IF kind cluster creation fails THEN the system SHALL display the error from kind with suggestions for common issues (disk space, port conflicts, Docker issues)
5. WHEN cluster creation succeeds THEN the system SHALL set the kubectl context to the new bootstrap cluster
6. WHEN cluster already exists THEN the system SHALL detect this and either skip creation or prompt the user for action
7. WHEN cluster creation completes THEN the system SHALL proceed to install Crossplane

### Requirement 4: Crossplane Installation
**User Story:** As a platform engineer, I want Crossplane automatically installed and configured on the bootstrap cluster, so that I can immediately begin provisioning AWS infrastructure.

#### Acceptance Criteria
1. WHEN the bootstrap cluster is ready THEN the system SHALL install Crossplane using Helm or kubectl manifests
2. WHEN installing Crossplane THEN the system SHALL use a specific, tested version of Crossplane (configurable via CLI option or default)
3. WHEN Crossplane is installing THEN the system SHALL monitor the deployment status and wait for Crossplane pods to be ready
4. IF Crossplane installation fails THEN the system SHALL display clear error messages including pod status, events, and logs
5. WHEN Crossplane installation times out THEN the system SHALL provide diagnostic information and suggestions (check cluster resources, network connectivity, image pull issues)
6. WHEN Crossplane is ready THEN the system SHALL install the AWS provider for Crossplane
7. WHEN the AWS provider is installed THEN the system SHALL verify the provider pod is running and healthy
8. WHEN Crossplane and AWS provider are ready THEN the system SHALL proceed to configure AWS credentials

### Requirement 5: AWS Credentials Configuration in Crossplane
**User Story:** As a platform engineer, I want AWS credentials automatically configured in Crossplane, so that the bootstrap cluster can provision AWS resources.

#### Acceptance Criteria
1. WHEN Crossplane and the AWS provider are ready THEN the system SHALL retrieve AWS credentials from the mk8 configuration file
2. WHEN AWS credentials are available THEN the system SHALL create a Kubernetes secret in the Crossplane namespace containing the credentials
3. WHEN the credentials secret is created THEN the system SHALL create a ProviderConfig resource that references the secret
4. WHEN the ProviderConfig is created THEN the system SHALL verify it is accepted by the AWS provider
5. IF AWS credentials are not configured THEN the system SHALL halt and instruct the user to run `mk8 config` first
6. WHEN credentials configuration completes THEN the system SHALL validate AWS connectivity by testing the credentials
7. IF AWS API validation succeeds THEN the system SHALL confirm that the bootstrap cluster is ready for use

### Requirement 6: Bootstrap Status Reporting
**User Story:** As a platform engineer, I want to check the status of my bootstrap cluster at any time, so that I can verify it's functioning correctly and troubleshoot issues.

#### Acceptance Criteria
1. WHEN the user executes `mk8 bootstrap status` THEN the system SHALL check if the kind cluster exists
2. IF the cluster does not exist THEN the system SHALL report that no bootstrap cluster is found
3. WHEN the bootstrap cluster exists THEN the system SHALL display cluster status (running, stopped, error)
4. WHEN the cluster is running THEN the system SHALL display Crossplane installation status (installed version, pod status)
5. WHEN Crossplane is installed THEN the system SHALL display AWS provider status (version, pod status, provider readiness)
6. WHEN AWS credentials are configured THEN the system SHALL display ProviderConfig status
7. WHEN status includes AWS connectivity THEN the system SHALL test AWS API access and report the result
8. IF any component is unhealthy THEN the system SHALL highlight the issue and suggest remediation steps
9. WHEN status check completes THEN the system SHALL provide a summary indicating if the bootstrap cluster is ready for management cluster provisioning

### Requirement 7: Error Detection and Diagnosis
**User Story:** As a platform engineer, I want detailed error messages with actionable suggestions when things go wrong, so that I can quickly resolve issues without deep Kubernetes or Crossplane expertise.

#### Acceptance Criteria
1. WHEN any operation fails THEN the system SHALL display a clear, human-readable error message describing what went wrong
2. WHEN displaying errors THEN the system SHALL include one or more specific suggestions for resolving the issue
3. IF a kind cluster operation fails THEN the system SHALL include kind-specific diagnostics (Docker status, port availability, resource usage)
4. IF Crossplane installation fails THEN the system SHALL include pod logs, events, and image pull status
5. IF AWS API calls fail THEN the system SHALL include AWS error codes, suggested IAM permissions, and credential verification steps
6. IF Crossplane managed resources fail to provision THEN the system SHALL display the resource status, conditions, and events with interpretation of common failure modes
7. WHEN network connectivity issues are detected THEN the system SHALL distinguish between local cluster issues and AWS connectivity problems
8. WHEN operations time out THEN the system SHALL provide timeout context and suggest increasing timeout values or checking underlying issues
9. WHEN doing something unexpected for a reason that might not be obvious THEN the system SHALL inform the user of the action and the reason

### Requirement 8: Resource Cleanup
**User Story:** As a platform engineer, I want to cleanly remove the bootstrap cluster when it's no longer needed, so that I don't leave behind orphaned resources or consume unnecessary local resources.

#### Acceptance Criteria
1. WHEN the user executes `mk8 bootstrap delete` THEN the system SHALL prompt for confirmation before deletion
2. WHEN deletion is confirmed THEN the system SHALL delete the kind cluster using kind's delete command
3. WHEN the kind cluster is deleted THEN the system SHALL verify all Docker containers associated with the cluster are removed
4. WHEN cleanup completes THEN the system SHALL remove the kubectl context for the bootstrap cluster from kubeconfig
5. IF the bootstrap cluster does not exist THEN the system SHALL inform the user and exit gracefully
6. IF cleanup encounters errors THEN the system SHALL log the errors but continue with remaining cleanup steps
7. WHEN cleanup completes THEN the system SHALL provide a summary of what was removed
8. WHEN the bootstrap cluster is deleted THEN the system SHALL inform the user that AWS credentials in the mk8 config file are preserved

### Requirement 9: Idempotent Operations
**User Story:** As a platform engineer, I want operations to be idempotent where possible, so that I can safely re-run commands without causing errors or inconsistent state.

#### Acceptance Criteria
1. WHEN `mk8 bootstrap create` is executed and the cluster already exists THEN the system SHALL detect this and either skip creation or offer to recreate
2. WHEN offering to recreate THEN the system SHALL prompt the user for confirmation before deleting the existing cluster
3. WHEN Crossplane is already installed THEN the system SHALL detect this and skip installation or offer to upgrade/reinstall
4. WHEN AWS credentials are already configured in Crossplane THEN the system SHALL detect this and skip or update the configuration
5. WHEN re-running status commands THEN the system SHALL always provide current, accurate information
6. WHEN operations are interrupted THEN the system SHALL be able to resume or cleanly restart on subsequent invocation

### Requirement 10: Progressive Status Display
**User Story:** As a platform engineer, I want to see progress updates during long-running operations, so that I know the system is working and not hung.

#### Acceptance Criteria
1. WHEN creating the bootstrap cluster THEN the system SHALL display progress messages for major steps (creating cluster, waiting for nodes, installing Crossplane, configuring credentials)
2. WHEN waiting for pods to be ready THEN the system SHALL display periodic status updates
3. WHEN operations take longer than expected THEN the system SHALL inform the user that the operation is still in progress
4. WHEN verbose mode is enabled THEN the system SHALL display detailed progress including pod events and resource states
5. WHEN operations complete THEN the system SHALL provide a clear success message with next steps

### Requirement 11: Management Cluster Provisioning Preparation
**User Story:** As a platform engineer, I want the bootstrap cluster fully configured to provision the AWS management cluster, so that I can proceed to the next phase of the architecture.

#### Acceptance Criteria
1. WHEN the bootstrap cluster creation completes successfully THEN the system SHALL confirm the cluster is ready to provision the management cluster
2. WHEN the bootstrap cluster is ready THEN the system SHALL provide instructions or commands for the next step (provisioning the management cluster)
3. WHEN AWS credentials are configured THEN the system SHALL verify they have appropriate IAM permissions for creating EKS clusters, VPCs, and related AWS resources
4. WHEN Crossplane is ready THEN the system SHALL verify it can reconcile AWS managed resources without errors
5. IF the bootstrap cluster is not ready for management cluster provisioning THEN the status command SHALL clearly indicate what is incomplete or misconfigured

### Requirement 12: Cluster Configuration Options
**User Story:** As a platform engineer, I want to customize the bootstrap cluster configuration if needed, so that I can adapt to different environments or requirements.

#### Acceptance Criteria
1. WHEN creating the bootstrap cluster THEN the system SHALL support optional flags for customization (e.g., Kubernetes version, Crossplane version)
2. IF no customization flags are provided THEN the system SHALL use sensible defaults
3. WHEN custom Kubernetes version is specified THEN the system SHALL validate it is supported by kind
4. WHEN custom Crossplane version is specified THEN the system SHALL validate it is compatible with the AWS provider
5. IF invalid options are provided THEN the system SHALL display an error with valid options
6. WHEN custom options are used THEN the system SHALL display what configuration is being applied

## Edge Cases and Constraints

### Edge Cases
- Bootstrap cluster creation interrupted mid-process (partial cluster state)
- Docker daemon stops while bootstrap cluster is running
- Network connectivity loss during Crossplane installation or AWS API calls
- Insufficient IAM permissions for specific AWS resources needed by management cluster
- Port conflicts when creating kind cluster (port already in use)
- Crossplane managed resources enter a degraded state that requires manual intervention
- kubectl context conflicts with existing clusters named similarly
- Insufficient local system resources (memory, disk) to run kind cluster and Crossplane
- Multiple bootstrap cluster creation attempts creating naming conflicts
- User manually deletes kind cluster outside of mk8 tool, leaving stale state
- Crossplane installation succeeds but pods crash-loop due to resource constraints
- AWS provider installation fails due to image pull errors or registry issues
- ProviderConfig creation succeeds but Crossplane cannot authenticate to AWS
- User attempts to create bootstrap cluster while one already exists
- AWS credentials change externally after bootstrap cluster is created

### Constraints
- The bootstrap cluster uses kind exclusively (no support for other local cluster providers)
- The bootstrap cluster is temporary and should be destroyed after management cluster provisioning
- AWS credentials must have sufficient IAM permissions to create EKS clusters, VPCs, IAM roles, and related resources
- Docker must be installed and running on the local machine
- The bootstrap cluster is not intended for running application workloads
- kubectl, kind, and Docker are external dependencies that must be pre-installed
- The system requires internet connectivity to pull container images and access AWS APIs
- The bootstrap cluster runs on the local machine only (not designed for remote cluster bootstrapping)
- Crossplane version compatibility with AWS provider must be maintained
- The cluster name "mk8-bootstrap" is reserved for the bootstrap cluster
- Only one bootstrap cluster can exist at a time per user
- The bootstrap cluster should be deleted after the management cluster is provisioned
- Crossplane installation uses default resource limits suitable for a local cluster
