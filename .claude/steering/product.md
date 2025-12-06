# Product Overview

## What is mk8?

mk8 is a command-line tool for managing Kubernetes infrastructure on AWS using a multi-tier cluster architecture powered by Crossplane. It simplifies the complex process of setting up and managing Kubernetes clusters on AWS by providing an automated, infrastructure-as-code approach.

## Target Audience

**Primary Users**: Platform engineers, DevOps engineers, and infrastructure teams who need to:
- Provision and manage multiple Kubernetes clusters on AWS
- Implement infrastructure as code for Kubernetes
- Separate management concerns from application workloads
- Bootstrap AWS infrastructure using local development tools

**Use Cases**:
- Creating development, staging, and production Kubernetes environments on AWS
- Implementing GitOps workflows for cluster management
- Managing multi-tenant Kubernetes infrastructures
- Rapid prototyping and testing of cluster configurations

## Architecture

mk8 implements a three-tier cluster architecture:

### 1. Bootstrap Cluster (Local)
- **Purpose**: Temporary local Kubernetes cluster for bootstrapping AWS infrastructure
- **Technology**: kind (Kubernetes in Docker)
- **Lifetime**: Created when needed, destroyed after management cluster is provisioned
- **Components**: Crossplane with AWS provider and credentials

### 2. Management Cluster (AWS)
- **Purpose**: Control plane for managing workload clusters
- **Technology**: AWS EKS
- **Provisioning**: Created by bootstrap cluster via Crossplane
- **Responsibilities**: Manages lifecycle of workload clusters, houses operational tools

### 3. Workload Clusters (AWS)
- **Purpose**: Run application workloads
- **Technology**: AWS EKS
- **Provisioning**: Created and managed by management cluster
- **Isolation**: Separate clusters for different environments or tenants

## Key Features

### Current (v0.1.0)
- **CLI Framework**: Modern, kubectl-like command structure with hierarchical help
- **Bootstrap Management**: Create, delete, and check status of local bootstrap clusters
- **AWS Integration**: Secure credential management with interactive configuration
- **Error Handling**: Clear, actionable error messages with suggestions
- **Logging**: Verbose and normal modes for debugging and production use

### Planned
- **Bootstrap Operations**:
  - Automatic Crossplane installation and configuration
  - AWS provider setup with credential validation
  - Cluster readiness verification

- **AWS Credentials Management**:
  - Multiple input methods (env vars, interactive prompts, config file)
  - Secure storage in `~/.config/mk8`
  - Automatic synchronization with Crossplane

- **kubectl Integration**:
  - Safe merging with existing kubeconfig
  - Context management and switching
  - Cleanup without disrupting other clusters

- **Management Cluster Provisioning**:
  - Infrastructure-as-code definitions
  - VPC and networking setup
  - EKS cluster creation
  - Operational tooling installation

## Value Proposition

mk8 reduces the complexity of Kubernetes infrastructure management on AWS by:
1. **Automating repetitive tasks**: No manual clicking through AWS console
2. **Ensuring consistency**: Infrastructure defined as code
3. **Reducing errors**: Validation and clear error messages throughout
4. **Enabling rapid iteration**: Quick setup and teardown of environments
5. **Separation of concerns**: Distinct clusters for management vs. workloads

## Development Status

- **Version**: 0.1.0 (Alpha)
- **License**: Apache 2.0
- **Stage**: Active development
- **Stability**: CLI framework complete, feature implementation in progress
