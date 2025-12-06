# Requirements Document

## Introduction

The kubeconfig-file-handling specification defines how mk8 manages the kubectl configuration file (`~/.kube/config`). This is critical for ensuring that mk8 operations do not disrupt a user's existing Kubernetes cluster access while properly integrating new clusters created by mk8.

kubectl uses the kubeconfig file to store cluster connection information, authentication credentials, and context settings. When mk8 creates or removes clusters, it must carefully merge or remove configuration entries without affecting other clusters the user may be managing. This specification ensures that mk8 is a good citizen in a multi-cluster environment.

## Requirements

### Requirement 1: Respect Existing Configuration
**User Story:** As a platform engineer, I want mk8 to respect my existing kubectl configuration, so that I don't lose access to other clusters when using mk8.

#### Acceptance Criteria
1. WHEN mk8 needs to modify the kubeconfig file THEN the system SHALL first check if `~/.kube/config` exists
2. WHEN the kubeconfig file exists THEN the system SHALL read and parse it before making any modifications
3. WHEN reading the kubeconfig file THEN the system SHALL validate that it contains valid YAML
4. IF the kubeconfig file is corrupted or invalid THEN the system SHALL display an error and refuse to modify it
5. WHEN the kubeconfig file is valid THEN the system SHALL preserve all existing entries that are not related to mk8-managed clusters

### Requirement 2: Merge Cluster Configuration
**User Story:** As a platform engineer, I want mk8 to properly merge new cluster configuration into my existing kubeconfig, so that all my clusters remain accessible.

#### Acceptance Criteria
1. WHEN a new cluster is created THEN the system SHALL merge the new cluster's configuration into `~/.kube/config`
2. WHEN merging configurations THEN the system SHALL preserve all existing cluster entries
3. WHEN merging configurations THEN the system SHALL preserve all existing context entries
4. WHEN merging configurations THEN the system SHALL preserve all existing user entries
5. WHEN merging configurations THEN the system SHALL ensure the resulting file remains valid YAML
6. IF a merge conflict occurs (duplicate names) THEN the system SHALL automatically rename the new cluster with a numeric suffix

### Requirement 3: Create Configuration if Missing
**User Story:** As a platform engineer new to kubectl, I want mk8 to create a kubeconfig file if one doesn't exist, so that I don't need to manually set up the file structure.

#### Acceptance Criteria
1. IF the `~/.kube/config` file does not exist THEN the system SHALL create it with the new cluster configuration
2. WHEN creating the kubeconfig file THEN the system SHALL ensure the `~/.kube` directory exists with mode 0o700
3. WHEN creating the kubeconfig file THEN the system SHALL set file permissions to mode 0o600
4. WHEN creating a new kubeconfig file THEN the system SHALL use the standard kubeconfig structure with clusters, contexts, and users sections

### Requirement 4: Set Current Context
**User Story:** As a platform engineer, I want mk8 to set the kubectl context to the newly created cluster, so that I can immediately start using it without manual context switching.

#### Acceptance Criteria
1. WHEN a new cluster is created THEN the system SHALL set the current-context in kubeconfig to the new cluster
2. WHEN setting the current context THEN the system SHALL store the previous context value for potential restoration later

### Requirement 5: Remove Cluster Configuration
**User Story:** As a platform engineer, I want mk8 to cleanly remove cluster entries when I delete a cluster, so that my kubeconfig stays clean and up-to-date.

#### Acceptance Criteria
1. WHEN a cluster is deleted THEN the system SHALL remove the cluster entry from the kubeconfig file
2. WHEN a cluster is deleted THEN the system SHALL remove the associated context entry from the kubeconfig file
3. WHEN a cluster is deleted THEN the system SHALL remove the associated user entry from the kubeconfig file
4. WHEN removing entries THEN the system SHALL preserve all other clusters, contexts, and users
5. WHEN the removed cluster was the current context THEN the system SHALL attempt to switch to a different valid context

### Requirement 6: Restore Previous Context
**User Story:** As a platform engineer, I want mk8 to restore my previous kubectl context when I delete a cluster, so that I'm returned to my previous working environment.

#### Acceptance Criteria
1. WHEN removing a cluster that was the current context THEN the system SHALL restore the previous context if it still exists
2. IF the previous context no longer exists THEN the system SHALL select another valid context or clear the current-context field

### Requirement 7: Atomic File Updates
**User Story:** As a platform engineer, I want kubeconfig file updates to be atomic, so that I never end up with a corrupted configuration if an operation is interrupted.

#### Acceptance Criteria
1. WHEN modifying the kubeconfig file THEN the system SHALL write to a temporary file first
2. WHEN the temporary file is written successfully THEN the system SHALL validate it contains valid YAML
3. WHEN the temporary file is validated THEN the system SHALL atomically replace the original file
4. IF the write or validation fails THEN the system SHALL keep the original file unchanged
5. WHEN the operation completes THEN the system SHALL remove any temporary files

### Requirement 8: Backup and Recovery
**User Story:** As a platform engineer, I want mk8 to create backups before modifying kubeconfig, so that I can recover if something goes wrong.

#### Acceptance Criteria
1. WHEN modifying an existing kubeconfig file THEN the system SHALL create a backup copy first
2. WHEN creating a backup THEN the system SHALL use a timestamped filename (e.g., `config.backup.2024-12-06T12:34:56`)
3. WHEN multiple backups exist THEN the system SHALL clean up old backups keeping only the last 5

### Requirement 9: Error Reporting
**User Story:** As a platform engineer, I want clear error messages when kubeconfig operations fail, so that I can understand and fix the problem.

#### Acceptance Criteria
1. WHEN kubeconfig operations fail THEN the system SHALL display a clear error message describing what went wrong
2. WHEN displaying errors THEN the system SHALL include one or more specific suggestions for resolving the issue

## Edge Cases and Constraints

### Edge Cases
- Kubeconfig file is corrupted or contains invalid YAML
- Kubeconfig file has incorrect permissions
- Disk is full when trying to write kubeconfig updates
- User manually deletes clusters outside of mk8, leaving stale kubeconfig entries
- Kubeconfig contains clusters with names that conflict with mk8 naming conventions
- User has set KUBECONFIG environment variable to a different location
- ~/.kube directory doesn't exist and can't be created (permissions issue)

### Constraints
- The tool assumes kubeconfig location is `~/.kube/config` unless KUBECONFIG environment variable is set
- The tool must handle standard kubeconfig format as defined by Kubernetes
- File operations must be atomic to prevent corruption
- The tool should respect the KUBECONFIG environment variable if set
- Backups should not accumulate indefinitely
- All kubeconfig modifications must preserve the ability to access other clusters
- The tool must work with kubeconfig files created by various tools (kubectl, kind, minikube, etc.)
