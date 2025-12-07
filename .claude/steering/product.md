# Product Overview

## What is mk8?

mk8 is a command-line tool for managing Kubernetes infrastructure on AWS using a multi-tier cluster architecture powered by Crossplane. It simplifies the complex process of setting up and managing Kubernetes clusters on AWS by providing an automated, infrastructure-as-code approach with GitOps workflows.

## Target Audience

**Primary Users**: Platform engineers, DevOps engineers, and infrastructure teams who need to:
- Provision and manage multiple Kubernetes clusters on AWS
- Implement infrastructure as code for Kubernetes using Crossplane
- Separate management concerns from application workloads
- Bootstrap AWS infrastructure using local development tools
- Learn Crossplane and GitOps patterns through hands-on tutorials

**Use Cases**:
- Creating development, staging, and production Kubernetes environments on AWS
- Implementing GitOps workflows for cluster and application management
- Managing multi-tenant Kubernetes infrastructures
- Rapid prototyping and testing of cluster configurations
- Learning Crossplane through guided tutorials

## Architecture

mk8 implements a three-tier cluster architecture:

### 1. Bootstrap Cluster (Local)
- **Purpose**: Temporary local Kubernetes cluster for bootstrapping AWS infrastructure
- **Technology**: kind (Kubernetes in Docker)
- **Lifetime**: Created when needed, can be kept for development/learning
- **Components**: Crossplane with AWS provider, credentials, and ProviderConfig
- **Status**: ✅ Fully implemented and operational

### 2. Management Cluster (AWS)
- **Purpose**: Control plane for managing workload clusters
- **Technology**: AWS EKS
- **Provisioning**: Created by bootstrap cluster via Crossplane
- **Responsibilities**: Manages lifecycle of workload clusters, houses ArgoCD and operational tools
- **Status**: 📋 Planned

### 3. Workload Clusters (AWS)
- **Purpose**: Run application workloads
- **Technology**: AWS EKS
- **Provisioning**: Created and managed by management cluster via GitOps
- **Isolation**: Separate clusters for different environments or tenants
- **Status**: 📋 Planned

## Key Features

### Current (v0.1.0)

**Foundation (100% Complete)**:
- ✅ **CLI Framework**: Modern, kubectl-like command structure with hierarchical help
- ✅ **Prerequisite Verification**: Automatic checking of Docker, kind, kubectl with installation instructions
- ✅ **AWS Credentials Management**: Interactive configuration, validation, secure storage, Crossplane synchronization
- ✅ **Kubeconfig Management**: Safe merging, atomic updates, automatic backups, conflict resolution
- ✅ **Error Handling**: Clear, actionable error messages with suggestions
- ✅ **Logging**: Verbose and normal modes for debugging and production use

**Bootstrap Cluster (100% Complete)**:
- ✅ **Local Kind Cluster**: Create, delete, status commands with safety-first design
- ✅ **Crossplane Installation**: Helm-based installation with version selection
- ✅ **AWS Provider Setup**: Automatic provider installation and configuration
- ✅ **Credential Integration**: Automatic AWS secret creation and ProviderConfig setup
- ✅ **Status Reporting**: Comprehensive cluster and Crossplane status information

**Documentation & Tutorials (In Progress)**:
- 🚧 **Tutorial System**: Hands-on tutorials for learning Crossplane and mk8
- 🚧 **Tutorial 01**: Create S3 bucket using Crossplane on bootstrap cluster (96% complete)

### Planned Features

**GitOps & ArgoCD**:
- 📋 **GitOps Repository Setup**: Structured repository for Helm-based GitOps workflows
- 📋 **ArgoCD Bootstrap**: ArgoCD installation and configuration on management cluster
- 📋 **Environment Promotion**: Safe testing of ArgoCD CRD changes across dev/staging/prod
- 📋 **Static Analysis**: Schema validation and safety policies for ArgoCD CRDs

**Management Cluster**:
- 📋 **EKS Provisioning**: Management cluster creation via Crossplane from bootstrap cluster
- 📋 **Operational Tooling**: ArgoCD, monitoring, logging setup
- 📋 **Workload Cluster Management**: Declarative cluster lifecycle management

**Workload Clusters**:
- 📋 **Multi-Environment Support**: Dev, staging, production cluster management
- 📋 **Canary Deployments**: Safe rollout of infrastructure changes
- 📋 **Application Deployment**: GitOps-based application workflows

## Value Proposition

mk8 reduces the complexity of Kubernetes infrastructure management on AWS by:
1. **Automating repetitive tasks**: No manual clicking through AWS console
2. **Ensuring consistency**: Infrastructure defined as code with Crossplane
3. **Reducing errors**: Validation and clear error messages throughout
4. **Enabling rapid iteration**: Quick setup and teardown of environments
5. **Separation of concerns**: Distinct clusters for management vs. workloads
6. **Learning by doing**: Comprehensive tutorials for Crossplane and GitOps patterns
7. **Safety first**: Atomic operations, backups, and resilient cleanup

## Development Status

- **Version**: 0.1.0 (Alpha)
- **License**: Apache 2.0
- **Stage**: Active development - Bootstrap cluster complete, tutorial development in progress
- **Stability**: Core features production-ready with 95%+ test coverage
- **Test Coverage**: 273+ tests passing, comprehensive property-based testing
- **Next Milestone**: Complete tutorial system, begin management cluster implementation
