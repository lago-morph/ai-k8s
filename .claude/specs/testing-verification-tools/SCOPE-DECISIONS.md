# Scope Decisions - Testing Verification Tools

**Purpose**: This file captures deferred scope decisions that need to be resolved before or during the design phase.

## Status

These questions were identified during initial requirements gathering but deferred to allow for more informed decision-making during design.

---

## Question 1: Integration Test Framework Scope

### Context

The requirements specify that kubectl and AWS CLI should be used for verification during integration testing. The question is: how much abstraction and helper functionality should be provided?

### Options

#### Option A: Minimal - Documentation Only

**Description**: Provide documentation and examples showing how to use kubectl and AWS CLI in tests, but no helper functions or abstractions.

**Pros**:
- Simplest to implement
- No additional code to maintain
- Developers have full control
- No learning curve for helpers

**Cons**:
- Tests may be verbose and repetitive
- Inconsistent verification patterns across tests
- Each test author reinvents common patterns
- Harder to update verification logic globally

**Example**:
```bash
# tests/integration/test_bootstrap.bats
@test "verify cluster exists" {
  run kubectl cluster-info
  [ "$status" -eq 0 ]
  
  run kubectl get nodes -o json
  [ "$status" -eq 0 ]
  node_count=$(echo "$output" | jq '.items | length')
  [ "$node_count" -gt 0 ]
}
```

---

#### Option B: Basic Helpers

**Description**: Provide simple helper functions for common verification operations, but keep them minimal and focused.

**Pros**:
- Reduces test verbosity
- Consistent verification patterns
- Easier to update verification logic
- Still relatively simple to maintain

**Cons**:
- Additional code to write and test
- Helpers may not cover all use cases
- Risk of over-abstraction

**Example**:
```bash
# lib/test-helpers.sh
verify_cluster_healthy() {
  local kubeconfig="$1"
  kubectl --kubeconfig="$kubeconfig" cluster-info >/dev/null 2>&1 || return 1
  kubectl --kubeconfig="$kubeconfig" get nodes >/dev/null 2>&1 || return 1
  return 0
}

verify_crossplane_installed() {
  local kubeconfig="$1"
  local pod_count=$(kubectl --kubeconfig="$kubeconfig" get pods -n crossplane-system -o json | jq '.items | length')
  [ "$pod_count" -gt 0 ]
}

# tests/integration/test_bootstrap.bats
source lib/test-helpers.sh

@test "verify cluster exists" {
  verify_cluster_healthy "$KUBECONFIG"
}
```

---

#### Option C: Comprehensive Framework

**Description**: Build a full verification framework with extensive helpers, retry logic, diff reporting, and integration with pytest.

**Pros**:
- Very easy to write tests
- Comprehensive error reporting
- Handles edge cases (retries, timeouts)
- Professional test infrastructure

**Cons**:
- Significant implementation effort
- Complex to maintain
- May be overkill for current needs
- Longer learning curve

**Example**:
```python
# lib/verification.py
from mk8.testing import KubernetesVerifier, AWSVerifier

def test_bootstrap_creates_cluster():
    k8s = KubernetesVerifier(kubeconfig="~/.kube/mk8-bootstrap-config")
    aws = AWSVerifier(region="us-west-2")
    
    # Verify cluster
    k8s.assert_cluster_healthy(timeout=300)
    k8s.assert_namespace_exists("crossplane-system")
    k8s.assert_pods_running("crossplane-system", min_count=3)
    
    # Verify AWS resources
    aws.assert_eks_cluster_exists("mk8-bootstrap")
    aws.assert_eks_cluster_status("mk8-bootstrap", "ACTIVE")
```

---

### Recommendation Needed

**Decision Point**: Which option should be implemented?

**Factors to Consider**:
1. Current test complexity - are tests already verbose?
2. Number of integration tests planned
3. Team familiarity with shell scripting vs Python
4. Maintenance burden tolerance
5. Time available for implementation

**Suggested Approach**: Start with Option B (Basic Helpers) and evolve to Option C if needed.

**Rationale**:
- Option A may lead to repetitive, hard-to-maintain tests
- Option B provides good balance of simplicity and utility
- Option C can be added incrementally if Option B proves insufficient

---

## Question 2: IAM Policy Creation and Management

### Context

A read-only IAM policy is needed for AWS CLI verification. The policy must be created in ephemeral AWS accounts (4-hour lifetime).

### Options

#### Option A: Manual Creation by Human

**Description**: Provide IAM policy JSON and instructions. Human creates policy manually in AWS console or via CLI.

**Pros**:
- Simple, no automation needed
- Human verifies policy before use
- Clear audit trail

**Cons**:
- Manual step required for each ephemeral account
- Error-prone (copy-paste mistakes)
- Slow for frequent account rotation

---

#### Option B: Script-Based Creation

**Description**: Provide shell script that creates IAM policy and user/role automatically.

**Pros**:
- Fast, repeatable
- Reduces human error
- Can be run multiple times safely (idempotent)

**Cons**:
- Requires admin permissions to run script
- Script must handle errors gracefully
- More complex than manual approach

