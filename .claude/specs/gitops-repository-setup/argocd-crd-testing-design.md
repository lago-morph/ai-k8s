---
status: AUTHORITATIVE
created: 2025-12-06
purpose: Design Specification
related:
  - argocd-crd-testing-requirements.md
  - argocd-testing-decisions.md (context only)
  - argocd-testing-analysis.md (frozen reference)
ai-instructions: |
  THIS IS THE AUTHORITATIVE DESIGN DOCUMENT for ArgoCD CRD Testing.
  
  PHASE 1 DESIGN: Complete and verified. Ready for detailed design and implementation.
  PHASE 2, 3, 4 DESIGN: High-level concepts captured from planning discussions but NOT
  fully designed. These phases require additional detailed design before implementation.
  
  For requirements, see argocd-crd-testing-requirements.md.
  For context on WHY decisions were made, see argocd-testing-decisions.md.
---

# ArgoCD CRD Testing - Design Document

## Document Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 | ✅ COMPLETE | High-level design verified, ready for detailed design |
| Phase 2 | 📝 DRAFT | Concepts captured, needs detailed design |
| Phase 3 | 📝 DRAFT | Concepts captured, needs detailed design |
| Phase 4 | 📝 DRAFT | Concepts captured, needs detailed design |

---

## Overview

This document describes the design for implementing safe testing and promotion of ArgoCD CRD changes. The design spans four phases, with Phase 1 fully specified and Phases 2-4 captured at a conceptual level.

### Architecture Overview

```mermaid
flowchart TD
    subgraph "GitOps Repository"
        Base[Kustomize Base<br/>Templated CRDs]
        DevOverlay[Dev Overlay]
        StagingOverlay[Staging Overlay]
        ProdOverlay[Prod Overlay]
        
        Base --> DevOverlay
        Base --> StagingOverlay
        Base --> ProdOverlay
    end
    
    subgraph "CI/CD Pipeline"
        StaticAnalysis[Static Analysis<br/>Phases 2 & 4]
    end
    
    subgraph "Management Cluster"
        subgraph "argocd-dev"
            DevConfig[Dev ArgoCD Config]
        end
        subgraph "argocd-staging"
            StagingConfig[Staging ArgoCD Config]
        end
        subgraph "argocd"
            ProdConfig[Prod ArgoCD Config]
        end
    end
    
    subgraph "Workload Clusters"
        Canary[Canary Cluster<br/>Phase 3]
        Wave1[Wave 1 Clusters]
        Wave2[Wave 2 Clusters]
    end
    
    DevOverlay --> StaticAnalysis
    StagingOverlay --> StaticAnalysis
    ProdOverlay --> StaticAnalysis
    
    StaticAnalysis --> DevConfig
    StaticAnalysis --> StagingConfig
    StaticAnalysis --> ProdConfig
    
    ProdConfig --> Canary
    Canary --> Wave1
    Wave1 --> Wave2
```

---

## Phase 1: Management Cluster Namespaced Environments

**Status**: ✅ COMPLETE - Ready for detailed design and implementation

### High-Level Architecture

```mermaid
flowchart LR
    subgraph "Git Repository"
        Feature[Feature Branch]
        Staging[staging Branch]
        Main[main Branch]
    end
    
    subgraph "Management Cluster"
        subgraph "argocd-dev namespace"
            DevArgo[ArgoCD Instance]
            DevApps[Dev Applications]
            DevProjects[Dev Projects]
        end
        
        subgraph "argocd-staging namespace"
            StagingArgo[ArgoCD Instance]
            StagingApps[Staging Applications]
            StagingProjects[Staging Projects]
        end
        
        subgraph "argocd namespace"
            ProdArgo[ArgoCD Instance]
            ProdApps[Prod Applications]
            ProdProjects[Prod Projects]
        end
    end
    
    Feature --> |Auto-sync| DevArgo
    Staging --> |Auto-sync| StagingArgo
    Main --> |Auto-sync| ProdArgo
    
    style DevArgo fill:#90EE90
    style StagingArgo fill:#FFD700
    style ProdArgo fill:#ff9999
```

### GitOps Repository Structure

