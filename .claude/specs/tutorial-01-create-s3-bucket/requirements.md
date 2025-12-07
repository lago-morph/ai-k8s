# Requirements Document

## Introduction

This feature provides a tutorial demonstrating how to use mk8 with Crossplane to create an AWS S3 bucket using a local bootstrap cluster. The tutorial serves as an introductory example for users learning to provision cloud resources through Crossplane, focusing on the fundamental workflow without GitOps complexity. Users will install mk8, verify dependencies, create a local bootstrap cluster, install Crossplane, and provision an S3 bucket directly using kubectl.

## Glossary

- **mk8**: The CLI tool for managing Kubernetes infrastructure on AWS using a multi-tier cluster architecture
- **Crossplane**: An open-source Kubernetes extension that transforms a Kubernetes cluster into a universal control plane for managing cloud infrastructure
- **S3 Bucket**: Amazon Simple Storage Service bucket, a container for storing objects in AWS
- **Bootstrap Cluster**: A local Kubernetes cluster created using kind (Kubernetes in Docker) that runs on the user's local machine
- **MRD (Managed Resource Definition)**: A Crossplane custom resource definition that represents actual cloud infrastructure (e.g., an S3 bucket in AWS)
- **Provider**: A Crossplane component that enables management of resources in a specific cloud provider (e.g., AWS Provider)
- **kubectl**: The Kubernetes command-line tool for interacting with Kubernetes clusters
- **kind**: Kubernetes in Docker, a tool for running local Kubernetes clusters using Docker containers

## Requirements

### Requirement 1

**User Story:** As a new mk8 user, I want to install the mk8 CLI tool, so that I can use it to manage my local Kubernetes infrastructure.

#### Acceptance Criteria

1. WHEN a user accesses installation instructions THEN the system SHALL provide commands to install mk8 on the user's platform
2. WHEN mk8 is installed THEN the system SHALL be accessible via the command line
3. WHEN the user verifies installation THEN the system SHALL provide a command to check the mk8 version
4. WHEN installation completes THEN the system SHALL confirm mk8 is ready for use
5. WHEN installation fails THEN the system SHALL provide troubleshooting guidance for common installation issues

### Requirement 2

**User Story:** As a tutorial user, I want to verify that all prerequisites are met, so that I can avoid errors during tutorial execution.

#### Acceptance Criteria

1. WHEN a user begins the tutorial THEN the system SHALL list all required prerequisites (Docker, kubectl, AWS credentials, mk8 CLI)
2. WHEN prerequisites are checked THEN the system SHALL provide commands to verify each prerequisite is installed and configured
3. IF Docker is not running THEN the system SHALL provide instructions to start Docker
4. WHEN AWS credentials are required THEN the system SHALL guide the user to configure credentials for AWS access
5. WHEN all prerequisites are verified THEN the system SHALL confirm the user can proceed with cluster creation

### Requirement 3

**User Story:** As a tutorial user, I want to use mk8 to create a local bootstrap cluster, so that I have a Kubernetes environment to install Crossplane.

#### Acceptance Criteria

1. WHEN the user executes the mk8 bootstrap cluster creation command THEN the system SHALL create a local kind cluster
2. WHEN the bootstrap cluster is created THEN the system SHALL configure kubectl to use the bootstrap cluster context
3. WHEN cluster creation completes THEN the system SHALL verify the cluster is running and accessible
4. WHEN the cluster is ready THEN the system SHALL confirm all cluster nodes are in Ready state
5. WHEN the user verifies the kubeconfig THEN the system SHALL show the bootstrap cluster context is properly configured

### Requirement 4

**User Story:** As a tutorial user, I want mk8 to install and configure Crossplane on the bootstrap cluster, so that I can use it to provision AWS resources.

#### Acceptance Criteria

1. WHEN the user executes the mk8 Crossplane installation command THEN the system SHALL install Crossplane on the bootstrap cluster
2. WHEN Crossplane is installed THEN the system SHALL verify the Crossplane pods are running in the cluster
3. WHEN the mk8 command completes THEN the system SHALL install the Crossplane AWS Provider
4. WHEN the Provider is installed THEN the system SHALL create a ProviderConfig with AWS credentials
5. WHEN installation completes THEN the system SHALL verify the AWS Provider is healthy and ready

