# AWS Credentials Management Design Document

## Overview

The AWS credentials management feature provides secure, user-friendly handling of AWS credentials for mk8. It supports multiple credential acquisition methods (environment variables, interactive prompts, explicit configuration), stores credentials securely in a local configuration file, and synchronizes them with Crossplane in managed Kubernetes clusters.

### Design Goals

1. **Security-first**: Secure storage with restrictive file permissions, credential masking in logs
2. **User-friendly**: Clear prompts, helpful error messages, multiple input methods
3. **Automation-ready**: Support for non-interactive configuration via MK8_* environment variables
4. **Crossplane integration**: Automatic credential synchronization with managed clusters
5. **Validation**: Early detection of invalid credentials through AWS API testing

### Key Features

- Configuration file storage at `~/.config/mk8` with 0600 permissions
- Dedicated MK8_* environment variables for automated configuration
- Interactive prompts with secure password entry for manual configuration
- `mk8 config` command for explicit credential management
- Automatic Crossplane secret and ProviderConfig synchronization
- AWS credential validation via STS GetCallerIdentity API
- Clear error messages with actionable suggestions

## Architecture

### Credential Update Decision Tree

This diagram shows when credentials are read, saved, or updated:

```mermaid
flowchart TD
    Start([Command Execution]) --> IsConfigCmd{mk8 config<br/>command?}
    
    IsConfigCmd -->|No| CheckFile{Config file<br/>complete?}
    IsConfigCmd -->|Yes| SkipFile[Skip file check]
    
    CheckFile -->|Yes| UseFile[✓ Use existing credentials]
    CheckFile -->|No| AcquireCreds[Acquire credentials]
    SkipFile --> AcquireCreds
    
    AcquireCreds --> CheckMK8{All 3 MK8_*<br/>vars set?}
    CheckMK8 -->|Yes| AutoSave[⚡ Auto-save to file]
    CheckMK8 -->|No| CheckAWS{All 3 AWS_*<br/>vars set?}
    
    CheckAWS -->|Yes| PromptUser[Prompt user:<br/>Use AWS_* / Enter / Exit]
    CheckAWS -->|No| PromptManual[Prompt user:<br/>Enter / Exit]
    
    PromptUser --> UserChoice{Choice?}
    UserChoice -->|Use AWS_*| SaveToFile[💾 Save to file]
    UserChoice -->|Enter| Interactive[Interactive entry]
    UserChoice -->|Exit| Exit[Exit]
    
    PromptManual --> ManualChoice{Choice?}
    ManualChoice -->|Enter| Interactive
    ManualChoice -->|Exit| Exit
    
    Interactive --> SaveToFile
    
    UseFile --> MaybeSyncA{Cluster<br/>exists?}
    AutoSave --> MaybeSyncB{Cluster<br/>exists?}
    SaveToFile --> MaybeSyncB
    
    MaybeSyncA -->|Yes| Sync[🔄 Sync to Crossplane<br/>+ Validate AWS]
    MaybeSyncA -->|No| Done([Done])
    MaybeSyncB -->|Yes| Sync
    MaybeSyncB -->|No| Done
    
    Sync --> Done
    Exit --> Done
    
    style UseFile fill:#90EE90
    style AutoSave fill:#FFD700
    style SaveToFile fill:#FFD700
    style Sync fill:#87CEEB
    style Exit fill:#FFB6C1
```

**Key Differences by Command**:

| Scenario | Regular Command | mk8 config |
|----------|----------------|------------|
| Config file complete | ✓ Use existing | ⚡ Overwrite |
| Config file incomplete | 💾 Acquire & save | 💾 Acquire & save |
| MK8_* vars set | ⚡ Auto-save | ⚡ Auto-save |
| AWS_* vars set | 💬 Prompt user | 💬 Prompt user |
| No vars set | 💬 Prompt manual entry | 💬 Prompt manual entry |

**Legend**:
- ✓ **Use**: Read from existing file (no update)
- 💾 **Save**: Write new credentials to file
- ⚡ **Auto-save**: Save without prompting
- 💬 **Prompt**: Ask user for input
- 🔄 **Sync**: Update Crossplane cluster

### Component Architecture

