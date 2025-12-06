# Requirements Document

## Introduction

The argocd-bootstrap feature installs and configures ArgoCD on the local bootstrap cluster, enabling GitOps-based management of the AWS management cluster. ArgoCD is a declarative, GitOps continuous delivery tool for Kubernetes that automatically synchronizes cluster state with configurations stored in Git.

Once ArgoCD is installed and configured, it will monitor the GitOps repository and automatically apply Crossplane manifests to provision the management cluster on AWS. This creates a fully automated, auditable infrastructure provisioning workflow where all changes are tracked in Git.

This feature handles the complete ArgoCD setup: installation, initial configuration, connection to the GitOps repository, and creation of ArgoCD Applications that manage the management cluster provisioning process.

## Glossary

- **ArgoCD**: A declarative GitOps continuous delivery tool for Kubernetes
- **ArgoCD Application**: A custom resource that defines what to deploy, where to deploy it, and how to sync it
- **Sync**: The process of applying Git repository contents to a Kubernetes cluster
- **Auto-Sync**: Automatic synchronization when Git repository changes are detected
- **Self-Heal**: Automatic correction when cluster state drifts from Git-defined state
- **Repository Credentials**: Authentication information for accessing private Git repositories
- **Application Project**: A logical grouping of ArgoCD Applications with shared policies
- **Bootstrap Cluster**: The local kind cluster where ArgoCD is installed

## Requirements

### Requirement 1: ArgoCD Installation

**User Story:** As a platform engineer, I want ArgoCD automatically installed on the bootstrap cluster, so that I can manage infrastructure through GitOps.

#### Acceptance Criteria

1. WHEN the bootstrap cluster is ready THEN the system SHALL install ArgoCD using kubectl manifests or Helm
2. WHEN installing ArgoCD THEN the system SHALL use a specific, tested version of ArgoCD
3. WHEN ArgoCD is installing THEN the system SHALL monitor the deployment status and wait for all ArgoCD pods to be ready
4. IF ArgoCD installation fails THEN the system SHALL display clear error messages including pod status and events
5. WHEN ArgoCD installation times out THEN the system SHALL provide diagnostic information and suggestions
6. WHEN ArgoCD is ready THEN the system SHALL verify the ArgoCD API server is responding

### Requirement 2: ArgoCD Version Management

**User Story:** As a platform engineer, I want to specify which version of ArgoCD to install, so that I can use tested versions or upgrade when needed.

#### Acceptance Criteria

1. WHEN installing ArgoCD THEN the system SHALL support a configurable version via CLI option or configuration file
2. IF no version is specified THEN the system SHALL use a tested default version
3. WHEN a specific version is requested THEN the system SHALL validate the version exists and is compatible
4. IF an invalid version is specified THEN the system SHALL display an error with available versions
5. WHEN ArgoCD is already installed THEN the system SHALL detect this and offer to skip, upgrade, or reinstall

### Requirement 3: ArgoCD Initial Configuration

**User Story:** As a platform engineer, I want ArgoCD configured with sensible defaults, so that it's ready to manage infrastructure immediately.

#### Acceptance Criteria

1. WHEN ArgoCD is installed THEN the system SHALL configure ArgoCD with appropriate resource limits for a local cluster
2. WHEN configuring ArgoCD THEN the system SHALL enable necessary features for Crossplane resource management
3. WHEN configuring ArgoCD THEN the system SHALL set appropriate sync timeouts for infrastructure provisioning
4. WHEN configuration is applied THEN the system SHALL verify ArgoCD accepts the configuration
5. IF configuration fails THEN the system SHALL display validation errors with suggestions

### Requirement 4: ArgoCD CLI Installation

**User Story:** As a platform engineer, I want the ArgoCD CLI automatically available, so that I can interact with ArgoCD from the command line.

#### Acceptance Criteria

1. WHEN ArgoCD is installed THEN the system SHALL check if the ArgoCD CLI is available
2. IF the ArgoCD CLI is not installed THEN the system SHALL provide installation instructions
3. WHEN the ArgoCD CLI is available THEN the system SHALL configure it to connect to the bootstrap cluster
4. WHEN CLI configuration completes THEN the system SHALL verify the CLI can communicate with ArgoCD
5. IF CLI configuration fails THEN the system SHALL display connection errors with troubleshooting steps

### Requirement 5: ArgoCD Admin Password Retrieval

**User Story:** As a platform engineer, I want the ArgoCD admin password automatically retrieved and displayed, so that I can access the ArgoCD UI.

#### Acceptance Criteria

1. WHEN ArgoCD installation completes THEN the system SHALL retrieve the initial admin password
2. WHEN retrieving the password THEN the system SHALL decode it from the Kubernetes secret
3. WHEN the password is retrieved THEN the system SHALL display it to the user with instructions to change it
4. WHEN displaying the password THEN the system SHALL provide the ArgoCD UI URL
5. WHEN password retrieval fails THEN the system SHALL provide instructions for manual retrieval

### Requirement 6: GitOps Repository Connection

