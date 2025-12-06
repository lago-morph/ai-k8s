# Requirements Document

## Introduction

The aws-credentials-management specification defines how mk8 handles AWS credentials including acquisition, storage, validation, and synchronization with managed clusters. Proper credential management is critical for security and usability, allowing users to provision AWS infrastructure through Crossplane while maintaining clear control over credential lifecycle.

mk8 supports multiple methods for providing AWS credentials: dedicated MK8_* environment variables for automatic configuration, standard AWS_* environment variables with interactive prompting, and manual entry through the `mk8 config` command. Credentials are stored in a configuration file (`~/.config/mk8`) and must include all three required components: access key ID, secret access key, and default region.

The system ensures credentials are synchronized with Crossplane in managed clusters, enabling seamless AWS resource provisioning while providing clear user feedback when credentials are missing, incomplete, or invalid.

## Requirements

### Requirement 1: Configuration File Management
**User Story:** As a platform engineer, I want AWS credentials stored securely in a configuration file, so that I can manage credentials independently of environment variables and have them persist across sessions.

#### Acceptance Criteria
1. WHEN the system needs to access AWS credentials THEN the system SHALL first check for credentials in the configuration file at `~/.config/mk8`
2. WHEN checking the configuration file THEN the system SHALL look for three key-value pairs: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION`
3. IF all three credentials are present in the configuration file THEN the system SHALL use these credentials for AWS operations
4. IF only some credentials are present in the configuration file THEN the system SHALL inform the user that the configuration file is incomplete and will not be used
5. WHEN informing the user about incomplete configuration THEN the system SHALL explain which credentials are missing
6. WHEN the configuration file is created or updated THEN the system SHALL store credentials using the standard AWS environment variable names as keys
7. WHEN storing credentials in the configuration file THEN the system SHALL ensure the file has restrictive permissions (readable/writable only by the owner)
8. WHEN the configuration file is created THEN the system SHALL ensure the `~/.config` directory exists

### Requirement 2: MK8 Environment Variables
**User Story:** As a platform engineer, I want to use dedicated MK8_* environment variables for automatic credential configuration, so that I can avoid interactive prompts in automated environments.

#### Acceptance Criteria
1. WHEN a command requires AWS credentials and they are not in the configuration file THEN the system SHALL check for `MK8_AWS_ACCESS_KEY_ID`, `MK8_AWS_SECRET_ACCESS_KEY`, and `MK8_AWS_DEFAULT_REGION` environment variables
2. IF all three MK8_* environment variables are set THEN the system SHALL automatically copy them to the configuration file without prompting the user
3. WHEN MK8_* environment variables are used THEN the system SHALL inform the user that credentials were automatically configured from environment variables
4. IF only some MK8_* environment variables are set THEN the system SHALL not use them and SHALL proceed to check standard AWS environment variables
5. WHEN MK8_* variables take precedence THEN the system SHALL document this behavior clearly in help text

### Requirement 3: Standard AWS Environment Variables with Prompting
**User Story:** As a platform engineer, I want to be prompted about using my existing AWS environment variables, so that I have explicit control over whether they're used by mk8.

#### Acceptance Criteria
1. IF MK8_* environment variables are not all set and AWS credentials are not in the configuration file THEN the system SHALL check for standard `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION` environment variables
2. IF all three standard AWS environment variables are set THEN the system SHALL prompt the user with three options: (1) use the existing environment variables, (2) be prompted for credentials and save them, or (3) exit
3. WHEN presenting the prompt THEN the system SHALL clearly explain what each option does
4. IF the user selects option 1 THEN the system SHALL copy the environment variables to the configuration file
5. IF the user selects option 2 THEN the system SHALL proceed to interactive credential entry
6. IF the user selects option 3 THEN the system SHALL exit without performing any operations
7. WHEN credentials are saved from environment variables THEN the system SHALL inform the user that they have been stored in the configuration file

### Requirement 4: Interactive Credential Entry
**User Story:** As a platform engineer, I want to interactively enter AWS credentials when they're not available, so that I can configure mk8 even without environment variables.

#### Acceptance Criteria
1. IF not all three standard AWS environment variables are set and credentials are needed THEN the system SHALL prompt the user to enter credentials interactively
2. WHEN prompting interactively THEN the system SHALL offer only options 2 (enter credentials) and 3 (exit), with an explanation that option 1 is disabled because all three environment variables are not set
3. WHEN prompting for the access key ID THEN the system SHALL display the prompt "AWS Access Key ID:" and echo the typed text
4. WHEN prompting for the secret access key THEN the system SHALL display the prompt "AWS Secret Access Key:" and echo asterisks (*) instead of the actual characters
5. WHEN prompting for the default region THEN the system SHALL display the prompt "AWS Default Region:" and echo the typed text
6. WHEN all three credentials are entered THEN the system SHALL save them to the configuration file
7. WHEN credentials are saved THEN the system SHALL inform the user that credentials have been stored
8. IF the user cancels during credential entry (Ctrl+C) THEN the system SHALL exit gracefully without saving partial credentials

### Requirement 5: mk8 config Command
**User Story:** As a platform engineer, I want to explicitly configure AWS credentials using a dedicated command, so that I can set or update credentials at any time.

#### Acceptance Criteria
1. WHEN the user executes `mk8 config` THEN the system SHALL initiate the AWS credentials configuration workflow
2. WHEN `mk8 config` is executed and all three MK8_* environment variables are set THEN the system SHALL automatically copy them to the configuration file without prompting
3. WHEN `mk8 config` is executed and MK8_* variables are used THEN the system SHALL inform the user that credentials were configured from MK8_* environment variables
4. WHEN `mk8 config` is executed without MK8_* variables THEN the system SHALL follow the standard AWS environment variable prompting workflow
5. WHEN `mk8 config` is executed THEN the system SHALL overwrite any existing configuration file regardless of prior contents
6. WHEN credentials are updated via `mk8 config` THEN the system SHALL inform the user that the configuration has been updated

### Requirement 6: Crossplane Credentials Synchronization
**User Story:** As a platform engineer, I want AWS credentials in Crossplane to stay synchronized with my mk8 configuration, so that Crossplane always uses the correct credentials for AWS operations.

#### Acceptance Criteria
1. WHEN a bootstrap cluster is created with Crossplane THEN the system SHALL create a Kubernetes secret containing the AWS credentials from the configuration file
2. WHEN creating the AWS credentials secret THEN the system SHALL include `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION`
3. WHEN the credentials secret is created THEN the system SHALL create a ProviderConfig resource that references the credentials secret
4. WHEN `mk8 config` is executed after a cluster with Crossplane has been created THEN the system SHALL detect the cluster and update the credentials in Crossplane
5. WHEN credentials are updated in Crossplane THEN the system SHALL update both the Kubernetes secret and verify the ProviderConfig references it correctly
6. WHEN credentials are updated in Crossplane THEN the system SHALL inform the user that Crossplane credentials have been synchronized
7. IF updating Crossplane credentials fails THEN the system SHALL display an error with suggestions for remediation

### Requirement 7: Credentials Validation
**User Story:** As a platform engineer, I want my AWS credentials validated before use, so that I can catch configuration errors early.

#### Acceptance Criteria
1. WHEN AWS credentials are configured in Crossplane THEN the system SHALL test the credentials by making a simple AWS API call (e.g., sts:GetCallerIdentity)
2. IF the AWS API test succeeds THEN the system SHALL display confirmation that credentials are valid and show the AWS account ID
3. IF the AWS API test fails THEN the system SHALL display the AWS error with suggestions for fixing IAM permissions or credential configuration
4. WHEN credentials validation fails THEN the system SHALL include the AWS error code and message in the output
5. WHEN credentials validation fails due to permissions THEN the system SHALL suggest checking IAM policies and permissions

### Requirement 8: Credential Security
**User Story:** As a platform engineer, I want my credentials stored securely, so that they are not exposed to unauthorized access.

#### Acceptance Criteria
1. WHEN the configuration file is created THEN the system SHALL set file permissions to 0600 (readable and writable only by the owner)
2. WHEN credentials are displayed in error messages or logs THEN the system SHALL mask the secret access key (show only first/last few characters)
3. WHEN credentials are in memory THEN the system SHOULD clear them promptly after use
4. IF the configuration file has incorrect permissions THEN the system SHALL warn the user and suggest correcting the permissions
5. WHEN storing credentials THEN the system SHALL not log the actual credential values

### Requirement 9: Credential Update Detection
**User Story:** As a platform engineer, I want to know when credentials have changed, so that I understand when Crossplane will use different AWS credentials.

#### Acceptance Criteria
1. WHEN `mk8 config` updates credentials THEN the system SHALL compare new credentials with existing ones
2. IF credentials have changed THEN the system SHALL inform the user that credentials have been updated
3. IF a Crossplane cluster exists and credentials changed THEN the system SHALL inform the user that Crossplane credentials will be updated
4. WHEN credentials are unchanged THEN the system SHALL inform the user that credentials are already up to date

### Requirement 10: Error Handling and User Guidance
**User Story:** As a platform engineer, I want clear guidance when credential operations fail, so that I can quickly fix configuration issues.

#### Acceptance Criteria
1. WHEN any credential operation fails THEN the system SHALL display a clear, human-readable error message describing what went wrong
2. WHEN displaying errors THEN the system SHALL include one or more specific suggestions for resolving the issue
3. IF the configuration file cannot be written THEN the system SHALL check and report permission issues
4. IF environment variables have unexpected values THEN the system SHALL explain what was expected
5. IF AWS API calls fail THEN the system SHALL include AWS error codes and suggested IAM permissions
6. WHEN doing something unexpected for a reason that might not be obvious THEN the system SHALL inform the user of the action and the reason

## Edge Cases and Constraints

### Edge Cases
- User interrupts credential prompting workflow (Ctrl+C during password entry)
- Configuration file (`~/.config/mk8`) is manually edited with invalid or incomplete credentials
- MK8_* and AWS_* environment variables are both set with conflicting values
- Configuration file permissions are incorrect (world-readable, exposing credentials)
- User pastes multi-line or malformed values when prompted for credentials
- AWS API rate limiting during credential validation
- AWS credentials expire or are revoked after initial configuration
- User has AWS credentials in ~/.aws/credentials but not in environment variables
- Region value is invalid or not recognized by AWS
- User enters empty strings when prompted for credentials
- Configuration file exists but is empty or contains only partial data
- ~/.config directory doesn't exist and cannot be created

### Constraints
- AWS credentials stored in `~/.config/mk8` are stored in plaintext (secured via file permissions)
- The tool assumes the user has permissions to create and modify files in their home directory
- MK8_* environment variables take precedence over AWS_* environment variables when both are set
- All three credentials (access key ID, secret access key, region) must be present to be considered valid
- The tool does not support AWS credential profiles or assume role workflows in the initial implementation
- Region specification is limited to AWS_DEFAULT_REGION (does not support per-service regions)
- The tool does not integrate with AWS SSO or temporary credentials in the initial implementation
- Credential validation requires internet connectivity to reach AWS APIs
- Secret access key input masking depends on terminal support for hidden input
