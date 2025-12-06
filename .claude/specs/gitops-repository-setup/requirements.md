# Requirements Document

## Introduction

The gitops-repository-setup feature creates and configures a Git repository with the proper structure for managing Kubernetes infrastructure using GitOps principles. This repository will contain Crossplane manifests, Kubernetes configurations, and other infrastructure-as-code definitions that ArgoCD will use to provision and manage the AWS management cluster.

GitOps is a methodology where Git serves as the single source of truth for infrastructure and application definitions. Changes to infrastructure are made through Git commits, and automated systems (like ArgoCD) continuously reconcile the actual state with the desired state defined in Git.

This feature supports two workflows: creating a new Git repository with the proper structure, or configuring an existing repository by adding the necessary directories and files.

## Glossary

- **GitOps**: A methodology where Git is the single source of truth for declarative infrastructure and applications
- **Infrastructure Repository**: A Git repository containing Kubernetes manifests and infrastructure definitions
- **Crossplane Manifest**: A YAML file defining cloud infrastructure resources using Crossplane custom resources
- **Kustomize**: A Kubernetes configuration management tool that uses overlays and patches
- **Base Configuration**: Common Kubernetes manifests shared across environments
- **Overlay**: Environment-specific customizations applied to base configurations
- **Management Cluster**: The AWS EKS cluster that will be provisioned using GitOps

## Requirements

### Requirement 1: Repository Creation Options

**User Story:** As a platform engineer, I want to choose between creating a new repository or using an existing one, so that I can integrate with my team's existing Git workflow.

#### Acceptance Criteria

1. WHEN the user initiates GitOps setup THEN the system SHALL prompt for repository creation preference
2. WHEN the user chooses to create a new repository THEN the system SHALL prompt for repository name and location
3. WHEN the user chooses to use an existing repository THEN the system SHALL prompt for the repository path
4. IF an existing repository path is provided THEN the system SHALL verify the path exists and is a valid Git repository
5. IF the path is not a Git repository THEN the system SHALL display an error with suggestions to initialize Git first

### Requirement 2: New Repository Initialization

**User Story:** As a platform engineer, I want a new Git repository automatically initialized with proper structure, so that I can immediately start defining infrastructure.

#### Acceptance Criteria

1. WHEN creating a new repository THEN the system SHALL initialize a Git repository at the specified location
2. WHEN initializing the repository THEN the system SHALL create an initial commit with a README file
3. WHEN the repository is created THEN the system SHALL configure Git user name and email if not already set
4. WHEN repository creation completes THEN the system SHALL display the repository path and next steps
5. IF repository creation fails THEN the system SHALL display clear error messages with suggestions

### Requirement 3: Directory Structure Creation

**User Story:** As a platform engineer, I want a standardized directory structure for GitOps, so that ArgoCD can easily discover and apply configurations.

#### Acceptance Criteria

1. WHEN setting up GitOps structure THEN the system SHALL create a base directory for common configurations
2. WHEN creating directories THEN the system SHALL create an overlays directory for environment-specific configurations
3. WHEN creating directories THEN the system SHALL create a bootstrap directory for initial cluster setup
4. WHEN creating directories THEN the system SHALL create a management-cluster directory for management cluster definitions
5. WHEN directory structure is created THEN the system SHALL create a README in each directory explaining its purpose

### Requirement 4: Crossplane Manifest Templates

**User Story:** As a platform engineer, I want template Crossplane manifests for the management cluster, so that I have a starting point for infrastructure definitions.

#### Acceptance Criteria

1. WHEN setting up GitOps structure THEN the system SHALL create template Crossplane manifests for EKS cluster creation
2. WHEN creating templates THEN the system SHALL include manifests for VPC and networking resources
3. WHEN creating templates THEN the system SHALL include manifests for IAM roles and policies
4. WHEN creating templates THEN the system SHALL include placeholder values that need to be customized
5. WHEN templates are created THEN the system SHALL include comments explaining each resource and required customizations

### Requirement 5: Kustomize Configuration

**User Story:** As a platform engineer, I want Kustomize configurations set up, so that I can manage environment-specific variations.

#### Acceptance Criteria

1. WHEN setting up GitOps structure THEN the system SHALL create a kustomization.yaml file in the base directory
2. WHEN creating kustomization files THEN the system SHALL list all base manifests as resources
3. WHEN creating overlays THEN the system SHALL create kustomization.yaml files for each environment
4. WHEN creating overlay kustomizations THEN the system SHALL reference the base directory
5. WHEN Kustomize configuration is complete THEN the system SHALL validate the kustomization files are syntactically correct

### Requirement 6: ArgoCD Application Manifests

**User Story:** As a platform engineer, I want ArgoCD Application manifests pre-configured, so that ArgoCD knows what to deploy.

#### Acceptance Criteria

1. WHEN setting up GitOps structure THEN the system SHALL create an ArgoCD Application manifest for the management cluster
2. WHEN creating Application manifests THEN the system SHALL configure the source repository path
3. WHEN creating Application manifests THEN the system SHALL configure the destination cluster and namespace
4. WHEN creating Application manifests THEN the system SHALL configure sync policies including auto-sync settings
5. WHEN Application manifests are created THEN the system SHALL include comments explaining configuration options

### Requirement 7: Repository Configuration File

**User Story:** As a platform engineer, I want a configuration file that stores repository settings, so that mk8 can reference the repository in future operations.

#### Acceptance Criteria

