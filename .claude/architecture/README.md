# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) that document significant architectural decisions made during the development of mk8.

## What is an ADR?

An Architecture Decision Record captures a significant architectural decision along with its context and consequences. ADRs are:

- **Immutable**: Once accepted, ADRs are not modified (create a new ADR to supersede)
- **Contextual**: They explain WHY a decision was made, not just WHAT
- **Referenced**: Implementation specs reference relevant ADRs for context

## ADR Status Values

| Status | Meaning |
|--------|---------|
| PROPOSED | Under discussion, not yet accepted |
| ACCEPTED | Decision has been made and is in effect |
| DEPRECATED | No longer applies, superseded by another ADR |
| SUPERSEDED | Replaced by a newer ADR (link to replacement) |
| FROZEN | Reference document, preserved for historical context |
| CONTEXT-ONLY | Provides context but is not the source of truth |

## How to Use ADRs

### For Implementers
- Read relevant ADRs before implementing a feature
- ADRs explain WHY decisions were made
- Implementation details are in spec documents, not ADRs

### For Decision Makers
- Create a new ADR when making significant architectural decisions
- Use the template in `template-adr.md`
- Get team review before marking as ACCEPTED

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | ArgoCD Testing Approaches Analysis | FROZEN | 2025-12-06 |
| ADR-002 | ArgoCD Testing Implementation Strategy | CONTEXT-ONLY | 2025-12-06 |

## Related Specs

ADRs inform the following specification documents:

- `.claude/specs/argocd-gitops-promotion/` - Phase 1: Namespaced environment promotion
- `.claude/specs/argocd-crd-basic-static/` - Phase 2: Basic static analysis
- `.claude/specs/workload-cluster-gitops/` - Phase 3: Workload cluster GitOps
- `.claude/specs/argocd-crd-advanced-static/` - Phase 4: Advanced static analysis
