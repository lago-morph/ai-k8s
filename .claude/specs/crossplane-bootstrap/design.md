# Design Document

## Architecture Overview

The crossplane-bootstrap feature implements a complete Crossplane installation and configuration system for the bootstrap cluster. It follows a layered architecture with clear separation between Helm operations, Crossplane orchestration, and CLI presentation.

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Layer                                │
│  mk8 crossplane {install|uninstall|status}                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Business Logic Layer                            │
│  CrossplaneInstaller - Orchestrates installation workflow    │
│  CrossplaneStatus - Installation state model                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Integration Layer                               │
│  HelmClient - Helm chart operations                          │
│  KubectlClient - Resource management                         │
│  CredentialManager - AWS credentials                         │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. HelmClient (Integration Layer)

**Purpose**: Provides a Python interface to Helm CLI operations with error handling and output parsing.

**Responsibilities**:
- Execute Helm commands with proper context
- Parse Helm output and errors
- Manage repositories (add, update)
- Install, upgrade, and uninstall charts
- Query release status and information
- Handle timeouts and failures gracefully

**Key Methods**:
```python
class HelmClient:
    def add_repository(name: str, url: str, force: bool) -> None
    def update_repositories() -> None
    def install_chart(release_name, chart, namespace, values, ...) -> None
    def upgrade_chart(release_name, chart, namespace, values, ...) -> None
    def uninstall_release(release_name, namespace, wait) -> None
    def list_releases(namespace) -> List[Dict]
    def get_release_status(release_name, namespace) -> Dict
    def release_exists(release_name, namespace) -> bool
    def wait_for_release(release_name, namespace, timeout) -> None
```

**Error Handling**:
- Parses Helm stderr for common error patterns
- Provides context-specific suggestions
- Handles command not found, timeouts, and failures
- Maps Helm errors to MK8Error hierarchy

### 2. CrossplaneStatus (Data Model)

**Purpose**: Represents the current state of Crossplane installation.

**Structure**:
```python
@dataclass
class CrossplaneStatus:
    installed: bool = False
    version: Optional[str] = None
    namespace: str = "crossplane-system"
    release_name: str = "crossplane"
    ready: bool = False
    pod_count: int = 0
    ready_pods: int = 0
    aws_provider_installed: bool = False
    aws_provider_ready: bool = False
    provider_config_exists: bool = False
    issues: List[str] = field(default_factory=list)
```

**Usage**: Returned by `CrossplaneInstaller.get_status()` for status reporting.

### 3. CrossplaneInstaller (Business Logic Layer)

**Purpose**: Orchestrates the complete Crossplane installation and configuration workflow.

**Responsibilities**:
- Install Crossplane via Helm
- Install AWS provider
- Configure AWS credentials
- Create ProviderConfig
- Monitor installation progress
- Validate AWS connectivity
- Handle cleanup and uninstallation
- Report status

**Key Methods**:
```python
class CrossplaneInstaller:
    def install_crossplane(version: Optional[str]) -> None
    def install_aws_provider() -> None
    def configure_aws_provider(credentials: AWSCredentials) -> None
    def uninstall_crossplane() -> None
    def get_status() -> CrossplaneStatus
```

**Installation Workflow**:
```
1. Add Crossplane Helm repository
2. Update repositories
3. Install Crossplane chart with values
4. Wait for Crossplane pods to be ready
5. Create AWS Provider resource
6. Wait for provider to be ready
7. Create AWS credentials secret
8. Create ProviderConfig resource
9. Wait for ProviderConfig to be ready
10. Validate AWS connectivity
```

**Uninstallation Workflow**:
```
1. Delete ProviderConfig (continue on error)
2. Delete AWS Provider (continue on error)
3. Uninstall Helm release (continue on error)
4. Delete namespace (continue on error)
5. Report cleanup summary
```

### 4. CLI Commands

**Purpose**: Provide user-friendly commands for Crossplane management.

**Commands**:

#### `mk8 crossplane install`
- Installs Crossplane on bootstrap cluster
- Options: `--version`, `--verbose`
- Validates AWS credentials before installation
- Displays progress and success messages
- Provides next steps after installation

#### `mk8 crossplane uninstall`
- Removes Crossplane and all components
- Options: `--yes`, `--verbose`
- Requires confirmation (unless --yes)
- Performs resilient cleanup
- Reports what was removed

#### `mk8 crossplane status`
- Shows current Crossplane installation state
- Options: `--verbose`
- Displays version, pod status, provider status
- Highlights issues and provides suggestions
- Indicates if ready for resource provisioning

## Data Flow

### Installation Flow

```
User Command
    │
    ▼
CLI Layer (crossplane.py)
    │
    ├─> Get AWS credentials (CredentialManager)
    ├─> Validate credentials
    │
    ▼
CrossplaneInstaller
    │
    ├─> Add Helm repo (HelmClient)
    ├─> Install chart (HelmClient)
    ├─> Wait for pods (kubectl)
    ├─> Create Provider (kubectl)
    ├─> Create Secret (KubectlClient)
    ├─> Create ProviderConfig (kubectl)
    └─> Validate connectivity
    │
    ▼
Success/Error Response
    │
    ▼
User Feedback (OutputFormatter)
```

### Status Flow

```
User Command
    │
    ▼
CLI Layer (crossplane.py)
    │
    ▼
CrossplaneInstaller.get_status()
    │
    ├─> Check Helm release (HelmClient)
    ├─> Get pod status (kubectl)
    ├─> Check Provider (kubectl)
    └─> Check ProviderConfig (kubectl)
    │
    ▼
CrossplaneStatus
    │
    ▼
User Feedback (OutputFormatter)
```

## Error Handling Strategy

### Error Types

1. **HelmError**: Helm operations fail
   - Repository not found
   - Chart installation failure
   - Release conflicts
   - Timeout errors

2. **CrossplaneInstallationError**: Crossplane setup fails
   - Pod startup failures
   - Provider installation issues
   - ProviderConfig validation errors
   - AWS connectivity problems

3. **Configuration Errors**: Missing or invalid configuration
   - No AWS credentials
   - Invalid credentials
   - Insufficient IAM permissions

### Error Response Pattern

All errors include:
- Clear, human-readable message
- Specific suggestions for resolution
- Relevant diagnostic commands
- Context about what failed

Example:
```python
raise CrossplaneInstallationError(
    "Failed to install AWS provider: pod failed to start",
    suggestions=[
        "Check provider status: kubectl get providers",
        "Check provider pods: kubectl get pods -n crossplane-system",
        "Check events: kubectl get events --sort-by=.metadata.creationTimestamp",
    ],
)
```

## Safety Guarantees

### Context Isolation
- All operations use explicit context: `kind-mk8-bootstrap`
- No operations on other clusters
- Prevents accidental modifications

### Idempotency
- Detect existing installations
- Skip or update existing resources
- Safe to re-run commands

### Resilient Cleanup
- Continue cleanup on partial failures
- Report what was cleaned up
- Report what failed to clean up
- Never leave system in broken state

### Validation
- Validate AWS credentials before installation
- Wait for readiness before proceeding
- Verify each step before moving to next

## Configuration

### Helm Values
```yaml
resourcesCrossplane:
  limits:
    cpu: "100m"
    memory: "512Mi"
  requests:
    cpu: "100m"
    memory: "256Mi"
resourcesRBACManager:
  limits:
    cpu: "100m"
    memory: "512Mi"
  requests:
    cpu: "100m"
    memory: "256Mi"
```

### AWS Provider Version
- Default: `xpkg.upbound.io/crossplane-contrib/provider-aws:v0.44.0`
- Compatible with Crossplane 1.14.x

### Namespace
- Crossplane: `crossplane-system`
- All resources created in this namespace

### ProviderConfig
- Name: `default`
- Credentials source: Kubernetes Secret
- Secret name: `aws-credentials`
- Secret key: `creds`

## Correctness Properties