```mermaid
graph TB
    subgraph "CLI Layer"
        ConfigCmd[config command]
        BootstrapCmd[bootstrap command]
    end

    subgraph "Business Layer"
        CredMgr[CredentialManager]
        CrossplaneMgr[CrossplaneManager]
    end

    subgraph "Integration Layer"
        AWSClient[AWSClient]
        KubectlClient[KubectlClient]
        FileIO[FileIO]
    end

    subgraph "Core Layer"
        Errors[Error Handling]
        Output[Output Formatting]
    end

    ConfigCmd --> CredMgr
    BootstrapCmd --> CredMgr
    CredMgr --> FileIO
    CredMgr --> AWSClient
    CredMgr --> CrossplaneMgr
    CrossplaneMgr --> KubectlClient
    CredMgr --> Output
    CredMgr --> Errors
```

### Credential Acquisition Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant CredMgr as CredentialManager
    participant Sources as Config File /<br/>Env Vars

    User->>CLI: mk8 bootstrap / mk8 config
    CLI->>CredMgr: get_credentials()
    CredMgr->>Sources: Check in priority order:<br/>1. Config file<br/>2. MK8_* vars<br/>3. AWS_* vars
    
    alt Complete credentials found
        Sources-->>CredMgr: credentials
    else Need user input
        CredMgr->>User: Prompt for credentials
        User-->>CredMgr: credentials or exit
    end
    
    CredMgr->>CredMgr: save_credentials()
    CredMgr-->>CLI: credentials
```

### Crossplane Synchronization Flow

```mermaid
sequenceDiagram
    participant CLI
    participant CrossplaneMgr as CrossplaneManager
    participant K8s as Kubernetes
    participant AWS as AWS STS API

    CLI->>CrossplaneMgr: sync_credentials()
    CrossplaneMgr->>K8s: Check cluster exists
    
    alt Cluster exists
        CrossplaneMgr->>K8s: Update secret
        CrossplaneMgr->>K8s: Verify ProviderConfig
        CrossplaneMgr->>AWS: GetCallerIdentity
        AWS-->>CrossplaneMgr: account_id or error
        CrossplaneMgr-->>CLI: result + feedback
    else No cluster
        CrossplaneMgr-->>CLI: Skip sync
    end
```

## Components and Interfaces

### 1. CredentialManager

**Purpose**: Orchestrate credential acquisition, storage, and validation.

**Location**: `mk8/business/credential_manager.py`

**Interface**:
```python
class CredentialManager:
    """Manages AWS credential acquisition, storage, and validation."""

    def __init__(
        self,
        file_io: FileIO,
        aws_client: AWSClient,
        output: OutputFormatter
    ):
        """Initialize credential manager with dependencies."""

    def get_credentials(self) -> AWSCredentials:
        """
        Get AWS credentials using priority order.
        
        Priority:
        1. Config file (~/.config/mk8)
        2. MK8_* environment variables (auto-save)
        3. AWS_* environment variables (prompt user)
        4. Interactive entry (prompt user)
        
        Returns:
            AWSCredentials object
            
        Raises:
            ConfigurationError: If credentials cannot be acquired
        """

    def update_credentials(self, force: bool = False) -> AWSCredentials:
        """
        Update credentials via mk8 config command.
        
        Args:
            force: If True, always prompt even if config exists
            
        Returns:
            Updated AWSCredentials
        """

    def validate_credentials(self, credentials: AWSCredentials) -> ValidationResult:
        """
        Validate credentials by calling AWS STS GetCallerIdentity.
        
        Args:
            credentials: Credentials to validate
            
        Returns:
            ValidationResult with success status and account_id or error
        """

    def _read_from_config_file(self) -> Optional[AWSCredentials]:
        """Read credentials from ~/.config/mk8."""

    def _read_from_mk8_env_vars(self) -> Optional[AWSCredentials]:
        """Read from MK8_AWS_* environment variables."""

    def _read_from_aws_env_vars(self) -> Optional[AWSCredentials]:
        """Read from standard AWS_* environment variables."""

    def _prompt_for_env_var_usage(self) -> PromptChoice:
        """Prompt user about using AWS_* environment variables."""

    def _prompt_for_manual_entry(self, allow_env_option: bool) -> PromptChoice:
        """Prompt user to enter credentials or exit."""

    def _interactive_credential_entry(self) -> AWSCredentials:
        """Prompt user to enter credentials interactively."""

    def _save_credentials(self, credentials: AWSCredentials) -> None:
        """Save credentials to config file with secure permissions."""

    def _check_credentials_changed(
        self,
        old: Optional[AWSCredentials],
        new: AWSCredentials
    ) -> bool:
        """Check if credentials have changed."""
