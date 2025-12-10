# mk8-prototype

A minimal, transparent bash-based reference implementation of mk8's core functionality.

## Overview

mk8-prototype is a simple, educational implementation that demonstrates the essential workflows of managing Kubernetes infrastructure on AWS using Crossplane. Unlike the production Python implementation, this prototype prioritizes readability, transparency, and visibility of underlying operations.

## Features

- **CLI Framework**: Command-line interface with help, version, and command routing
- **AWS Credential Management**: Secure handling of AWS credentials with environment variable isolation
- **Bootstrap Cluster Management**: Local kind cluster lifecycle management with isolated kubeconfig
- **Crossplane Installation**: Automated Crossplane installation via Helm with AWS Provider configuration
- **S3 Bucket Management**: Create and delete S3 buckets via Crossplane Managed Resource Definitions (MRDs)
- **Environment Utility**: Helper script to set up KUBECONFIG and AWS credentials

## Prerequisites

Before using mk8-prototype, ensure you have the following tools installed:

- **kind** - Kubernetes IN Docker for local clusters
  - Installation: https://kind.sigs.k8s.io/docs/user/quick-start/
- **kubectl** - Kubernetes command-line tool
  - Installation: https://kubernetes.io/docs/tasks/tools/
- **helm** - Kubernetes package manager
  - Installation: https://helm.sh/docs/intro/install/
- **aws** - AWS CLI for credential validation and S3 verification
  - Installation: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

## Quick Start

### 1. Set Up Environment

First, configure your environment with AWS credentials and KUBECONFIG:

```bash
# Source the environment utility to set up KUBECONFIG and AWS credentials
source ./env-bootstrap.sh
```

This will:
- Set KUBECONFIG to point to the bootstrap cluster
- Load AWS credentials from configuration files
- Display environment status

### 2. Configure AWS Credentials

Set up your AWS credentials using MK8_* prefixed environment variables:

```bash
# Copy the template and edit with your real credentials
cp .config/env-mk8-aws-template ~/.config/env-mk8-aws
chmod 600 ~/.config/env-mk8-aws
# Edit ~/.config/env-mk8-aws with your real AWS credentials

# Validate your credentials
./mk8-prototype.sh config
```

### 3. Create Bootstrap Cluster

Create a local Kubernetes cluster using kind:

```bash
./mk8-prototype.sh bootstrap create
```

### 4. Install Crossplane

Install Crossplane and configure the AWS Provider:

```bash
./mk8-prototype.sh crossplane install
```

### 5. Create S3 Bucket

Create a test S3 bucket via Crossplane:

```bash
./mk8-prototype.sh crossplane create-s3
```

### 6. Clean Up

When you're done, clean up the resources:

```bash
# Delete the S3 bucket
./mk8-prototype.sh crossplane delete-s3

# Delete the bootstrap cluster
./mk8-prototype.sh bootstrap delete
```

## Commands

### Main Commands

- `./mk8-prototype.sh version` - Display version information
- `./mk8-prototype.sh help` - Display help information
- `./mk8-prototype.sh config` - Validate AWS credentials

### Bootstrap Cluster Management

- `./mk8-prototype.sh bootstrap create` - Create local kind cluster
- `./mk8-prototype.sh bootstrap status` - Show cluster status
- `./mk8-prototype.sh bootstrap delete` - Delete cluster

### Crossplane Management

- `./mk8-prototype.sh crossplane install` - Install Crossplane and AWS Provider
- `./mk8-prototype.sh crossplane status` - Show Crossplane status
- `./mk8-prototype.sh crossplane create-s3` - Create S3 bucket
- `./mk8-prototype.sh crossplane delete-s3` - Delete S3 bucket

## Environment Variables

### Required for AWS Operations

- `MK8_AWS_ACCESS_KEY_ID` - AWS access key ID
- `MK8_AWS_SECRET_ACCESS_KEY` - AWS secret access key
- `MK8_AWS_REGION` - AWS region (default: us-east-1)

### Optional Configuration

- `MK8_CLUSTER_NAME` - Bootstrap cluster name (default: mk8-bootstrap)

### Important Notes

- **Never use standard AWS environment variables** (AWS_ACCESS_KEY_ID, etc.)
- The prototype uses MK8_* prefixed variables for complete isolation
- Standard AWS_* variables are only set temporarily within subshells when calling AWS CLI

## Configuration Files

### AWS Credentials

The prototype looks for AWS credentials in this order:

1. `~/.config/env-mk8-aws` - Your real credentials (recommended)
2. `.config/env-mk8-aws-template` - Template with dummy values

### Template Format

```bash
# AWS Credentials for mk8-prototype
export MK8_AWS_ACCESS_KEY_ID="your-access-key-here"
export MK8_AWS_SECRET_ACCESS_KEY="your-secret-key-here"
export MK8_AWS_REGION="us-east-1"
```

### Kubeconfig Isolation