1. WHEN GitOps setup completes THEN the system SHALL create a configuration file in the mk8 config directory
2. WHEN creating the configuration THEN the system SHALL store the repository path
3. WHEN creating the configuration THEN the system SHALL store the repository type (local or remote)
4. IF a remote repository URL is provided THEN the system SHALL store the URL and authentication method
5. WHEN configuration is saved THEN the system SHALL set appropriate file permissions

### Requirement 8: Git Remote Configuration

**User Story:** As a platform engineer, I want to optionally configure a Git remote, so that I can push changes to a hosted Git service.

#### Acceptance Criteria

1. WHEN setting up a new repository THEN the system SHALL prompt whether to configure a Git remote
2. WHEN the user chooses to configure a remote THEN the system SHALL prompt for the remote URL
3. WHEN a remote URL is provided THEN the system SHALL add the remote to the Git repository
4. WHEN adding a remote THEN the system SHALL verify the remote is accessible
5. IF remote configuration fails THEN the system SHALL display error messages with authentication suggestions

### Requirement 9: Initial Commit and Push

**User Story:** As a platform engineer, I want the initial GitOps structure automatically committed, so that I have a clean starting point.

#### Acceptance Criteria

1. WHEN GitOps structure is created THEN the system SHALL stage all created files for commit
2. WHEN files are staged THEN the system SHALL create a commit with a descriptive message
3. IF a Git remote is configured THEN the system SHALL prompt whether to push the initial commit
4. WHEN the user confirms push THEN the system SHALL push the commit to the remote repository
5. IF push fails THEN the system SHALL display error messages with authentication and permission suggestions

### Requirement 10: Existing Repository Integration

**User Story:** As a platform engineer, I want to add GitOps structure to an existing repository without disrupting existing content, so that I can integrate with current projects.

#### Acceptance Criteria

1. WHEN using an existing repository THEN the system SHALL check for conflicts with existing directories
2. IF conflicts exist THEN the system SHALL prompt the user for resolution options
3. WHEN adding to an existing repository THEN the system SHALL preserve all existing files and directories
4. WHEN changes are made THEN the system SHALL create a new Git branch for the GitOps structure
5. WHEN branch creation completes THEN the system SHALL inform the user to review and merge the branch

### Requirement 11: Validation and Verification

**User Story:** As a platform engineer, I want the GitOps repository structure validated, so that I know it's correctly configured before using it with ArgoCD.

#### Acceptance Criteria

1. WHEN GitOps setup completes THEN the system SHALL validate all required directories exist
2. WHEN validating THEN the system SHALL verify all kustomization.yaml files are syntactically correct
3. WHEN validating THEN the system SHALL verify all Crossplane manifests are valid YAML
4. WHEN validating THEN the system SHALL verify ArgoCD Application manifests are properly formatted
5. IF validation fails THEN the system SHALL display specific errors with file paths and line numbers

### Requirement 12: Documentation Generation

**User Story:** As a platform engineer, I want comprehensive documentation generated in the repository, so that team members understand the structure and how to use it.

#### Acceptance Criteria

1. WHEN GitOps structure is created THEN the system SHALL generate a main README.md file
2. WHEN creating documentation THEN the system SHALL include an overview of the directory structure
3. WHEN creating documentation THEN the system SHALL include instructions for customizing templates
4. WHEN creating documentation THEN the system SHALL include instructions for adding new resources
5. WHEN creating documentation THEN the system SHALL include links to relevant Crossplane and ArgoCD documentation

### Requirement 13: Status and Information Display

**User Story:** As a platform engineer, I want to view information about the configured GitOps repository, so that I can verify settings and troubleshoot issues.

#### Acceptance Criteria

1. WHEN checking GitOps status THEN the system SHALL display the repository path
2. WHEN displaying status THEN the system SHALL show whether the repository is local or remote
3. IF a remote is configured THEN the system SHALL display the remote URL
4. WHEN displaying status THEN the system SHALL show the last commit information
5. WHEN displaying status THEN the system SHALL verify the repository structure is intact

### Requirement 14: Error Detection and Diagnosis

**User Story:** As a platform engineer, I want detailed error messages when GitOps setup fails, so that I can quickly resolve issues.

#### Acceptance Criteria

1. WHEN any operation fails THEN the system SHALL display a clear, human-readable error message
2. WHEN displaying errors THEN the system SHALL include specific suggestions for resolving the issue
3. IF Git operations fail THEN the system SHALL include Git error messages and common resolution steps
4. IF file system operations fail THEN the system SHALL include permission and path validation suggestions
5. IF validation fails THEN the system SHALL display which files or configurations are invalid

## Edge Cases and Constraints

### Edge Cases
- User provides a path that exists but is not a Git repository
- Existing repository already contains directories with conflicting names
- Git user name and email not configured globally
- Remote repository requires authentication but credentials are not configured
- Network connectivity issues when accessing remote repository
- Insufficient file system permissions to create directories or files
- Repository path contains special characters or spaces
- Git operations interrupted mid-process leaving partial state
- Remote repository URL is invalid or inaccessible
- Kustomize or YAML syntax errors in generated files

### Constraints
- Git must be installed and accessible in the system PATH
- User must have write permissions to the target directory
- Repository structure follows a specific convention required by ArgoCD
- Crossplane manifests must be valid Kubernetes YAML
- Kustomize version compatibility must be maintained
- Remote repository access requires appropriate authentication
- The system does not manage Git credentials (relies on user's Git configuration)
- Only one GitOps repository can be configured per mk8 installation
- Repository structure is optimized for ArgoCD but may work with other GitOps tools
