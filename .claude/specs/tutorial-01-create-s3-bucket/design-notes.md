# Design Notes for Tutorial-01-Create-S3-Bucket

This file captures design-level decisions and context that will inform the design phase. These items should be incorporated into the design.md document when that phase begins.

## Tutorial Format and Presentation

### Documentation Framework
- The tutorial format will be determined during the design phase
- Must be compatible with automatic documentation/website generators
- Should use the same framework that will be used for documentation across the entire site
- See the `documentation-site` spec for the broader documentation generation strategy

### Content Structure
- Tutorial should be organized into clear, logical sections
- Should support code blocks with syntax highlighting
- Should support inline comments in YAML manifests
- Should include visual indicators for improved readability

## Scope Clarifications

### What This Tutorial Covers
- Installing mk8 CLI
- Verifying dependencies (Docker, kubectl, AWS credentials)
- Using mk8 to create a local bootstrap cluster
- Using mk8 to install and configure Crossplane on the bootstrap cluster
- Verifying the kubeconfig was properly configured by mk8
- Manually applying a Crossplane MRD using kubectl to create an S3 bucket
- Verifying the S3 bucket exists in AWS
- Manually deleting the S3 bucket MRD using kubectl
- Using mk8 to delete the local bootstrap cluster

### What This Tutorial Does NOT Cover
- Management cluster creation (EKS)
- GitOps workflows
- Crossplane Compositions or Claims (using direct MRDs instead)
- Advanced Crossplane features
- Multi-cluster scenarios

## Technical Approach

### Tool Usage
- **mk8 does the heavy lifting**: cluster creation, Crossplane installation, Crossplane configuration, cluster deletion
- **kubectl used minimally**: only for applying the S3 bucket MRD, verifying kubeconfig, and deleting the MRD
- **AWS CLI**: used only for verifying the S3 bucket exists in AWS

### Cluster Architecture
- Uses ONLY the bootstrap cluster (local kind cluster)
- No management cluster (EKS) is created
- Crossplane runs directly on the bootstrap cluster
- mk8 handles all cluster lifecycle operations

### Resource Provisioning Method
- mk8 installs and configures Crossplane and the AWS Provider
- Direct application of Crossplane Managed Resource Definitions (MRDs) via kubectl
- No Compositions or Claims in this introductory tutorial
- Focuses on the fundamental Crossplane workflow
- User manually applies and deletes the MRD to understand the process

### AWS Integration
- Requires AWS credentials configured locally
- mk8 installs the Crossplane AWS Provider on bootstrap cluster
- mk8 creates the ProviderConfig with AWS credentials
- S3 bucket created directly in user's AWS account via kubectl-applied MRD

## Learning Objectives

### Primary Goal
Demonstrate the fundamental workflow of using Crossplane to provision cloud resources, without the complexity of GitOps or multi-cluster architectures.

### Key Concepts to Teach
- What Crossplane is and how it works
- How to install Crossplane on a Kubernetes cluster
- How to configure a Crossplane Provider (AWS)
- How to define infrastructure as code using Kubernetes manifests
- How to apply and monitor Crossplane resources
- How to verify cloud resources were created
- How to clean up resources properly

### Intentional Simplifications
- Using bootstrap cluster only (not management cluster)
- Using direct MRDs (not Compositions/Claims)
- No GitOps integration
- Single resource type (S3 bucket)
- Manual kubectl commands (not automated workflows)

## Future Considerations

### Follow-up Tutorials
This tutorial should serve as a foundation for more advanced tutorials that introduce:
- Management cluster creation
- Crossplane Compositions and Claims
- GitOps workflows with ArgoCD
- Multi-resource provisioning
- Advanced Crossplane patterns

### Documentation Site Integration
The tutorial content and format should align with the broader documentation site strategy being developed in the `documentation-site` spec.