### Requirement 5

**User Story:** As a tutorial user, I want to define an S3 bucket using a Crossplane Managed Resource, so that I can declare my infrastructure as code.

#### Acceptance Criteria

1. WHEN the tutorial provides resource definitions THEN the system SHALL include a Crossplane Bucket MRD YAML manifest
2. WHEN the MRD is defined THEN the system SHALL specify bucket configuration including name, region, and access controls
3. WHEN the YAML manifest is presented THEN the system SHALL include inline comments explaining each field and its purpose
4. WHEN the resource definition is shown THEN the system SHALL explain how Crossplane translates the MRD into AWS API calls
5. WHEN the manifest is provided THEN the system SHALL ensure the bucket name is globally unique

### Requirement 6

**User Story:** As a tutorial user, I want to apply the S3 bucket configuration to my cluster, so that Crossplane provisions the actual AWS resource.

#### Acceptance Criteria

1. WHEN the user applies the MRD THEN the system SHALL create the Bucket resource in the bootstrap cluster using kubectl
2. WHEN the resource is applied THEN the system SHALL trigger Crossplane to provision the S3 bucket in AWS
3. WHEN provisioning begins THEN the system SHALL provide kubectl commands to monitor the resource status
4. WHEN provisioning is in progress THEN the system SHALL display the status conditions of the Bucket resource
5. WHEN provisioning completes THEN the system SHALL show the Bucket status as "Ready" and "Synced"

### Requirement 7

**User Story:** As a tutorial user, I want to verify that the S3 bucket was created successfully in AWS, so that I can confirm Crossplane worked correctly.

#### Acceptance Criteria

1. WHEN the user checks resource status THEN the system SHALL provide kubectl commands to inspect the Bucket resource
2. WHEN the Bucket resource is inspected THEN the system SHALL display the AWS S3 bucket ARN and region
3. WHEN AWS verification is performed THEN the system SHALL provide AWS CLI commands to list and describe the created bucket
4. WHEN the bucket is verified in AWS THEN the system SHALL confirm the bucket exists with the correct name and configuration
5. WHEN verification completes THEN the system SHALL demonstrate the bucket is accessible via AWS CLI

### Requirement 8

**User Story:** As a tutorial user, I want to delete the S3 bucket, so that I can clean up AWS resources and avoid unnecessary costs.

#### Acceptance Criteria

1. WHEN the user initiates bucket deletion THEN the system SHALL provide the kubectl command to delete the Bucket resource
2. WHEN the Bucket resource is deleted THEN the system SHALL trigger Crossplane to delete the S3 bucket from AWS
3. WHEN deletion is in progress THEN the system SHALL provide commands to monitor the deletion status
4. WHEN deletion completes THEN the system SHALL verify the Bucket resource is removed from the cluster
5. WHEN AWS cleanup is verified THEN the system SHALL confirm the bucket no longer exists in AWS

### Requirement 9

**User Story:** As a tutorial user, I want to use mk8 to delete the local bootstrap cluster, so that I can free up local resources after completing the tutorial.

#### Acceptance Criteria

1. WHEN the user executes the mk8 cluster deletion command THEN the system SHALL delete the bootstrap cluster
2. WHEN the cluster is deleted THEN the system SHALL remove all cluster containers and resources
3. WHEN deletion completes THEN the system SHALL verify the cluster no longer exists
4. WHEN kubectl contexts are checked THEN the system SHALL confirm the bootstrap cluster context is removed
5. WHEN cleanup is complete THEN the system SHALL confirm all local resources are freed

### Requirement 10

**User Story:** As a tutorial user, I want to understand common issues and their solutions, so that I can troubleshoot problems independently.

#### Acceptance Criteria

1. WHEN troubleshooting guidance is provided THEN the system SHALL include a section on common issues and resolutions
2. WHEN Crossplane provisioning fails THEN the system SHALL explain how to check Crossplane logs and resource events
3. WHEN AWS permissions are insufficient THEN the system SHALL describe the required IAM permissions for S3 bucket creation
4. WHEN resources are stuck THEN the system SHALL provide commands to inspect resource conditions and status messages
5. WHEN bucket deletion fails THEN the system SHALL explain how to manually delete the bucket and resolve finalizer issues