**User Story:** As a platform engineer, I want ArgoCD automatically connected to my GitOps repository, so that it can sync infrastructure definitions.

#### Acceptance Criteria

1. WHEN ArgoCD is ready THEN the system SHALL retrieve the GitOps repository configuration from mk8 config
2. IF GitOps repository is not configured THEN the system SHALL halt and instruct the user to set up GitOps first
3. WHEN repository configuration is available THEN the system SHALL register the repository with ArgoCD
4. IF the repository is private THEN the system SHALL prompt for authentication credentials
5. WHEN repository is registered THEN the system SHALL verify ArgoCD can access the repository
6. IF repository connection fails THEN the system SHALL display authentication and network troubleshooting steps

### Requirement 7: Repository Credentials Management

**User Story:** As a platform engineer, I want to securely provide Git credentials to ArgoCD, so that it can access private repositories.

#### Acceptance Criteria

1. WHEN connecting to a private repository THEN the system SHALL prompt for credential type (SSH key, HTTPS token, username/password)
2. WHEN SSH key authentication is chosen THEN the system SHALL prompt for the private key path
3. WHEN HTTPS token authentication is chosen THEN the system SHALL prompt for the token
4. WHEN credentials are provided THEN the system SHALL create an ArgoCD repository secret
5. WHEN the secret is created THEN the system SHALL verify ArgoCD can authenticate to the repository
6. IF authentication fails THEN the system SHALL display error messages with credential verification steps

### Requirement 8: Management Cluster Application Creation

**User Story:** As a platform engineer, I want an ArgoCD Application automatically created for the management cluster, so that ArgoCD begins provisioning infrastructure.

#### Acceptance Criteria

1. WHEN the repository is connected THEN the system SHALL create an ArgoCD Application for the management cluster
2. WHEN creating the Application THEN the system SHALL configure the source repository path to the management cluster manifests
3. WHEN creating the Application THEN the system SHALL configure the destination to the bootstrap cluster
4. WHEN creating the Application THEN the system SHALL enable auto-sync for continuous deployment
5. WHEN creating the Application THEN the system SHALL enable self-heal to automatically correct drift
6. WHEN the Application is created THEN the system SHALL verify ArgoCD accepts the Application definition

### Requirement 9: Application Sync Policy Configuration

**User Story:** As a platform engineer, I want appropriate sync policies configured, so that infrastructure changes are applied safely and automatically.

#### Acceptance Criteria

1. WHEN configuring sync policies THEN the system SHALL enable automated sync for the management cluster Application
2. WHEN configuring sync policies THEN the system SHALL enable automated pruning of deleted resources
3. WHEN configuring sync policies THEN the system SHALL enable self-healing to correct manual changes
4. WHEN configuring sync policies THEN the system SHALL set appropriate sync timeouts for infrastructure resources
5. WHEN sync policies are configured THEN the system SHALL verify the policies are applied correctly

### Requirement 10: Initial Sync Trigger

**User Story:** As a platform engineer, I want ArgoCD to immediately begin syncing the management cluster, so that infrastructure provisioning starts automatically.

#### Acceptance Criteria

1. WHEN the Application is created THEN the system SHALL trigger an initial sync
2. WHEN sync is triggered THEN the system SHALL monitor the sync status
3. WHEN sync is in progress THEN the system SHALL display progress updates
4. IF sync fails THEN the system SHALL display sync errors with resource-specific details
5. WHEN sync completes THEN the system SHALL display the sync result and resource status

### Requirement 11: ArgoCD Status Reporting

**User Story:** As a platform engineer, I want to check ArgoCD status at any time, so that I can verify it's functioning correctly and monitor sync progress.

#### Acceptance Criteria

1. WHEN checking ArgoCD status THEN the system SHALL display the installed ArgoCD version
2. WHEN ArgoCD is installed THEN the system SHALL display pod status for all ArgoCD components
3. WHEN displaying status THEN the system SHALL show connected repositories
4. WHEN displaying status THEN the system SHALL show all ArgoCD Applications and their sync status
5. WHEN displaying Application status THEN the system SHALL show health status of managed resources
6. IF any component is unhealthy THEN the system SHALL highlight the issue and suggest remediation steps

### Requirement 12: ArgoCD UI Access

**User Story:** As a platform engineer, I want easy access to the ArgoCD UI, so that I can visually monitor infrastructure provisioning.

#### Acceptance Criteria

1. WHEN ArgoCD is installed THEN the system SHALL provide the ArgoCD UI URL
2. WHEN providing the UI URL THEN the system SHALL include instructions for port-forwarding if needed
3. WHEN the user requests UI access THEN the system SHALL optionally set up port-forwarding automatically
4. WHEN port-forwarding is active THEN the system SHALL display the local URL to access the UI
5. WHEN providing UI access THEN the system SHALL display the admin username and password

### Requirement 13: Application Health Monitoring

**User Story:** As a platform engineer, I want to monitor the health of resources managed by ArgoCD, so that I can detect and resolve issues quickly.

#### Acceptance Criteria

