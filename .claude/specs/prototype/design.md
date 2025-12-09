# Design Document

## Overview

The prototype is a minimal, transparent bash-based implementation of mk8's core functionality. It serves as a reference implementation that prioritizes readability, debuggability, and visibility of operations over robustness. The design follows a simple script-based architecture where each command directly invokes the underlying tools (kind, kubectl, helm, aws) with minimal abstraction.

The prototype demonstrates the essential workflows:
1. CLI command parsing and routing
2. AWS credential validation
3. Local kind cluster lifecycle management
4. Crossplane installation via Helm

All operations are logged verbosely, showing the exact commands being executed, making it ideal for learning, debugging, and understanding the underlying Kubernetes operations.

## Architecture

The prototype uses a simple, flat architecture:

```
prototype/
├── mk8-prototype.sh          # Main entry point with CLI parsing
├── env-bootstrap.sh          # Utility to set KUBECONFIG and MK8_* env vars
├── lib/
│   ├── common.sh             # Shared utilities (logging, error handling)
│   ├── config.sh             # AWS credential management
│   ├── bootstrap.sh          # kind cluster operations
│   └── crossplane.sh         # Crossplane installation and S3 operations
├── .config/
│   ├── mk8-bootstrap         # Isolated kubeconfig for bootstrap cluster
│   └── env-mk8-aws-template  # Template for MK8_* environment variables
└── README.md                 # Usage documentation

# User's home directory (for integration testing with real credentials)
~/.config/
└── env-mk8-aws               # Optional: Real AWS credentials (takes precedence)
```

### Architecture Principles

1. **Transparency First**: Every external command is logged before execution
2. **Minimal Abstraction**: Direct invocation of tools with minimal wrapper logic
3. **Single Responsibility**: Each script handles one domain (config, bootstrap, crossplane)
4. **Fail Fast**: Simple error checking without complex recovery logic
5. **Self-Documenting**: Code comments explain what and why, not just how

### Execution Flow

```mermaid
graph TD
    A[User invokes mk8-prototype.sh] --> B{Parse Command}
    B -->|version| C[Display Version]
    B -->|config| D[Validate AWS Credentials]
    B -->|bootstrap| E{Parse Subcommand}
    B -->|crossplane| F{Parse Subcommand}
    B -->|help| G[Display Help]
    B -->|unknown| H[Display Error]
    
    D --> D1[Check MK8_* env vars only]
    D1 --> D2[Export to standard AWS vars temporarily]
    D2 --> D3[Call aws sts get-caller-identity]
    D3 --> D4[Unset standard AWS vars]
    D4 --> D5[Display account info]
    
    E -->|create| E1[kind create cluster with isolated kubeconfig]
    E1 --> E2[Store kubeconfig in .config/mk8-bootstrap]
    E -->|status| E3[kubectl cluster-info using isolated kubeconfig]
    E -->|delete| E4[kind delete cluster]
    
    F -->|install| F1[helm repo add]
    F1 --> F2[helm install crossplane]
    F2 --> F3[kubectl wait for pods]
    F3 --> F4[Create AWS ProviderConfig secret]
    F4 --> F5[Verify AWS Provider is ready]
    F -->|status| F6[kubectl get providers and providerconfigs]
    F -->|create-s3| F7[Generate UUID for bucket name]
    F7 --> F8[Apply S3 Bucket MRD]
    F8 --> F9[Wait and check MRD status]
    F9 --> F10[Verify with AWS CLI]
    F10 --> F11[Save bucket name to state file]
    F -->|delete-s3| F12[Read bucket name from state]
    F12 --> F13[Delete S3 Bucket MRD]
    F13 --> F14[Verify deletion]
    F14 --> F15[Clear state file]
```

## Components and Interfaces

### 1. Main Entry Point (mk8-prototype.sh)

**Purpose**: CLI parsing and command routing

