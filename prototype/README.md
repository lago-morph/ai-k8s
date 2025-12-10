# mk8-prototype

A minimal, transparent bash-based reference implementation of mk8's core functionality.

## Overview

The mk8-prototype is designed for Kubernetes experts who want to understand, debug, and modify the underlying operations of mk8. Unlike the production Python implementation, this prototype prioritizes:

- **Transparency**: Every command is logged before execution
- **Simplicity**: Minimal abstraction between user commands and underlying tools
- **Debuggability**: Easy to understand and modify bash scripts
- **Isolation**: Separate kubeconfig and AWS credentials to avoid conflicts

## Features

- ✅ CLI command parsing and routing
- ✅ AWS credential validation (isolated from standard AWS CLI config)
- ✅ Local kind cluster lifecycle management (isolated kubeconfig)
- ✅ Crossplane installation via Helm
- ✅ AWS Provider configuration
- ✅ S3 bucket creation/deletion via Crossplane MRDs

## Prerequisites

The following tools must be installed and available in your PATH:

- **kind** - Kubernetes IN Docker ([installation guide](https://kind.sigs.k8s.io/docs/user/quick-start/))
- **kubectl** - Kubernetes CLI ([installation guide](https://kubernetes.io/docs/tasks/tools/))
- **helm** - Kubernetes package manager ([installation guide](https://helm.sh/docs/intro/install/))
- **aws** - AWS CLI ([installation guide](https://aws.amazon.com/cli/))
- **Docker** - Container runtime (required by kind)

## Quick Start

### 1. Set Up Environment

The prototype uses isolated configurations to avoid interfering with your existing setup:

```bash
# Source the environment utility to set KUBECONFIG and AWS credentials
source ./env-bootstrap.sh
```

This will:
- Set `KUBECONFIG` to point to `.config/mk8-bootstrap` (isolated from `~/.kube/config`)
- Load AWS credentials from `~/.config/env-mk8-aws` (or template if not found)
- Export `MK8_AWS_*` environment variables (isolated from standard `AWS_*` variables)

### 2. Configure AWS Credentials

The prototype uses `MK8_*` prefixed environment variables to avoid conflicts with your existing AWS CLI configuration:

```bash
# Copy the template to your home directory
cp .config/env-mk8-aws-template ~/.config/env-mk8-aws

# Secure the file
chmod 600 ~/.config/env-mk8-aws

# Edit with your real AWS credentials
nano ~/.config/env-mk8-aws
```

Edit the file and replace the dummy values:
```bash
export MK8_AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_HERE"
export MK8_AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY_HERE"
export MK8_AWS_REGION="us-east-1"
```

Then source the environment utility again:
```bash
source ./env-bootstrap.sh
```

### 3. Validate AWS Credentials

```bash
./mk8-prototype.sh config
```

This will validate your credentials and display your AWS account information.

### 4. Create Bootstrap Cluster

```bash
./mk8-prototype.sh bootstrap create
```

This creates a local kind cluster with an isolated kubeconfig. You can now use kubectl:

```bash
kubectl get nodes
kubectl get pods -A
```

### 5. Install Crossplane

```bash
./mk8-prototype.sh crossplane install
```

This will:
- Add the Crossplane Helm repository
- Install Crossplane in the `crossplane-system` namespace
- Wait for Crossplane pods to be ready
- Install the AWS S3 Provider
- Create an AWS ProviderConfig with your credentials
- Verify the AWS Provider is ready

### 6. Create a Test S3 Bucket

```bash
./mk8-prototype.sh crossplane create-s3
```

This creates an S3 bucket via Crossplane and verifies it was created in AWS.

### 7. Clean Up

```bash
# Delete the S3 bucket
./mk8-prototype.sh crossplane delete-s3

# Delete the bootstrap cluster
./mk8-prototype.sh bootstrap delete
```

## Usage

### Commands

```bash
./mk8-prototype.sh <command> [subcommand] [options]
```

#### Version and Help

```bash
./mk8-prototype.sh version      # Display version information
./mk8-prototype.sh help         # Display help information
```

#### AWS Configuration

```bash
./mk8-prototype.sh config       # Validate AWS credentials
```

Requires `MK8_AWS_ACCESS_KEY_ID` and `MK8_AWS_SECRET_ACCESS_KEY` environment variables.

#### Bootstrap Cluster Management

```bash
./mk8-prototype.sh bootstrap create    # Create local kind cluster
./mk8-prototype.sh bootstrap status    # Show cluster status
./mk8-prototype.sh bootstrap delete    # Delete cluster
```

The cluster is created with an isolated kubeconfig at `.config/mk8-bootstrap`.

#### Crossplane Management

```bash
./mk8-prototype.sh crossplane install    # Install Crossplane and AWS Provider
./mk8-prototype.sh crossplane status     # Show Crossplane status
./mk8-prototype.sh crossplane create-s3  # Create test S3 bucket
./mk8-prototype.sh crossplane delete-s3  # Delete test S3 bucket
```

### Environment Variables

The prototype uses `MK8_*` prefixed variables to isolate from your existing AWS configuration:

- `MK8_AWS_ACCESS_KEY_ID` - AWS access key (required for AWS operations)
- `MK8_AWS_SECRET_ACCESS_KEY` - AWS secret access key (required for AWS operations)
- `MK8_AWS_REGION` - AWS region (default: us-east-1)
- `MK8_CLUSTER_NAME` - Cluster name (default: mk8-bootstrap)

**Important**: The prototype NEVER uses standard `AWS_*` environment variables. This ensures complete isolation from your existing AWS CLI configuration.

### Environment Utility Script

The `env-bootstrap.sh` utility script sets up your environment for working with the prototype:

```bash
# Source the utility (must be sourced, not executed)
source ./env-bootstrap.sh
```

This script:
1. Sets `KUBECONFIG` to `.config/mk8-bootstrap`
2. Loads AWS credentials from:
   - `~/.config/env-mk8-aws` (if exists - for real credentials)
   - `.config/env-mk8-aws-template` (fallback - for dummy values)
3. Exports `MK8_AWS_*` environment variables
4. Displays confirmation messages

After sourcing, you can use kubectl directly:
```bash
kubectl get nodes
kubectl get pods -A
```

## Configuration Files

### Kubeconfig Isolation

The prototype stores the bootstrap cluster kubeconfig in:
```
.config/mk8-bootstrap
```

This file is NEVER merged into `~/.kube/config`, ensuring complete isolation from your existing Kubernetes configurations.

### AWS Credentials

The prototype looks for AWS credentials in this order:

1. `~/.config/env-mk8-aws` (user's home directory - for real credentials)
2. `.config/env-mk8-aws-template` (local template - for dummy values)

The template file is included in the repository with dummy values. Copy it to your home directory and edit with real credentials:

```bash
cp .config/env-mk8-aws-template ~/.config/env-mk8-aws
chmod 600 ~/.config/env-mk8-aws
# Edit with your real credentials
```

### State Files

The prototype tracks S3 bucket state in:
```
~/.config/mk8-prototype-state
```

This file stores the name of the currently managed S3 bucket (only one bucket at a time is supported).

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
│   ├── mk8-bootstrap         # Isolated kubeconfig (created by bootstrap)
│   └── env-mk8-aws-template  # Template for MK8_* environment variables
├── tests/
│   ├── unit/                 # Unit tests (BATS)
│   └── test_helper.bash      # Test helper functions
├── run-tests.sh              # Test runner script
└── README.md                 # This file
```

### Design Principles

1. **Transparency First**: Every external command is logged before execution
2. **Minimal Abstraction**: Direct invocation of tools with minimal wrapper logic
3. **Single Responsibility**: Each script handles one domain (config, bootstrap, crossplane)
4. **Fail Fast**: Simple error checking without complex recovery logic
5. **Self-Documenting**: Code comments explain what and why, not just how

## Testing

The prototype includes comprehensive unit tests using BATS (Bash Automated Testing System).

### Running Tests

```bash
# Run all unit tests
./run-tests.sh

# Run specific test file
./run-tests.sh tests/unit/test_cli.bats

# Run with verbose output
./run-tests.sh -v
```

### Static Analysis

The prototype uses shellcheck for static analysis:

```bash
# Check all scripts
shellcheck mk8-prototype.sh env-bootstrap.sh lib/*.sh

# Check with specific configuration
shellcheck --shell=bash --external-sources mk8-prototype.sh
```

Configuration is in `.shellcheckrc`.

## Exit Codes

The prototype uses specific exit codes for different error conditions:

- `0` - Success
- `1` - General error
- `2` - Missing prerequisite (command not found)
- `3` - Invalid arguments (unknown command or subcommand)
- `4` - AWS credential error (missing or invalid credentials)
- `5` - Cluster operation error (kind or kubectl failure)
- `6` - Crossplane operation error (Helm, Crossplane, or S3 failure)

## Troubleshooting

### "Required command not found"

Install the missing prerequisite tool. See the [Prerequisites](#prerequisites) section for installation guides.

### "Missing required environment variables"

Set the required `MK8_AWS_*` environment variables. See the [Configure AWS Credentials](#2-configure-aws-credentials) section.

### "Cluster already exists"

Delete the existing cluster first:
```bash
./mk8-prototype.sh bootstrap delete
```

### "kubectl: command not found" after sourcing env-bootstrap.sh

Make sure you sourced the script (not executed it):
```bash
source ./env-bootstrap.sh  # Correct
./env-bootstrap.sh         # Wrong - will not set environment variables
```

### "AWS credentials are invalid"

Verify your credentials are correct:
```bash
# Check what's loaded
echo $MK8_AWS_ACCESS_KEY_ID
echo $MK8_AWS_REGION

# Test with AWS CLI directly (temporarily map variables)
AWS_ACCESS_KEY_ID=$MK8_AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=$MK8_AWS_SECRET_ACCESS_KEY \
AWS_REGION=$MK8_AWS_REGION \
aws sts get-caller-identity
```

### "S3 bucket already exists"

Delete the existing bucket first:
```bash
./mk8-prototype.sh crossplane delete-s3
```

### Crossplane pods not ready

Check pod status:
```bash
kubectl get pods -n crossplane-system
kubectl describe pod -n crossplane-system <pod-name>
```

Wait longer for pods to be ready (can take 2-3 minutes on first install).

### AWS Provider not ready

Check provider status:
```bash
kubectl get providers
kubectl describe provider upbound-provider-aws-s3
```

Verify your AWS credentials are correct and have necessary permissions.

## Examples

### Complete Workflow

```bash
# 1. Set up environment
source ./env-bootstrap.sh

# 2. Validate AWS credentials
./mk8-prototype.sh config

# 3. Create bootstrap cluster
./mk8-prototype.sh bootstrap create

# 4. Check cluster status
./mk8-prototype.sh bootstrap status
kubectl get nodes

# 5. Install Crossplane
./mk8-prototype.sh crossplane install

# 6. Check Crossplane status
./mk8-prototype.sh crossplane status
kubectl get pods -n crossplane-system

# 7. Create S3 bucket
./mk8-prototype.sh crossplane create-s3

# 8. Verify bucket in AWS
aws s3 ls | grep test-s3-bucket

# 9. Check bucket status in Crossplane
kubectl get buckets

# 10. Clean up
./mk8-prototype.sh crossplane delete-s3
./mk8-prototype.sh bootstrap delete
```

### Using kubectl Directly

After sourcing `env-bootstrap.sh`, you can use kubectl directly:

```bash
source ./env-bootstrap.sh

# View all resources
kubectl get all -A

# View Crossplane resources
kubectl get providers
kubectl get providerconfigs
kubectl get buckets

# View logs
kubectl logs -n crossplane-system -l app=crossplane

# Describe resources
kubectl describe bucket <bucket-name>
```

### Testing AWS Provider Configuration

```bash
# Check if Provider is installed and healthy
kubectl get providers

# Check if ProviderConfig is created
kubectl get providerconfigs

# View Provider details
kubectl describe provider upbound-provider-aws-s3

# View ProviderConfig details
kubectl describe providerconfig default

# Check Provider pod logs
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=upbound-provider-aws-s3
```

## Limitations

The prototype is intentionally minimal and has several limitations:

1. **Single S3 Bucket**: Only one S3 bucket can be managed at a time
2. **No Error Recovery**: Simple error handling without automatic retry or recovery
3. **Limited AWS Resources**: Only S3 buckets are supported (no VPCs, EC2, etc.)
4. **No Configuration Files**: All configuration via environment variables
5. **Manual Testing**: No automated integration tests (unit tests only)
6. **Basic Logging**: Simple command logging without detailed debugging options

These limitations are by design to keep the prototype simple and understandable.

## Comparison with Production mk8

| Feature | Prototype | Production mk8 |
|---------|-----------|----------------|
| Language | Bash | Python |
| Error Handling | Basic | Comprehensive |
| Testing | Unit tests (BATS) | Unit + Integration + Property tests |
| Logging | Simple command logging | Structured logging with levels |
| Configuration | Environment variables | Config files + env vars |
| AWS Resources | S3 only | Full AWS resource support |
| Robustness | Minimal | Production-grade |
| Transparency | Maximum | Configurable |
| Use Case | Learning, debugging | Production deployments |

## Contributing

The prototype is a reference implementation and is not intended for production use. However, contributions to improve clarity, fix bugs, or add documentation are welcome.

### Development Workflow

1. Make changes to bash scripts
2. Run shellcheck for static analysis
3. Run unit tests with BATS
4. Test manually with real AWS credentials
5. Update documentation if needed

### Code Style

- Use `set -euo pipefail` in all scripts
- Log all external commands before execution
- Use descriptive variable names
- Add comments for non-obvious logic
- Follow existing patterns for consistency

## License

See the LICENSE file in the root of the repository.

## Related Documentation

- [mk8 Main README](../README.md) - Production Python implementation
- [Requirements Document](.claude/specs/prototype/requirements.md) - Detailed requirements
- [Design Document](.claude/specs/prototype/design.md) - Architecture and design decisions
- [Tasks Document](.claude/specs/prototype/tasks.md) - Implementation plan

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [Examples](#examples) section
3. Read the source code (it's designed to be readable!)
4. Check the design and requirements documents

The prototype is a learning tool - reading and understanding the code is encouraged!