- Bootstrap cluster kubeconfig: `.config/mk8-bootstrap`
- **Never modifies** `~/.kube/config`
- Use `source ./env-bootstrap.sh` to set KUBECONFIG automatically

## Architecture

The prototype follows a simple, modular architecture:

```
mk8-prototype.sh          # Main CLI entry point
├── lib/
│   ├── common.sh         # Shared utilities and logging
│   ├── config.sh         # AWS credential management
│   ├── bootstrap.sh      # kind cluster operations
│   └── crossplane.sh     # Crossplane and S3 operations
├── .config/
│   ├── mk8-bootstrap     # Isolated kubeconfig (created by bootstrap)
│   └── env-mk8-aws-template  # AWS credentials template
└── env-bootstrap.sh      # Environment setup utility
```

### Design Principles

1. **Transparency First** - Every external command is logged before execution
2. **Minimal Abstraction** - Direct invocation of tools with minimal wrapper logic
3. **Isolation** - Complete separation from user's existing configurations
4. **Fail Fast** - Simple error checking without complex recovery logic
5. **Self-Documenting** - Code comments explain what and why, not just how

## Testing

The prototype includes comprehensive unit tests using BATS (Bash Automated Testing System).

### Running Tests

```bash
# Run all tests (unit tests + shellcheck)
./run-tests.sh all

# Run only unit tests
./run-tests.sh unit

# Run only shellcheck static analysis
./run-tests.sh shellcheck
```

### Test Coverage

- **CLI Framework**: Argument parsing, command routing, help/version display
- **Common Utilities**: Logging functions, prerequisite checking, error handling
- **AWS Configuration**: Credential validation, environment variable isolation
- **Bootstrap Management**: Cluster lifecycle, kubeconfig isolation
- **Crossplane Operations**: Installation, AWS Provider configuration, status display
- **S3 Management**: Bucket creation/deletion, state management, UUID generation
- **Environment Utility**: KUBECONFIG setup, credential sourcing

## Troubleshooting

### Common Issues

#### "Bootstrap cluster kubeconfig not found"

```bash
# Create the bootstrap cluster first
./mk8-prototype.sh bootstrap create
```

#### "Missing required environment variables"

```bash
# Set up AWS credentials
cp .config/env-mk8-aws-template ~/.config/env-mk8-aws
# Edit ~/.config/env-mk8-aws with real credentials
source ./env-bootstrap.sh
```

#### "Docker is not running"

```bash
# Start Docker Desktop or Docker daemon
sudo systemctl start docker  # Linux
# or start Docker Desktop application
```

#### "Command not found: kind/kubectl/helm/aws"

Install the missing prerequisite tools. See the Prerequisites section for installation links.

#### "AWS credentials validation failed"

```bash
# Check your credentials
./mk8-prototype.sh config

# Verify AWS CLI access
aws sts get-caller-identity
```

#### "S3 bucket already exists"

```bash
# Delete the existing bucket first
./mk8-prototype.sh crossplane delete-s3

# Then create a new one
./mk8-prototype.sh crossplane create-s3
```

### Debug Mode

For detailed debugging, you can run commands with bash debug mode:

```bash
bash -x ./mk8-prototype.sh <command>
```

### Log Output

All operations are logged with prefixes:
- `[INFO]` - Informational messages
- `[SUCCESS]` - Success messages
- `[ERROR]` - Error messages
- `[CMD]` - Commands being executed
- `[WARN]` - Warning messages

## Limitations

This is a prototype implementation with intentional limitations:

- **Single S3 bucket** - Only one bucket can exist at a time
- **Basic error handling** - No automatic retry or complex recovery
- **No production hardening** - Focused on transparency over robustness
- **Limited AWS services** - Only S3 buckets via Crossplane
- **Local clusters only** - Uses kind for local development

## Comparison with Production mk8

| Feature | Prototype | Production mk8 |
|---------|-----------|----------------|
| Language | Bash | Python |
| Error Handling | Basic | Comprehensive |
| Testing | Unit tests | Unit + Integration + Property-based |
| AWS Services | S3 only | Full AWS service support |
| Cluster Types | kind only | Multiple cluster types |
| Configuration | Environment variables | Multiple config sources |
| Logging | Simple prefixed output | Structured logging |
| Documentation | README | Full documentation site |

## Contributing

This prototype is designed for educational purposes. For production use cases, please use the main mk8 Python implementation.

### Development Workflow

1. Make changes to the bash scripts
2. Run tests: `./run-tests.sh all`
3. Ensure all tests pass
4. Update documentation if needed

### Code Style

- Use `set -euo pipefail` in all scripts
- Log all external commands before execution
- Include error messages with suggestions
- Follow the existing function naming conventions
- Add unit tests for new functionality

## License

Apache License 2.0 - See LICENSE file for details.

## Support

This is a prototype implementation. For production support, please refer to the main mk8 project documentation.