**Example**:
```bash
#!/bin/bash
# scripts/create-test-iam-policy.sh

POLICY_NAME="mk8-testing-read-only"
USER_NAME="mk8-test-user"

# Create policy
aws iam create-policy \
  --policy-name "$POLICY_NAME" \
  --policy-document file://iam-read-only-policy.json

# Create user
aws iam create-user --user-name "$USER_NAME"

# Attach policy
aws iam attach-user-policy \
  --user-name "$USER_NAME" \
  --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$POLICY_NAME"

# Create access key
aws iam create-access-key --user-name "$USER_NAME"
```

---

#### Option C: Agent-Driven Creation

**Description**: AI agent creates IAM policy when needed during test setup.

**Pros**:
- Fully automated
- Agent can adapt policy as needed
- No human intervention required

**Cons**:
- Agent needs admin permissions (security risk)
- Complex error handling
- Harder to audit
- May not work in all environments

---

### Recommendation Needed

**Decision Point**: How should the IAM policy be created and managed?

**Factors to Consider**:
1. Frequency of AWS account rotation
2. Availability of admin permissions
3. Security requirements
4. Automation vs control trade-off

**Suggested Approach**: Option B (Script-Based Creation)

**Rationale**:
- Balances automation with control
- Fast enough for 4-hour account rotation
- Human can review script before running
- Can be version-controlled and tested

---

## Question 3: Credential Validation Strategy

### Context

Tests need valid credentials to run. Should tests validate credentials before running, and how should they handle invalid credentials?

### Options

#### Option A: Fail Fast

**Description**: Tests check credentials at startup and fail immediately if invalid.

**Pros**:
- Clear error messages
- Saves time (don't run tests that will fail)
- Easy to debug

**Cons**:
- Additional validation code
- May slow down test startup

---

#### Option B: Fail on First Use

**Description**: Tests don't validate credentials upfront, just fail when first kubectl/aws command fails.

**Pros**:
- Simpler implementation
- No validation overhead
- Tests may partially succeed

**Cons**:
- Less clear error messages
- Wastes time running tests that will fail
- Harder to debug

---

#### Option C: Retry with Guidance

**Description**: Tests detect credential failures and provide guidance for fixing them, with retry option.

**Pros**:
- Best user experience
- Helpful error messages
- Allows fixing credentials without restarting

**Cons**:
- Most complex to implement
- May mask real test failures

---

### Recommendation Needed

**Decision Point**: How should tests handle credential validation?

**Suggested Approach**: Option A (Fail Fast) with clear error messages

**Rationale**:
- Better developer experience
- Saves time in CI/CD
- Clear separation between setup issues and test failures

---

## Question 4: Helper Function Language

### Context

If helper functions are provided (Option B or C from Question 1), should they be in shell (BATS) or Python (pytest) or both?

### Options

#### Option A: Shell Only

**Pros**:
- Works with BATS tests
- Simple, no Python dependency
- Easy to understand

**Cons**:
- Can't use in pytest tests
- Shell scripting limitations

---

#### Option B: Python Only

**Pros**:
- Works with pytest tests
- Better error handling
- Type hints, IDE support

**Cons**:
- Can't use in BATS tests
- Requires Python in test environment

---

#### Option C: Both Shell and Python

**Pros**:
- Works with all tests
- Best of both worlds

**Cons**:
- Duplicate implementation
- More maintenance burden
- Risk of inconsistency

---

### Recommendation Needed

**Decision Point**: Which language(s) for helper functions?

**Factors to Consider**:
1. Which test framework is used more (BATS vs pytest)?
2. Team language preferences
3. Maintenance capacity

**Suggested Approach**: Start with shell (Option A), add Python if needed

**Rationale**:
- BATS tests likely to use verification more
- Shell is simpler for CLI tool wrappers
- Can add Python later if pytest tests need it

---

## Question 5: Resource Cleanup Responsibility

### Context

Integration tests create resources (clusters, AWS resources). Should verification tools help with cleanup?

### Options

#### Option A: No Cleanup Helpers

**Description**: Tests are responsible for their own cleanup.

**Pros**:
- Simpler verification tool scope
- Tests have full control

**Cons**:
- Cleanup code duplicated across tests
- Orphaned resources if tests fail

---

#### Option B: Cleanup Helpers Provided

**Description**: Provide helper functions for common cleanup operations.

**Pros**:
- Consistent cleanup patterns
- Easier to write tests
- Reduces orphaned resources

**Cons**:
- Additional code to maintain
- May not cover all cleanup scenarios

---

#### Option C: Automatic Cleanup

**Description**: Verification framework tracks resources and cleans up automatically.

**Pros**:
- No cleanup code in tests
- Guaranteed cleanup

**Cons**:
- Complex to implement
- May clean up resources that should persist
- Harder to debug

---

### Recommendation Needed

**Decision Point**: Should verification tools provide cleanup functionality?

**Suggested Approach**: Option A (No Cleanup Helpers) initially

**Rationale**:
- Cleanup is orthogonal to verification
- Tests should own their lifecycle
- Can add cleanup helpers later if needed

---

## Resolution Process

These questions should be resolved:

1. **During Requirements Review**: Get user input on priorities and preferences
2. **During Design Phase**: Make technical decisions based on requirements
3. **Iteratively**: Start with minimal scope, expand if needed

## Notes for Future Agents

When resolving these questions:

1. **Consider current state**: Review existing tests to understand patterns
2. **Start minimal**: Can always add more functionality later
3. **Get user input**: Ask user for preferences on scope and approach
4. **Document decisions**: Update this file with final decisions and rationale
5. **Be pragmatic**: Choose solutions that balance utility with maintainability
