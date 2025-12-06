# Implementation Plan

## Phase 1: Foundation - KindClient and Safety

- [ ] 1. Write all property tests for KindClient foundation (Red phase)
  - Create test file: `tests/unit/integrations/test_kind_client.py`
  - **Property 1: Cluster name isolation** - Validates: Requirements 2.1
  - **Property 2: Context isolation** - Validates: Requirements 2.3
  - **Property 3: Cluster creation with correct name** - Validates: Requirements 4.1
  - **Property 6: Cluster configuration correctness** - Validates: Requirements 4.2
  - Run tests to verify they all fail
  - _Requirements: 2.1, 2.3, 4.1, 4.2_

- [ ] 2. Implement KindClient (Green phase)
  - Create `mk8/integrations/kind_client.py` module
  - Implement error hierarchy: `BootstrapError`, `KindError`, `ClusterExistsError`, `ClusterNotFoundError`
  - Create `KindClient` class with hardcoded CLUSTER_NAME = "mk8-bootstrap"
  - Implement `_run_kind_command()` helper that always uses cluster name
  - Implement `cluster_exists()` method
  - Implement `create_cluster()` with default kind configuration
  - Ensure all kubectl commands explicitly specify `--context kind-mk8-bootstrap`
  - Run tests to verify they pass
  - _Requirements: 2.1, 2.3, 4.1, 4.2, 9.1, 9.2_

## Phase 2: KindClient Operations

- [ ] 3. Write all property tests for KindClient operations (Red phase)
  - **Property 7: Readiness verification** - Validates: Requirements 4.3
  - **Property 8: Creation errors include suggestions** - Validates: Requirements 4.4, 9.2
  - **Property 10: Existing cluster detection** - Validates: Requirements 5.1
  - **Property 13: Status checking** - Validates: Requirements 7.1
  - **Property 14: Status completeness** - Validates: Requirements 7.3, 7.4, 7.5
  - **Property 15: Cluster deletion** - Validates: Requirements 8.2
  - **Property 16: Container cleanup verification** - Validates: Requirements 8.3
  - **Property 19: Kubernetes version customization** - Validates: Requirements 10.1
  - **Property 20: Version validation** - Validates: Requirements 10.3
  - Run tests to verify they all fail
  - _Requirements: 4.3, 4.4, 5.1, 7.1, 7.3-7.5, 8.2, 8.3, 9.2, 10.1, 10.3_

- [ ] 4. Implement KindClient operations (Green phase)
  - Implement `wait_for_ready()` with timeout
  - Implement `get_kubeconfig()`
  - Implement `get_cluster_info()` returning dict with cluster details
  - Implement `delete_cluster()` with container cleanup verification
  - Add kubernetes_version parameter to `create_cluster()`
  - Implement version validation
  - Run tests to verify they pass
  - _Requirements: 4.3, 4.4, 5.1, 7.1, 7.3-7.5, 8.2, 8.3, 9.2, 10.1, 10.3_

## Phase 3: BootstrapManager Orchestration

- [ ] 5. Write all property tests for BootstrapManager (Red phase)
  - Create test file: `tests/unit/business/test_bootstrap_manager.py`
  - **Property 4: Prerequisite validation before operations** - Validates: Requirements 3.1, 3.2, 3.3
  - **Property 5: Prerequisite errors include suggestions** - Validates: Requirements 3.4
  - **Property 9: Context setting on creation** - Validates: Requirements 4.5, 6.2
  - **Property 11: Force recreate workflow** - Validates: Requirements 5.2
  - **Property 12: Kubeconfig merging** - Validates: Requirements 6.1
  - **Property 17: Kubeconfig cleanup** - Validates: Requirements 8.4
  - **Property 18: Cleanup resilience** - Validates: Requirements 8.6
  - Run tests to verify they all fail
  - _Requirements: 3.1-3.4, 4.5, 5.2, 6.1, 6.2, 8.4, 8.6_

- [ ] 6. Implement BootstrapManager (Green phase)
  - Create `mk8/business/bootstrap_manager.py` module
  - Implement `ClusterStatus` data model
  - Create `BootstrapManager` class
  - Integrate with existing `PrerequisiteChecker` from installer spec
  - Implement `create_cluster()` orchestration with prerequisite validation
  - Integrate with `KubeconfigManager` for context merging
  - Handle existing cluster detection and force_recreate flag
  - Implement `get_status()` method
  - Implement `delete_cluster()` orchestration with kubeconfig cleanup
  - Implement cleanup resilience (continue on errors)
  - Run tests to verify they pass
  - _Requirements: 3.1-3.6, 4.5, 5.2, 6.1, 6.2, 7.1-7.6, 8.4, 8.6_

## Phase 4: CLI Integration

- [ ] 7. Implement bootstrap CLI commands
  - Create `mk8/cli/commands/bootstrap.py` module
  - Implement `bootstrap` command group
  - Implement `bootstrap create` command with --force-recreate and --kubernetes-version flags
  - Implement `bootstrap delete` command with --yes flag
  - Implement `bootstrap status` command
  - Follow UX guidelines from Requirement 11
  - _Requirements: 1.1-1.5, 11 (UX guidelines)_

- [ ] 8. Write integration tests (no mocking)
  - Create test file: `tests/integration/test_bootstrap_lifecycle.py`
  - Test full cluster lifecycle with real kind
  - Test safety properties with real operations
  - Test error scenarios
  - Test prerequisite validation
  - _Requirements: All requirements_

## Final Checkpoint

- [ ] 9. Verify complete implementation
  - Run full test suite to ensure all tests pass
  - Verify 100% property coverage (20 properties implemented)
  - Manually test UX guidelines from Requirement 11
  - Test with real kind cluster creation and deletion
  - Ask user if questions arise