```
gitops-repo/
├── README.md                           # Repository overview and workflow docs
├── argocd-config/                      # ArgoCD CRD configurations
│   ├── README.md                       # ArgoCD config documentation
│   ├── base/                           # Kustomize base (templates)
│   │   ├── kustomization.yaml
│   │   ├── applications/               # Application templates
│   │   │   ├── kustomization.yaml
│   │   │   └── *.yaml
│   │   ├── applicationsets/            # ApplicationSet templates
│   │   │   ├── kustomization.yaml
│   │   │   └── *.yaml
│   │   ├── projects/                   # AppProject templates
│   │   │   ├── kustomization.yaml
│   │   │   └── *.yaml
│   │   └── repositories/               # Repository templates
│   │       ├── kustomization.yaml
│   │       └── *.yaml
│   │
│   └── overlays/                       # Environment-specific overlays
│       ├── dev/
│       │   ├── kustomization.yaml
│       │   ├── namespace-patch.yaml    # namespace: argocd-dev
│       │   └── config-patches/         # Dev-specific patches
│       ├── staging/
│       │   ├── kustomization.yaml
│       │   ├── namespace-patch.yaml    # namespace: argocd-staging
│       │   └── config-patches/
│       └── prod/
│           ├── kustomization.yaml
│           ├── namespace-patch.yaml    # namespace: argocd
│           └── config-patches/
│
├── argocd-instances/                   # ArgoCD instance configurations
│   ├── dev/
│   │   └── argocd-instance.yaml        # ArgoCD CR for dev
│   ├── staging/
│   │   └── argocd-instance.yaml        # ArgoCD CR for staging
│   └── prod/
│       └── argocd-instance.yaml        # ArgoCD CR for prod (reference)
│
└── ... (other gitops content)
```

### Kustomize Structure

#### Base Template Example

```yaml
# argocd-config/base/applications/example-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: example-app  # Will be patched with environment suffix
  # namespace injected by overlay
  labels:
    app.kubernetes.io/managed-by: argocd-crd-testing
    environment: base  # Will be patched by overlay
spec:
  project: default  # Will be patched to environment-specific project
  source:
    repoURL: https://github.com/org/app-repo
    targetRevision: HEAD  # May be patched by overlay
    path: manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: app-namespace
  syncPolicy:
    automated:
      prune: false  # Conservative default, may be patched
      selfHeal: true
```

#### Base Kustomization

```yaml
# argocd-config/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - applications/
  - applicationsets/
  - projects/
  - repositories/

commonLabels:
  app.kubernetes.io/part-of: argocd-crd-testing
```

#### Dev Overlay Example

```yaml
# argocd-config/overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namespace: argocd-dev

nameSuffix: -dev

commonLabels:
  environment: dev

patches:
  - path: config-patches/sync-policy-patch.yaml
    target:
      kind: Application
  - path: config-patches/project-patch.yaml
    target:
      kind: Application
```

```yaml
# argocd-config/overlays/dev/config-patches/sync-policy-patch.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: not-used  # Kustomize will match by target
spec:
  syncPolicy:
    automated:
      prune: false  # Never auto-prune in dev
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

#### Prod Overlay Example

```yaml
# argocd-config/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namespace: argocd

# No nameSuffix for prod - these are the "real" names

commonLabels:
  environment: prod

patches:
  - path: config-patches/sync-policy-patch.yaml
    target:
      kind: Application
```

```yaml
# argocd-config/overlays/prod/config-patches/sync-policy-patch.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: not-used
  annotations:
    argocd.argoproj.io/sync-options: "PruneLast=true"
spec:
  syncPolicy:
    automated:
      prune: true  # Prune enabled but with PruneLast
      selfHeal: true
    syncOptions:
      - PrunePropagationPolicy=foreground
      - PruneLast=true
```

### ArgoCD Instance Configuration

#### Dev Instance

```yaml
# argocd-instances/dev/argocd-instance.yaml
apiVersion: argoproj.io/v1beta1
kind: ArgoCD
metadata:
  name: argocd-dev
  namespace: argocd-dev
spec:
  server:
    route:
      enabled: true
  controller:
    appSync: 30s  # Aggressive sync for fast feedback
  applicationSet:
    enabled: true
```

#### Staging Instance

```yaml
# argocd-instances/staging/argocd-instance.yaml
apiVersion: argoproj.io/v1beta1
kind: ArgoCD
metadata:
  name: argocd-staging
  namespace: argocd-staging
spec:
  server:
    route:
      enabled: true
  controller:
    appSync: 180s  # 3 minute sync
  applicationSet:
    enabled: true
