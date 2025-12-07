# Bootstrap Cluster Workflow

## Document Purpose

This document serves as a **high-level orchestration guide** that shows how the four bootstrap specifications work together to create a fully operational management cluster. It provides:

- The complete sequence of bootstrap operations
- The mk8 CLI command catalog for bootstrap
- An end-to-end workflow example
- The relationship between bootstrap and ongoing GitOps management

## Relationship to Other Documents

| Document | Purpose | Relationship |
|----------|---------|--------------|
| **This Document** | Orchestration workflow and CLI reference | Shows how specs work together |
| **ADR-001** | ArgoCD testing approaches analysis | Explains why we chose namespaced environments |
| **ADR-002** | ArgoCD testing implementation strategy | Documents the 4-phase testing approach |
| **argocd-gitops-promotion** | Phase 1: Namespaced environment promotion | Defines how ArgoCD CRDs are managed post-bootstrap |
| **Individual Specs** | Detailed requirements/design/tasks | Implementation details for each component |

### Key Distinction: Bootstrap vs. Steady-State

- **Bootstrap Phase** (this document): One-time setup to create the management cluster
- **Steady-State Phase** (argocd-gitops-promotion): Ongoing management of ArgoCD CRDs using dev/staging/prod promotion

The `argocd-config/` GitOps repository structure serves BOTH phases:
- During bootstrap: Initial ArgoCD configuration is deployed
- After bootstrap: ArgoCD CRDs are tested and promoted through dev/staging/prod environments

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

---

## Steady-State Phase: Ongoing ArgoCD Management

After the bootstrap process completes and the management cluster is operational, ArgoCD CRD management transitions to a **dev/staging/prod promotion workflow**. This is documented in the `argocd-gitops-promotion` spec.

### Post-Bootstrap ArgoCD Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Management Cluster (Steady-State)             │
└─────────────────────────────────────────────────────────────────┘

argocd-dev namespace
├─ ArgoCD Dev Instance
├─ Dev Projects, ApplicationSets, Applications
└─ Watches: feature branches

argocd-staging namespace
├─ ArgoCD Staging Instance
├─ Staging Projects, ApplicationSets, Applications
└─ Watches: staging branch

argocd namespace (prod)
├─ ArgoCD Production Instance
├─ Prod Projects, ApplicationSets, Applications
└─ Watches: main branch

┌─────────────────────────────────────────────────────────────────┐
│              Promotion Workflow (Dev → Staging → Prod)           │
│         See: .claude/specs/argocd-gitops-promotion/              │
└─────────────────────────────────────────────────────────────────┘
```

### How Bootstrap Enables Steady-State

The bootstrap process (specifically `argocd-bootstrap` and `gitops-repository-setup`) creates the foundation for the ongoing promotion workflow:

1. **GitOps Repository Structure**: Created during bootstrap with `argocd-config/base/` and `argocd-config/overlays/`
2. **Initial ArgoCD Instance**: Installed in the `argocd` namespace (production)
3. **Dev/Staging Namespaces**: Created during bootstrap handoff
4. **Dev/Staging ArgoCD Instances**: Deployed as part of the initial management cluster setup

After bootstrap completes, changes to ArgoCD CRDs follow the promotion workflow:
- Feature branch → Dev environment (test changes safely)
- PR to staging branch → Staging environment (integration testing)
- PR to main branch → Production environment (controlled rollout)

**For details on the promotion workflow, see**: `.claude/specs/argocd-gitops-promotion/`

---

## Migration from Original Spec

The original `local-bootstrap-cluster` spec has been marked as deprecated. All requirements have been distributed across the four new specs:

- **Requirements 1-3, 6, 8-10, 12** → local-kind-cluster
- **Requirements 4-5, 7, 11** → crossplane-bootstrap
- **New requirements** → gitops-repository-setup
- **New requirements** → argocd-bootstrap

---

## Related Architecture Decisions

The bootstrap workflow and subsequent ArgoCD management approach are informed by architectural decisions documented in:

### ADR-001: ArgoCD Testing Approaches Analysis
**Status**: FROZEN (Reference Document)

Analyzes four approaches for safely testing ArgoCD CRD changes:
1. Ephemeral Preview Environments
2. Static Analysis and Policy Engine
3. Hybrid Staged Rollout with Canary Testing
4. **Namespaced Environment Promotion** ← Selected approach

**Key Finding**: For single management cluster scenarios (our case), Approach 4 (Namespaced Environments) combined with static analysis provides the best balance of safety, practicality, and resource efficiency.

**Location**: `.claude/architecture/ADR-001-argocd-testing-approaches-analysis.md`

### ADR-002: ArgoCD Testing Implementation Strategy
**Status**: CONTEXT-ONLY (Decision Log)

Documents the decision-making process and rationale for the 4-phase implementation:
- **Phase 1**: Management Cluster Namespaced Environments (argocd-gitops-promotion)
- **Phase 2**: Basic Static Analysis (schema validation + safety policies)
- **Phase 3**: Workload Cluster Canary Deployment
- **Phase 4**: Advanced Static Analysis (change detection + blast radius)

**Key Decision**: ArgoCD installation is managed by mk8 orchestrator (bootstrap), while ArgoCD configuration (CRDs) is managed via GitOps with namespaced promotion.

**Location**: `.claude/architecture/ADR-002-argocd-testing-implementation-strategy.md`

---

## Next Steps

### For Bootstrap Implementation
For each spec:
1. Review and approve requirements
2. Create design document
3. Create implementation tasks
4. Execute tasks following TDD methodology

### For Ongoing Management
After bootstrap is complete:
1. Implement Phase 1: Namespaced environment promotion (argocd-gitops-promotion)
2. Implement Phase 2: Basic static analysis
3. Implement Phase 3: Workload cluster canary deployment
4. Implement Phase 4: Advanced static analysis