```

### 2. CrossplaneManager

**Purpose**: Synchronize AWS credentials with Crossplane in Kubernetes clusters.

**Location**: `mk8/business/crossplane_manager.py`

**Interface**:
```python
class CrossplaneManager:
    """Manages Crossplane credential synchronization."""

    def __init__(
        self,
        kubectl_client: KubectlClient,
        output: OutputFormatter
    ):
        """Initialize Crossplane manager with dependencies."""

    def sync_credentials(self, credentials: AWSCredentials) -> SyncResult:
        """
        Synchronize credentials to Crossplane.
        
        Args:
            credentials: AWS credentials to sync
            
        Returns:
            SyncResult with success status
            
        Raises:
            CommandError: If Kubernetes operations fail
        """

    def cluster_exists(self) -> bool:
        """Check if a Crossplane-enabled cluster exists."""

    def create_or_update_secret(self, credentials: AWSCredentials) -> None:
        """Create or update AWS credentials Kubernetes secret."""

    def verify_provider_config(self) -> bool:
        """Verify ProviderConfig references the credentials secret."""

    def _build_secret_manifest(self, credentials: AWSCredentials) -> str:
        """Build Kubernetes secret YAML manifest."""
```

### 3. AWSClient

**Purpose**: Interface with AWS APIs for credential validation.

**Location**: `mk8/integrations/aws_client.py`

**Interface**:
```python
class AWSClient:
    """Client for AWS API operations."""

    def __init__(self):
        """Initialize AWS client."""

    def validate_credentials(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str
    ) -> ValidationResult:
        """
        Validate credentials using STS GetCallerIdentity.
        
        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region
            
        Returns:
            ValidationResult with account_id if successful
        """

    def _mask_secret(self, secret: str) -> str:
        """Mask secret for display (show first/last 4 chars)."""
```

### 4. FileIO

**Purpose**: Handle file operations for credential storage.

**Location**: `mk8/integrations/file_io.py`

**Interface**:
```python
class FileIO:
    """Handles file I/O operations."""

    def __init__(self):
        """Initialize file I/O handler."""

    def read_config_file(self) -> Optional[Dict[str, str]]:
        """
        Read configuration from ~/.config/mk8.
        
        Returns:
            Dictionary of key-value pairs or None if file doesn't exist
        """

    def write_config_file(self, config: Dict[str, str]) -> None:
        """
        Write configuration to ~/.config/mk8 with secure permissions.
        
        Args:
            config: Dictionary of key-value pairs to write
            
        Raises:
            ConfigurationError: If file cannot be written
        """

    def ensure_config_directory(self) -> None:
        """Ensure ~/.config directory exists."""

    def set_secure_permissions(self, file_path: str) -> None:
        """Set file permissions to 0600."""

    def check_file_permissions(self, file_path: str) -> bool:
        """Check if file has secure permissions (0600)."""
```

### 5. ConfigCommand

**Purpose**: CLI command handler for `mk8 config`.

**Location**: `mk8/cli/commands/config.py`

**Interface**:
```python
class ConfigCommand:
    """Handler for mk8 config command."""

    @staticmethod
    def execute(ctx: click.Context) -> int:
        """
        Execute config command.
        
        Args:
            ctx: Click context with verbose, logger, output
            
        Returns:
            Exit code (0 for success)
        """