```

### Promotion Workflow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Feature as Feature Branch
    participant DevEnv as Dev Environment
    participant StagingBranch as staging Branch
    participant StagingEnv as Staging Environment
    participant MainBranch as main Branch
    participant ProdEnv as Prod Environment
    
    Dev->>Feature: Push changes
    Feature->>DevEnv: Auto-sync (30s)
    Dev->>DevEnv: Verify changes work
    
    Dev->>StagingBranch: Create PR
    Note over StagingBranch: Review + Approve
    StagingBranch->>StagingEnv: Auto-sync (3min)
    Dev->>StagingEnv: Verify changes work
    
    Dev->>MainBranch: Create PR
    Note over MainBranch: Review + Approve
    MainBranch->>ProdEnv: Auto-sync (5min)
    Dev->>ProdEnv: Verify changes work
```

### Namespace and RBAC Design

```mermaid
flowchart TD
    subgraph "Namespace: argocd-dev"
        DevSA[ServiceAccount: argocd-dev]
        DevRole[Role: dev-argocd-admin]
        DevRB[RoleBinding]
        
        DevSA --> DevRB
        DevRole --> DevRB
    end
    
    subgraph "Namespace: argocd-staging"
        StagingSA[ServiceAccount: argocd-staging]
        StagingRole[Role: staging-argocd-admin]
        StagingRB[RoleBinding]
        
        StagingSA --> StagingRB
        StagingRole --> StagingRB
    end
    
    subgraph "Namespace: argocd"
        ProdSA[ServiceAccount: argocd]
        ProdRole[Role: prod-argocd-admin]
        ProdRB[RoleBinding]
        
        ProdSA --> ProdRB
        ProdRole --> ProdRB
    end
    
    Note1[Each ArgoCD instance<br/>only has permissions<br/>in its own namespace]
```

### Integration with mk8 Bootstrap

```mermaid
sequenceDiagram
    participant mk8 as mk8 Orchestrator
    participant Kind as Kind Cluster
    participant GitOps as GitOps Repository
    participant Mgmt as Management Cluster
    
    mk8->>Kind: Create bootstrap cluster
    mk8->>Kind: Install ArgoCD + Crossplane
    
    mk8->>GitOps: Initialize/update repository
    Note over GitOps: Create argocd-config/<br/>base + overlays structure
    
    Kind->>Mgmt: Provision management cluster
    Kind->>Mgmt: Install ArgoCD (prod instance)
    
    mk8->>Mgmt: Create argocd-dev namespace
    mk8->>Mgmt: Create argocd-staging namespace
    mk8->>Mgmt: Deploy dev ArgoCD instance
    mk8->>Mgmt: Deploy staging ArgoCD instance
    
    mk8->>Mgmt: Configure all instances to watch GitOps repo
    
    mk8->>Kind: Delete bootstrap cluster
    
    Note over Mgmt: Management cluster now<br/>self-manages via GitOps
```

### Component Interactions

| Component | Responsibility |
|-----------|----------------|
| GitOps Repository | Source of truth for all ArgoCD CRD configurations |
| Kustomize Base | Template definitions shared across environments |
| Kustomize Overlays | Environment-specific patches and namespace targeting |
| ArgoCD Dev Instance | Watches feature branches, syncs to argocd-dev namespace |
| ArgoCD Staging Instance | Watches staging branch, syncs to argocd-staging namespace |
| ArgoCD Prod Instance | Watches main branch, syncs to argocd namespace |
| mk8 Orchestrator | Bootstraps initial structure, manages ArgoCD installation |

---

## Phase 2: Basic Static Analysis

**Status**: 📝 DRAFT - Concepts captured, needs detailed design

### Conceptual Design

```mermaid
flowchart TD
    subgraph "CI/CD Pipeline"
        PR[Pull Request] --> Schema[Schema Validation]
        Schema --> Policies[Safety Policies]
        Policies --> |Pass| Merge[Allow Merge]
        Policies --> |Fail| Block[Block Merge]
    end
    
    subgraph "Validation Tools"
        Schema --> Kubeconform[kubeconform]
        Policies --> PolicyEngine[OPA/Kyverno CLI]
    end
```

### Schema Validation Concept

- Use `kubeconform` or similar tool
- Validate against ArgoCD CRD schemas
- Run on every PR
- Block merge on failure

### Basic Safety Policies Concept

