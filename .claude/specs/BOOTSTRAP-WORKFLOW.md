# Bootstrap Cluster Workflow

This document describes the complete workflow for setting up the bootstrap cluster and provisioning the AWS management cluster using GitOps.

## Overview

The bootstrap cluster setup has been broken down into four discrete, manageable specifications that build upon each other:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Bootstrap Cluster Workflow                    │
└─────────────────────────────────────────────────────────────────┘

1. local-kind-cluster
   ├─ Create local kind cluster
   ├─ Manage kubeconfig
   └─ Basic cluster operations (status, delete)
   
2. crossplane-bootstrap
   ├─ Install Crossplane
   ├─ Install AWS provider
   ├─ Configure AWS credentials
   └─ Validate AWS connectivity
   
3. gitops-repository-setup
   ├─ Create/configure Git repository
   ├─ Set up directory structure
   ├─ Create Crossplane manifest templates
   └─ Configure Kustomize overlays
   
4. argocd-bootstrap
   ├─ Install ArgoCD
   ├─ Connect to GitOps repository
   ├─ Create management cluster Application
   └─ Trigger initial sync

┌─────────────────────────────────────────────────────────────────┐
│              Management Cluster Provisioning Begins              │
│         (ArgoCD syncs Crossplane manifests from Git)            │
└─────────────────────────────────────────────────────────────────┘
```

## Specification Details

### 1. local-kind-cluster

**Purpose**: Establish the basic Kubernetes cluster foundation

**Key Features**:
- Prerequisites validation (Docker, kind, kubectl)
- kind cluster creation with deterministic naming
- kubeconfig file management and context switching
- Cluster status monitoring
- Clean cluster deletion and resource cleanup

**Dependencies**: None (first step)

**CLI Commands**:
- `mk8 bootstrap create` - Create the kind cluster
- `mk8 bootstrap status` - Check cluster status
- `mk8 bootstrap delete` - Remove cluster and cleanup

**Spec Location**: `.claude/specs/local-kind-cluster/`

---

### 2. crossplane-bootstrap

**Purpose**: Transform the basic cluster into an infrastructure provisioning platform

**Key Features**:
- Crossplane installation and version management
- AWS provider installation
- AWS credentials configuration via Kubernetes secrets
- ProviderConfig creation and validation
- AWS API connectivity testing
- IAM permissions verification

**Dependencies**: 
- Requires local-kind-cluster to be complete
- Requires AWS credentials configured via `mk8 config`

**CLI Commands**:
- `mk8 crossplane install` - Install Crossplane and AWS provider
- `mk8 crossplane status` - Check Crossplane health
- `mk8 crossplane validate` - Test AWS connectivity

**Spec Location**: `.claude/specs/crossplane-bootstrap/`

---

### 3. gitops-repository-setup

**Purpose**: Create the Git repository structure for infrastructure-as-code

**Key Features**:
- New repository creation or existing repository integration
- Standardized directory structure (base, overlays, bootstrap, management-cluster)
- Crossplane manifest templates for EKS, VPC, IAM
- Kustomize configuration for environment management
- ArgoCD Application manifest templates
- Comprehensive documentation generation

**Dependencies**:
- Can be done independently, but typically after crossplane-bootstrap
- Requires Git installed locally

**CLI Commands**:
- `mk8 gitops init` - Initialize GitOps repository
- `mk8 gitops status` - Show repository information
- `mk8 gitops validate` - Validate repository structure

**Spec Location**: `.claude/specs/gitops-repository-setup/`

---

### 4. argocd-bootstrap

**Purpose**: Install ArgoCD and enable GitOps-based infrastructure management

**Key Features**:
- ArgoCD installation and version management
- ArgoCD CLI configuration
- Admin password retrieval and UI access
- GitOps repository connection with credential management
- Management cluster Application creation
- Auto-sync and self-heal configuration
- Initial sync trigger and monitoring

**Dependencies**:
- Requires local-kind-cluster to be complete
- Requires crossplane-bootstrap to be complete
- Requires gitops-repository-setup to be complete

**CLI Commands**:
- `mk8 argocd install` - Install ArgoCD
- `mk8 argocd connect` - Connect to GitOps repository
- `mk8 argocd status` - Check ArgoCD and Application health
- `mk8 argocd ui` - Access ArgoCD UI

**Spec Location**: `.claude/specs/argocd-bootstrap/`

---

## Complete Workflow Example

```bash
# Step 1: Configure AWS credentials (prerequisite)
mk8 config

# Step 2: Create the local kind cluster
mk8 bootstrap create

# Step 3: Install Crossplane and configure AWS
mk8 crossplane install
mk8 crossplane validate

# Step 4: Set up GitOps repository
mk8 gitops init
mk8 gitops validate

# Step 5: Install ArgoCD and start GitOps
mk8 argocd install
mk8 argocd connect
mk8 argocd status

# Step 6: Monitor management cluster provisioning
mk8 argocd ui  # Open ArgoCD UI to watch progress
```

## Benefits of This Breakdown

1. **Modularity**: Each spec can be implemented and tested independently
2. **Clarity**: Clear separation of concerns makes each component easier to understand
3. **Flexibility**: Users can customize or replace individual components
4. **Testability**: Smaller specs are easier to test thoroughly
5. **Maintainability**: Changes to one component don't affect others
6. **Reusability**: Components like gitops-repository-setup can be used in other contexts

## Implementation Order

The recommended implementation order follows the dependency chain:

1. **local-kind-cluster** (no dependencies)
2. **crossplane-bootstrap** (depends on #1)
3. **gitops-repository-setup** (independent, but logically after #2)
4. **argocd-bootstrap** (depends on #1, #2, #3)

## Migration from Original Spec

The original `local-bootstrap-cluster` spec has been marked as deprecated. All requirements have been distributed across the four new specs:

- **Requirements 1-3, 6, 8-10, 12** → local-kind-cluster
- **Requirements 4-5, 7, 11** → crossplane-bootstrap
- **New requirements** → gitops-repository-setup
- **New requirements** → argocd-bootstrap

## Next Steps

For each spec:
1. Review and approve requirements
2. Create design document
3. Create implementation tasks
4. Execute tasks following TDD methodology