**Interface**:
```bash
./mk8-prototype.sh <command> [subcommand] [options]

Commands:
  version                    Display version information
  config                     Validate AWS credentials from environment
  bootstrap create           Create local kind cluster
  bootstrap status           Show bootstrap cluster status
  bootstrap delete           Delete bootstrap cluster
  crossplane install         Install Crossplane via Helm
  crossplane status          Show Crossplane and AWS Provider status
  crossplane create-s3       Create test S3 bucket via Crossplane
  crossplane delete-s3       Delete test S3 bucket
  help                       Display help information
```

**Responsibilities**:
- Parse command-line arguments
- Route to appropriate command handler
- Display usage/help information
- Set up environment (source library scripts)
- Ensure MK8_* environment variables are used exclusively

### 2. Common Library (lib/common.sh)

**Purpose**: Shared utilities for logging and error handling

**Functions**:
```bash
log_info()      # Log informational message
log_success()   # Log success message
log_error()     # Log error message and exit
log_command()   # Log command before execution
check_prereq()  # Check if required command exists
```

**Responsibilities**:
- Consistent logging format with colors
- Command execution logging
- Prerequisite checking
- Error handling and exit codes

### 3. Config Module (lib/config.sh)

**Purpose**: AWS credential management with strict isolation

**Functions**:
```bash
validate_aws_credentials()  # Check and validate AWS credentials
with_mk8_aws_env()         # Execute command with MK8_* vars mapped to AWS_* temporarily
```

**Environment Variables**:
- `MK8_AWS_ACCESS_KEY_ID`: AWS access key (REQUIRED)
- `MK8_AWS_SECRET_ACCESS_KEY`: AWS secret key (REQUIRED)
- `MK8_AWS_REGION`: AWS region (default: us-east-1)

**Critical Constraint**:
- NEVER use standard AWS environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
- Only use MK8_* prefixed variables
- Temporarily map MK8_* to AWS_* only within subshells when calling AWS CLI
- Immediately unset standard AWS_* variables after use

**Responsibilities**:
- Check for required MK8_* environment variables
- Validate credentials via AWS STS (using temporary mapping)
- Display account information
- Ensure complete isolation from user's AWS configuration

### 4. Bootstrap Module (lib/bootstrap.sh)

**Purpose**: kind cluster lifecycle management with isolated kubeconfig

**Functions**:
```bash
bootstrap_create()   # Create kind cluster with isolated kubeconfig
bootstrap_status()   # Show cluster status
bootstrap_delete()   # Delete kind cluster
get_kubeconfig_path() # Return path to isolated kubeconfig
```

**Configuration**:
- Cluster name: `mk8-bootstrap`
- Kubeconfig location: `.config/mk8-bootstrap` (relative to script directory)
- Uses default kind configuration

**Kubeconfig Isolation**:
- NEVER merge into `~/.kube/config`
- Store kubeconfig in dedicated `.config/` directory
- All kubectl commands use `--kubeconfig` flag or KUBECONFIG environment variable
- Provide `env-bootstrap.sh` utility for users to source

**Responsibilities**:
- Create/delete kind clusters with isolated kubeconfig
- Display cluster status using isolated kubeconfig
- Log all kind and kubectl commands
- Maintain kubeconfig isolation

### 5. Environment Utility (env-bootstrap.sh)

**Purpose**: Utility script to set KUBECONFIG and MK8_* environment variables for bootstrap cluster access

**Usage**:
```bash
# Source the utility to set KUBECONFIG and MK8_* env vars
source ./env-bootstrap.sh
# or
. ./env-bootstrap.sh

# Now kubectl commands will target the bootstrap cluster
kubectl get nodes
kubectl get pods -A

# And AWS credentials are available via MK8_* variables
./mk8-prototype.sh config
```