```

## Data Models

### AWSCredentials
```python
@dataclass
class AWSCredentials:
    """AWS credential set."""

    access_key_id: str
    secret_access_key: str
    region: str

    def is_complete(self) -> bool:
        """Check if all three credentials are present and non-empty."""
        return bool(
            self.access_key_id
            and self.secret_access_key
            and self.region
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for storage."""
        return {
            "AWS_ACCESS_KEY_ID": self.access_key_id,
            "AWS_SECRET_ACCESS_KEY": self.secret_access_key,
            "AWS_DEFAULT_REGION": self.region,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "AWSCredentials":
        """Create from dictionary."""
        return cls(
            access_key_id=data.get("AWS_ACCESS_KEY_ID", ""),
            secret_access_key=data.get("AWS_SECRET_ACCESS_KEY", ""),
            region=data.get("AWS_DEFAULT_REGION", ""),
        )

    @classmethod
    def from_env_vars(cls, prefix: str = "AWS") -> Optional["AWSCredentials"]:
        """
        Create from environment variables.
        
        Args:
            prefix: Variable prefix ("AWS" or "MK8_AWS")
            
        Returns:
            AWSCredentials if all three vars present, None otherwise
        """
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    """Result of credential validation."""

    success: bool
    account_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def get_suggestions(self) -> List[str]:
        """Get suggestions based on error code."""
        if not self.success and self.error_code:
            return self._error_code_to_suggestions(self.error_code)
        return []

    def _error_code_to_suggestions(self, error_code: str) -> List[str]:
        """Map AWS error codes to user-friendly suggestions."""
```

### SyncResult
```python
@dataclass
class SyncResult:
    """Result of Crossplane credential synchronization."""

    success: bool
    cluster_exists: bool
    secret_updated: bool
    validation_result: Optional[ValidationResult] = None
    error: Optional[str] = None
```

### PromptChoice
```python
class PromptChoice(Enum):
    """User choices for credential prompts."""

    USE_ENV_VARS = "use_env"
    ENTER_MANUALLY = "enter_manual"
    EXIT = "exit"
```


## Error Handling

### Error Types

**ConfigurationError**: Used for all credential-related errors
- Missing credentials
- Invalid configuration file
- Permission issues
- File I/O failures

**CommandError**: Used for Crossplane synchronization failures
- Kubernetes API failures
- kubectl command failures
- Secret creation/update failures

**ValidationError**: Used for AWS credential validation failures
- Invalid credentials
- Insufficient IAM permissions
- Network connectivity issues

### Error Messages and Suggestions

#### Missing Credentials
```
Error: AWS credentials not configured

No credentials found in:
  • Configuration file (~/.config/mk8)
  • MK8_AWS_* environment variables
  • AWS_* environment variables

Suggestions:
  • Run 'mk8 config' to configure credentials interactively
  • Set MK8_AWS_ACCESS_KEY_ID, MK8_AWS_SECRET_ACCESS_KEY, and MK8_AWS_DEFAULT_REGION
  • Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION
```

#### Incomplete Configuration File
```
Error: Configuration file is incomplete

Found ~/.config/mk8 but missing required credentials:
  • AWS_SECRET_ACCESS_KEY
  • AWS_DEFAULT_REGION

Suggestions:
  • Run 'mk8 config' to reconfigure credentials
  • Manually edit ~/.config/mk8 to add missing values
```

#### Invalid Permissions
```
Error: Configuration file has insecure permissions

File ~/.config/mk8 is readable by other users (current: 0644)

Suggestions:
  • Run: chmod 600 ~/.config/mk8
  • Or run 'mk8 config' to recreate with secure permissions
```

#### AWS Validation Failure
```
Error: AWS credentials are invalid

AWS API returned: InvalidClientTokenId
The security token included in the request is invalid

Suggestions:
  • Verify your AWS Access Key ID is correct
  • Check if the credentials have been deactivated in IAM
  • Run 'mk8 config' to update credentials
```

#### Insufficient IAM Permissions
```
Error: AWS credentials lack required permissions

AWS API returned: AccessDenied
User is not authorized to perform: sts:GetCallerIdentity

Suggestions:
  • Ensure the IAM user/role has 'sts:GetCallerIdentity' permission
  • Check IAM policies attached to your credentials
  • Contact your AWS administrator for permission updates
```

#### Crossplane Sync Failure
```
Error: Failed to synchronize credentials to Crossplane

kubectl command failed: secret "aws-credentials" could not be created

Suggestions:
  • Verify kubectl is configured correctly
  • Check if you have permissions to create secrets in the cluster
  • Ensure the cluster is running: kubectl cluster-info
```

### Exit Codes

- `ExitCode.SUCCESS` (0): Credentials configured successfully
- `ExitCode.CONFIGURATION_ERROR` (5): Credential configuration failed
- `ExitCode.COMMAND_ERROR` (2): Crossplane sync failed
- `ExitCode.KEYBOARD_INTERRUPT` (130): User cancelled operation

## Testing Strategy

### Unit Testing

**Framework**: pytest with pytest-mock

**Coverage Target**: >80% overall, 100% for security-critical paths

**Test Organization**:
```
tests/unit/
├── business/
│   ├── test_credential_manager.py
│   └── test_crossplane_manager.py
├── integrations/
│   ├── test_aws_client.py
│   └── test_file_io.py
└── cli/
    └── test_config_command.py
```

**Key Test Cases**:

1. **CredentialManager**:
   - Reading from config file (complete, incomplete, missing)
   - Reading from MK8_* environment variables (all set, partial, none)
   - Reading from AWS_* environment variables (all set, partial, none)
   - Interactive credential entry (successful, cancelled)
   - Credential validation (success, various AWS errors)
   - Credential change detection

2. **CrossplaneManager**:
   - Cluster existence check
   - Secret creation and updates
   - ProviderConfig verification
   - Error handling for kubectl failures

3. **AWSClient**:
   - Successful validation with account ID
   - Various AWS error codes (InvalidClientTokenId, AccessDenied, etc.)
   - Network failures
   - Secret masking

4. **FileIO**:
   - Config file reading (exists, missing, malformed)
   - Config file writing with secure permissions
   - Directory creation
   - Permission checking and setting

5. **ConfigCommand**:
   - Command execution with various scenarios
   - Context passing
   - Exit code handling

### Property-Based Testing

**Framework**: Hypothesis

**Configuration**: Minimum 100 iterations per property


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Credential Source Priority Order
*For any* credential acquisition request, the system should check sources in this exact order: (1) config file, (2) MK8_* environment variables, (3) AWS_* environment variables, (4) interactive prompts, and should use the first complete set found.
**Validates: Requirements 1.1, 2.1, 3.1**

### Property 2: Complete Credential Set Requirement
*For any* credential source (config file, environment variables, or interactive input), credentials should only be considered valid if all three values (access_key_id, secret_access_key, region) are present and non-empty.
**Validates: Requirements 1.2, 1.3, 1.4, 2.4**

### Property 3: Incomplete Credential Reporting
*For any* incomplete credential set from the config file, the error message should list exactly which credentials are missing from the set {AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION}.
**Validates: Requirements 1.4, 1.5**

### Property 4: Config File Format Consistency
*For any* credentials saved to the config file, the keys should be exactly "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", and "AWS_DEFAULT_REGION".
**Validates: Requirements 1.6**

### Property 5: Secure File Permissions
*For any* config file write operation, the resulting file should have permissions set to 0600 (readable and writable only by owner).
**Validates: Requirements 1.7, 8.1**

### Property 6: Config Directory Creation
*For any* config file write operation when ~/.config doesn't exist, the directory should be created before writing the file.
**Validates: Requirements 1.8**

### Property 7: MK8 Environment Variable Auto-Configuration
*For any* credential acquisition when all three MK8_* environment variables are set and the config file is missing or incomplete, the credentials should be automatically saved to the config file without user prompting.
**Validates: Requirements 2.2**

### Property 8: Partial MK8 Variables Ignored
*For any* credential acquisition when only 1 or 2 MK8_* environment variables are set, the system should skip them and proceed to check AWS_* environment variables.
**Validates: Requirements 2.4**

### Property 9: Config Command Overwrites Existing Config
*For any* execution of `mk8 config`, if a config file already exists, it should be completely replaced with the new credentials regardless of its previous contents.
**Validates: Requirements 5.5**

### Property 10: Crossplane Secret Contains All Credentials
*For any* Crossplane credential synchronization, the created Kubernetes secret should contain all three keys: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION.
**Validates: Requirements 6.2**

### Property 11: Crossplane Sync Updates Secret and ProviderConfig
*For any* credential update when a Crossplane cluster exists, both the Kubernetes secret should be updated and the ProviderConfig should reference the updated secret.
**Validates: Requirements 6.4, 6.5**

### Property 12: Credential Validation Calls AWS API
*For any* credential configuration in Crossplane, the system should make an AWS STS GetCallerIdentity API call to validate the credentials.
**Validates: Requirements 7.1**

### Property 13: Successful Validation Returns Account ID
*For any* successful credential validation, the output should include the AWS account ID returned from the STS API.
**Validates: Requirements 7.2**

### Property 14: Failed Validation Includes Error Details
*For any* failed credential validation, the error message should include both the AWS error code and the AWS error message.
**Validates: Requirements 7.4**

### Property 15: Secret Masking in Output
*For any* error message or log output that includes an AWS secret access key, the secret should be masked showing only the first and last 4 characters.
**Validates: Requirements 8.2**

### Property 16: Insecure Permissions Warning
*For any* config file read operation where the file has permissions more permissive than 0600, the system should warn the user and suggest correcting the permissions.
**Validates: Requirements 8.4**

### Property 17: No Credential Logging
*For any* log output, actual credential values (access key ID, secret access key) should never appear in full.
**Validates: Requirements 8.5**

### Property 18: Credential Change Detection
*For any* `mk8 config` execution with existing credentials, the system should compare the new credentials with the existing ones and report whether they changed.
**Validates: Requirements 9.1, 9.2, 9.4**

### Property 19: Error Messages Include Suggestions
*For any* error raised by the credential management system, the error message should include at least one actionable suggestion for resolving the issue.
**Validates: Requirements 10.2**

### Property 20: AWS Error Codes Include IAM Suggestions
*For any* AWS API error related to permissions (AccessDenied, InvalidClientTokenId, etc.), the error message should include suggestions about checking IAM policies or permissions.
**Validates: Requirements 7.5, 10.5**

## Implementation Details

### Configuration File Format

The `~/.config/mk8` file uses a simple key=value format:

```
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
```

**Rationale**: Simple format for easy manual editing, standard AWS variable names for familiarity.

### Kubernetes Secret Format

The Crossplane AWS credentials secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: aws-credentials
  namespace: crossplane-system
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: AKIAIOSFODNN7EXAMPLE
  AWS_SECRET_ACCESS_KEY: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  AWS_DEFAULT_REGION: us-east-1
```

### ProviderConfig Reference

```yaml
apiVersion: aws.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-credentials
      key: credentials
```

### Interactive Prompts

**When all three AWS_* environment variables are set**:
```
AWS credentials detected in environment variables.

Options:
  1. Use existing AWS_* environment variables and save to config
  2. Enter credentials manually and save to config
  3. Exit without configuring

Choice [1/2/3]:
```

**When AWS_* environment variables are incomplete**:
```
AWS credentials not found in environment variables.

Options:
  1. Enter credentials manually and save to config
  2. Exit without configuring

Choice [1/2]:
```

**Interactive credential entry**:
```
AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key: ************************************
AWS Default Region: us-east-1

Credentials saved to ~/.config/mk8
```

### Secret Masking Algorithm

```python
def mask_secret(secret: str) -> str:
    """Mask secret showing only first and last 4 characters."""
    if len(secret) <= 8:
        return "****"
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"

# Example: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
# Becomes: "wJal********************************EKEY"
```

### AWS Error Code Mapping

Common AWS error codes and their suggestions:

| Error Code | Suggestions |
|------------|-------------|
| InvalidClientTokenId | Verify Access Key ID is correct, check if credentials are deactivated |
| SignatureDoesNotMatch | Verify Secret Access Key is correct |
| AccessDenied | Check IAM policies, ensure required permissions are granted |
| InvalidToken | Token may have expired, regenerate credentials |
| UnrecognizedClientException | Verify region is correct, check AWS service availability |

### Dependency Injection Pattern

All components use constructor injection for testability:

```python
# In CLI command
def execute(ctx: click.Context) -> int:
    file_io = FileIO()
    aws_client = AWSClient()
    kubectl_client = KubectlClient()
    output = ctx.obj["output"]
    
    cred_manager = CredentialManager(file_io, aws_client, output)
    crossplane_manager = CrossplaneManager(kubectl_client, output)
    
    # Use managers...
```

This allows easy mocking in tests:

```python
# In tests
def test_credential_acquisition():
    mock_file_io = Mock(spec=FileIO)
    mock_aws_client = Mock(spec=AWSClient)
    mock_output = Mock(spec=OutputFormatter)
    
    manager = CredentialManager(mock_file_io, mock_aws_client, mock_output)
    # Test manager behavior...
```

## Security Considerations

### Credential Storage

- **File permissions**: 0600 ensures only the owner can read/write
- **No encryption**: Credentials stored in plaintext (secured by OS permissions)
- **Rationale**: Matches AWS CLI behavior, relies on OS-level security

### Credential Transmission

- **In-memory only**: Credentials passed between components in memory
- **No network transmission**: Credentials only sent to AWS APIs via boto3 (HTTPS)
- **Kubernetes secrets**: Stored as Kubernetes secrets (base64 encoded, not encrypted by default)

### Credential Display

- **Masking**: Secret access keys always masked in output
- **Logging**: Credentials never logged in full
- **Error messages**: Only masked secrets in error output

### Threat Model

**Threats mitigated**:
- Unauthorized file access (via 0600 permissions)
- Credential exposure in logs (via masking)
- Credential exposure in error messages (via masking)

**Threats not mitigated** (out of scope for MVP):
- Root user access to config file
- Memory dumps containing credentials
- Kubernetes secret encryption at rest
- Credential rotation
- Temporary credentials / AWS STS

## Performance Considerations

### File I/O

- **Config file reads**: Cached after first read (invalidated on write)
- **Permission checks**: Only performed on write operations
- **Directory creation**: Only attempted if write fails

### AWS API Calls

- **Validation**: Single STS GetCallerIdentity call per configuration
- **Timeout**: 10-second timeout for AWS API calls
- **Retry**: No automatic retry (fail fast for user feedback)

### Kubernetes Operations

- **Secret updates**: Single kubectl apply operation
- **ProviderConfig check**: Single kubectl get operation
- **Cluster detection**: Check for kubeconfig context

### Expected Performance

- Config file read: <10ms
- Config file write: <50ms
- AWS validation: 200-500ms (network dependent)
- Crossplane sync: 500-1000ms (network dependent)
- Total `mk8 config` execution: <2 seconds

## Future Enhancements

### Potential Improvements (Out of Scope for MVP)

1. **AWS SSO Support**: Integration with AWS Single Sign-On
2. **Temporary Credentials**: Support for AWS STS temporary credentials
3. **Credential Rotation**: Automatic credential rotation and expiry handling
4. **Multiple Profiles**: Support for multiple AWS credential profiles
5. **Assume Role**: Support for IAM role assumption
6. **Credential Encryption**: Encrypt credentials at rest using OS keychain
7. **Region Validation**: Validate region against AWS region list
8. **IAM Permission Check**: Pre-flight check for required IAM permissions
9. **Credential Expiry Warnings**: Warn when credentials are about to expire
10. **AWS Config File Integration**: Read from ~/.aws/credentials and ~/.aws/config

### Migration Path

If encryption is added in the future:
1. Detect unencrypted config file
2. Prompt user to migrate
3. Encrypt and replace file
4. Maintain backward compatibility with unencrypted files

## Dependencies

### Python Packages

- **boto3**: AWS SDK for Python (credential validation)
- **click**: CLI framework (prompts, commands)
- **pytest**: Testing framework
- **pytest-mock**: Mocking for tests
- **hypothesis**: Property-based testing

### External Tools

- **kubectl**: Kubernetes CLI (Crossplane secret management)
- **AWS APIs**: STS service for credential validation

### Internal Dependencies

- `mk8.core.errors`: Error types and exit codes
- `mk8.core.logging`: Logging infrastructure
- `mk8.cli.output`: Output formatting
- `mk8.cli.main`: CLI framework and context

## Acceptance Criteria Mapping

This design addresses all requirements from the requirements document:

- **Requirement 1** (Configuration File Management): Covered by CredentialManager, FileIO
- **Requirement 2** (MK8 Environment Variables): Covered by CredentialManager._read_from_mk8_env_vars
- **Requirement 3** (Standard AWS Environment Variables): Covered by CredentialManager._prompt_for_env_var_usage
- **Requirement 4** (Interactive Credential Entry): Covered by CredentialManager._interactive_credential_entry
- **Requirement 5** (mk8 config Command): Covered by ConfigCommand
- **Requirement 6** (Crossplane Synchronization): Covered by CrossplaneManager
- **Requirement 7** (Credentials Validation): Covered by AWSClient.validate_credentials
- **Requirement 8** (Credential Security): Covered by FileIO.set_secure_permissions, AWSClient._mask_secret
- **Requirement 9** (Credential Update Detection): Covered by CredentialManager._check_credentials_changed
- **Requirement 10** (Error Handling): Covered by all error handling throughout

All 20 correctness properties map to specific acceptance criteria and will be implemented as property-based tests.