### Property 1: Installation Atomicity
**Property**: Crossplane installation either completes fully or fails cleanly without partial state.
**Implementation**: Wait for each step to complete before proceeding; rollback on failure.

### Property 2: Context Safety
**Property**: All operations target the bootstrap cluster context only.
**Implementation**: Explicit context specification in all Helm and kubectl operations.

### Property 3: Credential Security
**Property**: AWS credentials are stored securely in Kubernetes secrets with appropriate permissions.
**Implementation**: Use KubectlClient.apply_secret() with proper namespace and permissions.

### Property 4: Idempotency
**Property**: Running install multiple times produces the same result without errors.
**Implementation**: Check for existing resources; skip or update as appropriate.

### Property 5: Status Accuracy
**Property**: Status command always reflects current actual state.
**Implementation**: Query live cluster state; never cache status information.

### Property 6: Error Clarity
**Property**: All errors include actionable suggestions for resolution.
**Implementation**: Parse error messages; provide context-specific suggestions.

### Property 7: Progress Visibility
**Property**: Long-running operations provide progress feedback.
**Implementation**: Display progress messages; periodic status updates during waits.

### Property 8: Cleanup Completeness
**Property**: Uninstall removes all Crossplane resources.
**Implementation**: Delete ProviderConfig, Provider, Helm release, and namespace.

### Property 9: Cleanup Resilience
**Property**: Cleanup continues even if individual steps fail.
**Implementation**: Try-except around each cleanup step; report all results.

### Property 10: Version Compatibility
**Property**: Installed components are version-compatible.
**Implementation**: Use tested version combinations; validate compatibility.

### Property 11: Readiness Validation
**Property**: System waits for components to be ready before proceeding.
**Implementation**: Poll pod status; wait for "Running" state; timeout with error.

### Property 12: AWS Connectivity
**Property**: System validates AWS API connectivity before declaring success.
**Implementation**: Test API calls after ProviderConfig creation.

### Property 13: Permission Verification
**Property**: System checks for required IAM permissions.
**Implementation**: Validate credentials with CredentialManager before installation.

### Property 14: Resource Limits
**Property**: Crossplane components have appropriate resource limits for local cluster.
**Implementation**: Configure resource requests/limits in Helm values.

### Property 15: Namespace Isolation
**Property**: All Crossplane resources are isolated in crossplane-system namespace.
**Implementation**: Specify namespace in all resource creation operations.

## Testing Strategy

### Unit Tests
- HelmClient command execution and error parsing
- CrossplaneInstaller orchestration logic
- Status model construction
- Error handling and suggestions

### Integration Tests
- Full installation workflow
- Uninstallation and cleanup
- Status reporting
- Error scenarios (no cluster, no credentials, etc.)

### Manual Testing
- Install on real bootstrap cluster
- Verify all pods running
- Check AWS provider functionality
- Test status command
- Test uninstall cleanup
- Test with invalid credentials
- Test version selection

## Dependencies

### External Tools
- `helm` - Helm CLI for chart operations
- `kubectl` - Kubernetes CLI for resource management

### Internal Components
- `HelmClient` - Helm operations
- `KubectlClient` - Kubernetes operations
- `CredentialManager` - AWS credential management
- `OutputFormatter` - User feedback
- `MK8Error` - Error handling framework

### Kubernetes Resources
- Namespace: crossplane-system
- Helm Release: crossplane
- Provider: provider-aws
- ProviderConfig: default
- Secret: aws-credentials

## Future Enhancements

1. **Multiple Provider Support**: Support for Azure, GCP providers
2. **Custom ProviderConfigs**: Allow multiple ProviderConfigs for different AWS accounts
3. **Upgrade Management**: Automated Crossplane version upgrades
4. **Health Monitoring**: Continuous health checks and alerting
5. **Resource Validation**: Validate managed resources before creation
6. **Backup/Restore**: Backup and restore Crossplane configuration
7. **Multi-Region**: Support for multi-region AWS configurations
8. **IAM Role Support**: Support for IAM roles instead of access keys