**Functionality**:
- Sets KUBECONFIG environment variable to point to `.config/mk8-bootstrap`
- Sources AWS credentials from configuration file:
  - First checks `~/.config/env-mk8-aws` (user's home directory - for real credentials)
  - Falls back to `.config/env-mk8-aws-template` (local template - for dummy values)
- Exports MK8_AWS_ACCESS_KEY_ID, MK8_AWS_SECRET_ACCESS_KEY, MK8_AWS_REGION
- Provides user feedback confirming the environment is configured
- Can be sourced multiple times safely
- Does not modify `~/.kube/config`

**Configuration File Lookup Priority**:
1. `~/.config/env-mk8-aws` (if exists) - Real credentials for integration testing
2. `.config/env-mk8-aws-template` (fallback) - Template with dummy values

**Template File Format** (`.config/env-mk8-aws-template`):
```bash
# AWS Credentials for mk8-prototype
# This is a template file with dummy values
# For real credentials, copy to ~/.config/env-mk8-aws and update values

export MK8_AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export MK8_AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export MK8_AWS_REGION="us-east-1"
```

**Example Output**:
```bash
$ source ./env-bootstrap.sh
[INFO] Loading AWS credentials from: ~/.config/env-mk8-aws
[INFO] KUBECONFIG set to: /path/to/prototype/.config/mk8-bootstrap
[INFO] MK8_AWS_* environment variables configured
[INFO] kubectl now points to mk8-bootstrap cluster
```

**Security**:
- Template file contains dummy values only
- Real credentials stored in home directory (`~/.config/env-mk8-aws`)
- Template name includes "template" to prevent accidental editing with real credentials

### 6. Crossplane Module (lib/crossplane.sh)

**Purpose**: Crossplane installation, configuration, and S3 bucket management

**Functions**:
```bash
crossplane_install()        # Install Crossplane via Helm
crossplane_status()         # Show Crossplane and AWS Provider status
create_aws_provider_config() # Create AWS ProviderConfig with credentials
verify_aws_provider()       # Verify AWS Provider is ready and configured
crossplane_create_s3()      # Create test S3 bucket via Crossplane MRD
crossplane_delete_s3()      # Delete test S3 bucket
generate_bucket_name()      # Generate unique bucket name with UUID
save_bucket_state()         # Save bucket name to state file
load_bucket_state()         # Load bucket name from state file
clear_bucket_state()        # Clear bucket state file
```

**Configuration**:
- Helm chart: `crossplane-stable/crossplane`
- Namespace: `crossplane-system`
- Release name: `crossplane`
- AWS Provider: `upbound/provider-aws-s3`
- State file: `~/.config/mk8-prototype-state`
- Bucket name format: `test-s3-bucket-<uuid>`

**S3 Bucket Management**:
- Only one bucket can exist at a time
- Bucket name tracked in `~/.config/mk8-prototype-state`
- UUID ensures uniqueness without excessive length
- Each create generates new UUID (even after delete)
- Verification via both Crossplane MRD status and AWS CLI

**Responsibilities**:
- Add Helm repository
- Install Crossplane chart
- Wait for pods to be ready
- Create AWS ProviderConfig with credentials from MK8_* env vars
- Verify AWS Provider is properly configured and can manage AWS resources
- Create/delete S3 buckets via Crossplane MRDs
- Verify bucket operations via Crossplane status and AWS CLI
- Manage bucket state in configuration file
- Display installation and operation status

## Data Models

### Environment Variables

```bash
# AWS Credentials (MK8_* prefix REQUIRED)
MK8_AWS_ACCESS_KEY_ID       # Required for AWS operations
MK8_AWS_SECRET_ACCESS_KEY   # Required for AWS operations
MK8_AWS_REGION              # Optional, defaults to us-east-1

# Cluster Configuration
MK8_CLUSTER_NAME            # Optional, defaults to mk8-bootstrap

# Kubeconfig (set by env-bootstrap.sh)
KUBECONFIG                  # Points to .config/mk8-bootstrap when sourced

# CRITICAL: Standard AWS variables must NEVER be used
# AWS_ACCESS_KEY_ID         # ❌ NEVER USE
# AWS_SECRET_ACCESS_KEY     # ❌ NEVER USE
# AWS_REGION                # ❌ NEVER USE
```

### State Files

```bash
# Bucket state tracking
~/.config/mk8-prototype-state     # Stores current S3 bucket name

# Kubeconfig storage
.config/mk8-bootstrap             # Isolated kubeconfig for bootstrap cluster

# AWS credentials configuration
.config/env-mk8-aws-template      # Template with dummy AWS credentials
~/.config/env-mk8-aws             # User's home directory credentials (takes precedence)
```

### Exit Codes

```bash
0   # Success
1   # General error
2   # Missing prerequisite
3   # Invalid arguments
4   # AWS credential error
5   # Cluster operation error
6   # Crossplane operation error
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Command routing correctness

*For any* valid command and subcommand combination, invoking the prototype script should route execution to the correct command handler function.

**Validates: Requirements 1.3**

### Property 2: Invalid command error handling

*For any* invalid or unknown command string, the prototype script should display an error message and exit with a non-zero status code.

**Validates: Requirements 1.2**

### Property 3: Missing environment variable detection

*For any* subset of required MK8_* environment variables that is incomplete, the config command should display an error message listing all missing variables.

**Validates: Requirements 2.4**

### Property 4: Cluster name consistency

*For any* sequence of bootstrap operations (create, status, delete), the system should use the same cluster name across all operations.

**Validates: Requirements 3.6**

### Property 5: Command execution transparency

*For any* external command executed by the system (kind, kubectl, helm, aws), the full command with all arguments should be displayed before execution.

**Validates: Requirements 5.1**

### Property 6: Error reporting completeness

*For any* error encountered during execution, the system should display both the error message and the command that failed.

**Validates: Requirements 5.4**

### Property 7: Kubeconfig isolation

*For any* bootstrap cluster operation, the system should never modify `~/.kube/config` and should always use an isolated kubeconfig file.

**Validates: Requirements 3.1, 3.3, 3.4**

### Property 8: AWS environment variable isolation

*For any* operation requiring AWS credentials, the system should only read from MK8_* prefixed environment variables and never use standard AWS_* variables.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 9: S3 bucket name uniqueness

*For any* sequence of S3 bucket creation operations (including create-delete-create cycles), each bucket should have a unique name with a different UUID.

**Validates: Requirements 4.6, 4.7**

### Property 10: State file consistency

*For any* S3 bucket that exists, the state file should contain the correct bucket name, and for any deleted bucket, the state file should be cleared.

**Validates: Requirements 4.6, 4.7**

## Error Handling

The prototype uses a simple error handling strategy:

### Error Detection
- Check exit codes of all external commands
- Validate environment variables before use
- Check for prerequisite commands (kind, kubectl, helm, aws)

### Error Reporting
- Display error message with context
- Show the command that failed
- Exit with appropriate exit code
- No automatic retry or recovery

### Error Categories

1. **Missing Prerequisites** (exit code 2)
   - Required command not found in PATH
   - Example: kind, kubectl, helm, aws CLI

2. **Invalid Arguments** (exit code 3)
   - Unknown command or subcommand
   - Missing required arguments

3. **AWS Credential Errors** (exit code 4)
   - Missing MK8_* environment variables
   - Invalid credentials (STS validation fails)

4. **Cluster Operation Errors** (exit code 5)
   - kind cluster creation fails
   - kind cluster deletion fails
   - kubectl commands fail

5. **Crossplane Operation Errors** (exit code 6)
   - Helm repository add fails
   - Helm install fails
   - Pod readiness timeout
   - ProviderConfig creation fails
   - AWS Provider not ready
   - S3 bucket creation/deletion fails
   - State file operations fail

### Example Error Messages

```bash
# Missing prerequisite
ERROR: Required command 'kind' not found in PATH
Please install kind: https://kind.sigs.k8s.io/docs/user/quick-start/

# Missing environment variable
ERROR: Missing required environment variables:
  - MK8_AWS_ACCESS_KEY_ID
  - MK8_AWS_SECRET_ACCESS_KEY
Please set these variables before running 'config' command

# Command failure
ERROR: Command failed with exit code 1
Command: kind create cluster --name mk8-bootstrap
```

## Testing Strategy

The prototype uses a pragmatic testing approach focused on integration testing rather than unit testing, given its nature as a simple bash script collection.

### Testing Approach

1. **Manual Integration Testing**
   - Primary testing method for the prototype
   - Test complete workflows end-to-end
   - Verify transparency (commands are logged)
   - Validate error handling

2. **Property-Based Testing (Not Applicable)**
   - Bash doesn't have mature property-based testing frameworks
   - Properties serve as manual test guidelines
   - Each property should be verified through integration tests

### Test Scenarios

#### CLI Parsing Tests
- Invoke with no arguments → displays usage
- Invoke with `--help` → displays help
- Invoke with unknown command → displays error
- Invoke with valid commands → routes correctly

#### AWS Credentials Tests
- All env vars set → validates successfully
- Missing env vars → displays error with list
- Invalid credentials → AWS STS fails with error
- Valid credentials → displays account info

#### Bootstrap Tests
- Create cluster → kind creates cluster successfully
- Status on existing cluster → displays cluster info
- Status on non-existent cluster → displays appropriate message
- Delete cluster → kind deletes cluster successfully
- Cluster name consistency → same name used throughout

#### Crossplane Tests
- Install without AWS credentials → installs Crossplane only
- Install with AWS credentials → installs Crossplane, creates ProviderConfig, verifies AWS Provider
- Status after install → displays pod and provider status
- Install when already installed → handles gracefully
- Create S3 bucket → generates unique name, applies MRD, verifies via Crossplane and AWS CLI
- Create S3 when one exists → displays error
- Delete S3 bucket → deletes MRD, verifies deletion, clears state
- Delete S3 when none exists → displays error
- Create-delete-create cycle → each bucket has unique UUID

#### Transparency Tests
- All commands logged before execution
- Helm chart details visible
- kubectl commands visible
- Crossplane MRD manifests visible
- Error messages include failed command

#### Isolation Tests
- Kubeconfig never merged into ~/.kube/config
- env-bootstrap.sh sets KUBECONFIG correctly
- kubectl uses isolated kubeconfig
- MK8_* env vars used exclusively
- Standard AWS_* vars never used
- State file tracks bucket correctly

### Test Execution

```bash
# Manual testing workflow
./mk8-prototype.sh                    # Test no args
./mk8-prototype.sh --help             # Test help
./mk8-prototype.sh invalid            # Test invalid command
./mk8-prototype.sh version            # Test version

# Test config
export MK8_AWS_ACCESS_KEY_ID=test
export MK8_AWS_SECRET_ACCESS_KEY=test
export MK8_AWS_REGION=us-east-1
./mk8-prototype.sh config             # Test with env vars

# Test bootstrap
./mk8-prototype.sh bootstrap create   # Test cluster creation
./mk8-prototype.sh bootstrap status   # Test status
./mk8-prototype.sh bootstrap delete   # Test deletion

# Test crossplane
./mk8-prototype.sh crossplane install  # Test installation
./mk8-prototype.sh crossplane status   # Test status
./mk8-prototype.sh crossplane create-s3 # Test S3 creation
./mk8-prototype.sh crossplane delete-s3 # Test S3 deletion

# Test environment utility
source ./env-bootstrap.sh              # Set KUBECONFIG
kubectl get nodes                      # Verify kubectl works
```

### Testing Priorities

1. **High Priority**
   - CLI parsing and routing
   - Error handling for missing prerequisites
   - Error handling for missing env vars
   - Command transparency (logging)

2. **Medium Priority**
   - AWS credential validation
   - Bootstrap cluster operations
   - Crossplane installation

3. **Low Priority**
   - Edge cases and error recovery
   - Performance testing
   - Stress testing

### Testing Limitations

- Integration tests require actual tools (kind, kubectl, helm, aws)
- Tests require AWS credentials for full workflow validation
- Tests create actual resources (clusters, pods, S3 buckets)
- No automated test framework - manual testing only

## Implementation Notes

### Script Structure

Each script follows a consistent structure:

```bash
#!/usr/bin/env bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Source dependencies
source "$(dirname "$0")/lib/common.sh"

# Function definitions
function_name() {
    local arg1="$1"
    # Implementation
}

# Main execution (if script is run directly)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Logging Format

```bash
# Info messages (blue)
[INFO] Creating bootstrap cluster...

# Success messages (green)
[SUCCESS] Cluster created successfully

# Error messages (red)
[ERROR] Command failed: kind create cluster

# Command logging (yellow)
[CMD] kind create cluster --name mk8-bootstrap
```

### Configuration Defaults

```bash
# Cluster configuration
CLUSTER_NAME="${MK8_CLUSTER_NAME:-mk8-bootstrap}"
CONFIG_DIR=".config"
KUBECONFIG_FILE="${CONFIG_DIR}/mk8-bootstrap"

# AWS credentials configuration files (priority: home > template)
AWS_ENV_HOME="${HOME}/.config/env-mk8-aws"
AWS_ENV_TEMPLATE="${CONFIG_DIR}/env-mk8-aws-template"

# AWS configuration (MK8_* prefix required)
AWS_REGION="${MK8_AWS_REGION:-us-east-1}"

# Crossplane configuration
CROSSPLANE_NAMESPACE="crossplane-system"
CROSSPLANE_RELEASE="crossplane"
CROSSPLANE_CHART="crossplane-stable/crossplane"
CROSSPLANE_VERSION="1.14.0"
AWS_PROVIDER="upbound/provider-aws-s3"
PROVIDER_CONFIG_NAME="default"

# S3 bucket configuration
STATE_FILE="${HOME}/.config/mk8-prototype-state"
BUCKET_PREFIX="test-s3-bucket"
```

### Prerequisite Checking

```bash
# Check for required commands
check_prereq "kind"
check_prereq "kubectl"
check_prereq "helm"
check_prereq "aws"
```

### Command Execution Pattern

```bash
# Log command before execution
log_command "kind create cluster --name $CLUSTER_NAME --kubeconfig $KUBECONFIG_FILE"

# Execute command
if kind create cluster --name "$CLUSTER_NAME" --kubeconfig "$KUBECONFIG_FILE"; then
    log_success "Cluster created successfully"
else
    log_error "Failed to create cluster"
fi
```

### AWS CLI Execution Pattern

```bash
# Temporarily map MK8_* to AWS_* in subshell
with_mk8_aws_env() {
    local cmd="$@"
    (
        export AWS_ACCESS_KEY_ID="$MK8_AWS_ACCESS_KEY_ID"
        export AWS_SECRET_ACCESS_KEY="$MK8_AWS_SECRET_ACCESS_KEY"
        export AWS_REGION="$MK8_AWS_REGION"
        eval "$cmd"
    )
    # Standard AWS_* vars automatically unset when subshell exits
}

# Usage
log_command "aws sts get-caller-identity"
with_mk8_aws_env "aws sts get-caller-identity"
```

### Kubectl Execution Pattern

```bash
# Always use isolated kubeconfig
kubectl --kubeconfig "$KUBECONFIG_FILE" get nodes

# Or set KUBECONFIG for multiple commands
export KUBECONFIG="$KUBECONFIG_FILE"
kubectl get nodes
kubectl get pods -A
```

## Future Enhancements

The prototype is intentionally minimal, but potential enhancements include:

1. **Configuration File Support**
   - Read settings from `.mk8-prototype.conf`
   - Override with environment variables

2. **Verbose Mode**
   - Add `-v` flag for even more detailed output
   - Show kubectl/helm output in real-time

3. **Dry Run Mode**
   - Add `--dry-run` flag to show commands without executing
   - Useful for learning and debugging

4. **Custom kind Configuration**
   - Support custom kind config files
   - Configure node count, Kubernetes version, etc.

5. **Provider Configuration**
   - Support multiple cloud providers (Azure, GCP)
   - Configurable provider installation

These enhancements should maintain the prototype's core principles of simplicity and transparency.