1. WHEN checking Application health THEN the system SHALL display the health status of all managed resources
2. WHEN resources are unhealthy THEN the system SHALL display resource-specific error messages
3. WHEN Crossplane resources are provisioning THEN the system SHALL display provisioning progress
4. IF Crossplane resources fail THEN the system SHALL display Crossplane status conditions and events
5. WHEN health check completes THEN the system SHALL provide a summary of overall Application health

### Requirement 14: Sync Retry and Recovery

**User Story:** As a platform engineer, I want ArgoCD to automatically retry failed syncs, so that transient errors don't block infrastructure provisioning.

#### Acceptance Criteria

1. WHEN a sync fails THEN the system SHALL configure ArgoCD to automatically retry
2. WHEN configuring retries THEN the system SHALL set appropriate retry intervals
3. WHEN configuring retries THEN the system SHALL set a maximum retry limit
4. IF retries are exhausted THEN the system SHALL alert the user with detailed error information
5. WHEN sync eventually succeeds THEN the system SHALL confirm successful recovery

### Requirement 15: Error Detection and Diagnosis

**User Story:** As a platform engineer, I want detailed error messages when ArgoCD setup or sync fails, so that I can quickly resolve issues.

#### Acceptance Criteria

1. WHEN any operation fails THEN the system SHALL display a clear, human-readable error message
2. WHEN displaying errors THEN the system SHALL include specific suggestions for resolving the issue
3. IF ArgoCD installation fails THEN the system SHALL include pod logs, events, and image pull status
4. IF repository connection fails THEN the system SHALL include authentication and network diagnostics
5. IF Application sync fails THEN the system SHALL display resource-level errors with Crossplane conditions
6. WHEN Crossplane resources fail THEN the system SHALL interpret common AWS provisioning errors
7. WHEN operations time out THEN the system SHALL provide timeout context and suggest checking underlying issues

### Requirement 16: Progressive Status Display

**User Story:** As a platform engineer, I want to see progress updates during ArgoCD installation and sync operations, so that I know the system is working.

#### Acceptance Criteria

1. WHEN installing ArgoCD THEN the system SHALL display progress messages for major steps
2. WHEN waiting for pods to be ready THEN the system SHALL display periodic status updates
3. WHEN sync is in progress THEN the system SHALL display which resources are being created or updated
4. WHEN operations take longer than expected THEN the system SHALL inform the user that the operation is still in progress
5. WHEN verbose mode is enabled THEN the system SHALL display detailed progress including pod events and resource states

### Requirement 17: Idempotent Operations

**User Story:** As a platform engineer, I want ArgoCD setup operations to be idempotent, so that I can safely re-run commands without causing errors.

#### Acceptance Criteria

1. WHEN ArgoCD is already installed THEN the system SHALL detect this and skip installation or offer to upgrade
2. WHEN repository is already connected THEN the system SHALL detect this and skip or update the connection
3. WHEN Application already exists THEN the system SHALL detect this and skip or update the Application
4. WHEN operations are interrupted THEN the system SHALL be able to resume or cleanly restart on subsequent invocation
5. WHEN re-running status commands THEN the system SHALL always provide current, accurate information

### Requirement 18: Cleanup Support

**User Story:** As a platform engineer, I want to cleanly remove ArgoCD when deleting the bootstrap cluster, so that no orphaned resources remain.

#### Acceptance Criteria

1. WHEN the bootstrap cluster is deleted THEN the system SHALL remove all ArgoCD resources
2. WHEN ArgoCD is removed THEN the system SHALL verify all ArgoCD pods are terminated
3. WHEN cleanup completes THEN the system SHALL confirm all ArgoCD components are removed
4. IF cleanup encounters errors THEN the system SHALL log the errors but continue with remaining cleanup steps
5. WHEN ArgoCD is removed THEN the system SHALL inform the user that the GitOps repository is preserved

## Edge Cases and Constraints

### Edge Cases
- ArgoCD installation succeeds but pods crash-loop due to resource constraints
- Repository connection succeeds but ArgoCD cannot read repository contents
- Application sync starts but Crossplane resources fail to provision due to AWS errors
- Network connectivity loss during sync operations
- Git repository changes while sync is in progress
- Multiple Applications trying to manage the same resources
- ArgoCD UI port conflicts with other local services
- Repository credentials expire or are revoked during operation
- Crossplane resources enter a degraded state that ArgoCD cannot resolve
- Manual changes to cluster conflict with ArgoCD-managed state

### Constraints
- ArgoCD must be installed on an existing Kubernetes cluster (the bootstrap cluster)
- GitOps repository must be configured before ArgoCD setup
- The system requires internet connectivity to pull ArgoCD images and access Git repositories
- ArgoCD version compatibility with Kubernetes version must be maintained
- Repository must be accessible from the bootstrap cluster
- Only one ArgoCD instance should exist on the bootstrap cluster
- ArgoCD installation uses default resource limits suitable for a local cluster
- The bootstrap cluster must have sufficient resources to run ArgoCD components
- Crossplane must be installed before ArgoCD begins syncing infrastructure resources
- AWS credentials must be configured in Crossplane before management cluster provisioning