| Policy | Purpose |
|--------|---------|
| ApplicationSet preserveResourcesOnDeletion | Prevent mass deletion on AppSet removal |
| Application prune requires annotation | Prevent accidental prune enablement |
| Project destinations not wildcard | Prevent overly permissive projects |
| Repository URL pattern matching | Prevent typos in repo URLs |
| Application targetRevision not empty | Prevent accidental HEAD tracking |

### Tooling Options (To Be Decided)

- **OPA/Conftest**: Rego-based policies, powerful but steeper learning curve
- **Kyverno CLI**: YAML-based policies, easier to read/write
- **Custom validators**: Python/Go scripts for specific checks

---

## Phase 3: Workload Cluster Canary Deployment

**Status**: 📝 DRAFT - Concepts captured, needs detailed design

### Conceptual Design

```mermaid
flowchart TD
    subgraph "Change Flow"
        Change[Configuration Change]
        Change --> Canary[Canary Cluster]
        Canary --> |Health OK| Wave1[Wave 1 Clusters]
        Wave1 --> |Health OK| Wave2[Wave 2 Clusters]
        
        Canary --> |Health Fail| Rollback[Rollback]
        Wave1 --> |Health Fail| Rollback
    end
    
    subgraph "Health Checks"
        ArgoSync[ArgoCD Sync Status]
        PodHealth[Pod Health]
        CustomMetrics[Custom Metrics]
    end
    
    Canary --> ArgoSync
    Canary --> PodHealth
    Canary --> CustomMetrics
```

### Canary Strategy Options (To Be Decided)

1. **Dedicated Canary Cluster**: One cluster always receives changes first
2. **Environment-Based**: Dev clusters → Staging clusters → Prod clusters
3. **Rotating Canary**: Different cluster is canary based on change type

### Wave Configuration Concept

```yaml
# Conceptual - actual format TBD
waves:
  - name: canary
    clusters: [canary-cluster]
    waitTime: 30m
    healthChecks: [argocd-sync, pod-health]
    
  - name: wave-1
    clusters: [dev-cluster-1, dev-cluster-2]
    waitTime: 1h
    
  - name: wave-2
    clusters: [staging-cluster-1]
    waitTime: 2h
    requireApproval: true
```

---

## Phase 4: Advanced Static Analysis

**Status**: 📝 DRAFT - Concepts captured, needs detailed design

### Conceptual Design

```mermaid
flowchart TD
    subgraph "Change Detection"
        GitDiff[Git Diff Analysis]
        GitDiff --> FieldChanges[Identify Changed Fields]
        FieldChanges --> RiskAssessment[Risk Assessment]
    end
    
    subgraph "Blast Radius Analysis"
        RiskAssessment --> AppSetExpansion[ApplicationSet Expansion]
        AppSetExpansion --> ImpactCount[Count Affected Apps]
        ImpactCount --> Report[Impact Report]
    end
    
    Report --> |High Risk| RequireApproval[Require Manual Approval]
    Report --> |Low Risk| AutoProceed[Auto-Proceed]
```

### Change Detection Concept

Detect changes to high-risk fields:
- ApplicationSet `spec.generators[*].selector`
- AppProject `spec.destinations`
- Application `spec.syncPolicy`
- Repository `spec.url`

### Blast Radius Analysis Concept

For ApplicationSet changes:
1. Parse the old and new ApplicationSet
2. Simulate template expansion for both
3. Compare generated Applications
4. Report: "This change affects N applications across M clusters"

### Implementation Complexity

This phase requires custom tooling:
- Git diff parsing
- ApplicationSet template simulation
- State comparison logic
- Report generation

Estimated effort: 1-2 weeks

---

## Security Considerations

### Phase 1

- Namespace isolation prevents cross-environment interference
- RBAC limits each ArgoCD instance to its own namespace
- Git branch protection enforces PR requirements
- No credentials stored in GitOps repository

### Phases 2-4

- CI/CD secrets managed by platform (not in repo)
- Policy definitions are code-reviewed like any other change
- Canary health checks don't expose sensitive data

---

## Testing Strategy

### Phase 1

- Unit tests for Kustomize overlays (kustomize build succeeds)
- Integration tests for ArgoCD instance deployment
- End-to-end tests for promotion workflow

### Phases 2-4

- Policy unit tests (known-good and known-bad inputs)
- Canary simulation tests
- Blast radius calculation accuracy tests
