# Quality Remediation Task List

**Date**: 2025-12-06
**Approach**: Fix by module, not by tool
**Workflow**: For each module: mypy → flake8 → tests → verify all pass → commit

---

## Module-by-Module Remediation Order

### Priority 1: Critical Infrastructure (Shared Dependencies)

These modules are used by others, so fix them first.

#### Module 1: mk8/integrations/kubectl_client.py
**Issues**: 2 flake8, 3 mypy, 3 test failures
**Estimated Time**: 2 hours

**Tasks**:
1. Install type stubs: `pip install types-PyYAML boto3-stubs`
2. Fix mypy errors:
   - Line 127: Fix `no-any-return` - properly type json.loads return
   - Line 318: Fix `no-any-return` - properly type return value
3. Fix flake8 errors:
   - Line 69: Break long line (E501)
   - Line 129: Fix f-string missing placeholders (F541)
4. Fix unit tests (DO NOT DELETE):
   - `test_get_resource_returns_true_when_exists`: Fix mock to return valid JSON string
   - `test_get_resource_returns_false_when_not_found`: Update test expectations to match actual behavior (raises exception, not returns False)
   - `test_get_resource_uses_correct_namespace`: Fix mock.stdout to be string not Mock object
5. Verify all checks pass:
   ```bash
   python -m mypy mk8/integrations/kubectl_client.py
   python -m flake8 mk8/integrations/kubectl_client.py
   python -m pytest tests/unit/integrations/test_kubectl_client.py -v
   ```
6. Commit: `fix(kubectl): resolve type errors, linting issues, and test failures`

---

#### Module 2: mk8/integrations/kind_client.py
**Issues**: 3 flake8, 2 mypy, 0 test failures (but low coverage)
**Estimated Time**: 1 hour

**Tasks**:
1. Fix mypy errors:
   - Line 5: Already fixed by installing types-PyYAML in Module 1
   - Line 45: Add return type annotation `-> None`
2. Fix flake8 errors:
   - Line 87: Break long line (E501)
   - Line 245: Break long line (E501)
   - Line 256: Break long line (E501)
3. Run existing tests (should pass):
   ```bash
   python -m pytest tests/unit/integrations/test_kind_client.py -v
   ```
4. Verify all checks pass:
   ```bash
   python -m mypy mk8/integrations/kind_client.py
   python -m flake8 mk8/integrations/kind_client.py
   python -m pytest tests/unit/integrations/test_kind_client.py -v
   ```
5. Commit: `fix(kind): resolve type annotations and line length issues`

---

#### Module 3: mk8/integrations/helm_client.py
**Issues**: 1 flake8, 2 mypy, 0 test failures (but low coverage)
**Estimated Time**: 1 hour

**Tasks**:
1. Fix flake8 errors:
   - Line 4: Remove unused import `time` (F401)
2. Fix mypy errors:
   - Line 5: Already fixed by installing types-PyYAML in Module 1
   - Line 275: Fix `no-any-return` - properly type yaml.safe_load return
3. Run existing tests (should pass):
   ```bash
   python -m pytest tests/unit/integrations/test_helm_client.py -v
   ```
4. Verify all checks pass:
   ```bash
   python -m mypy mk8/integrations/helm_client.py
   python -m flake8 mk8/integrations/helm_client.py
   python -m pytest tests/unit/integrations/test_helm_client.py -v
   ```
5. Commit: `fix(helm): remove unused import and fix return type`

---

#### Module 4: mk8/integrations/aws_client.py
**Issues**: 0 flake8, 3 mypy, 0 test failures
**Estimated Time**: 30 minutes

**Tasks**:
1. Fix mypy errors:
   - Lines 3-5: Already fixed by installing boto3-stubs in Module 1
2. Verify all checks pass:
   ```bash
   python -m mypy mk8/integrations/aws_client.py
   python -m flake8 mk8/integrations/aws_client.py
   python -m pytest tests/unit/integrations/test_aws_client.py -v
   ```
3. Commit: `fix(aws): resolve type stub issues with boto3-stubs`

---

#### Module 5: mk8/integrations/kubeconfig.py
**Issues**: 1 flake8, 1 mypy, 0 test failures
**Estimated Time**: 30 minutes

**Tasks**:
1. Fix mypy errors:
   - Line 4: Already fixed by installing types-PyYAML in Module 1
2. Fix flake8 errors:
   - Line 36: Break long line (E501)
3. Verify all checks pass:
   ```bash
   python -m mypy mk8/integrations/kubeconfig.py
   python -m flake8 mk8/integrations/kubeconfig.py
   python -m pytest tests/unit/integrations/test_kubeconfig.py -v
   ```
4. Commit: `fix(kubeconfig): resolve line length issue`

---

#### Module 6: mk8/integrations/file_io.py
**Issues**: 0 flake8 in source, 6 flake8 in tests, 0 mypy, 0 test failures
**Estimated Time**: 30 minutes

**Tasks**:
1. Fix flake8 errors in test file:
   - tests/unit/integrations/test_file_io.py lines 37, 66, 79, 91, 104, 315: Break long lines (E501)
2. Verify all checks pass:
   ```bash
   python -m mypy mk8/integrations/file_io.py
   python -m flake8 mk8/integrations/file_io.py tests/unit/integrations/test_file_io.py
   python -m pytest tests/unit/integrations/test_file_io.py -v
   ```
3. Commit: `fix(file_io): resolve line length issues in tests`

---

### Priority 2: Business Logic Layer

#### Module 7: mk8/business/credential_manager.py
**Issues**: 2 flake8, 0 mypy, 4 test issues (F811 in tests)
**Estimated Time**: 1 hour

**Tasks**:
1. Fix flake8 errors in source:
   - Line 15: Remove unused import `ConfigurationError` (F401)
   - Line 245: Break long line (E501)
2. Fix flake8 errors in test file:
   - tests/unit/business/test_credential_manager.py lines 255, 281, 425, 428: Fix redefinition of `call` (F811)
   - Import `call` once at top, or use different variable names
3. Verify all checks pass:
   ```bash
   python -m mypy mk8/business/credential_manager.py
   python -m flake8 mk8/business/credential_manager.py tests/unit/business/test_credential_manager.py
   python -m pytest tests/unit/business/test_credential_manager.py -v
   ```
4. Commit: `fix(credentials): remove unused import and fix test import issues`

---

#### Module 8: mk8/business/crossplane_manager.py
**Issues**: 1 flake8, 1 mypy, 0 test failures
**Estimated Time**: 1 hour

**Tasks**:
1. Fix flake8 errors:
   - Line 81: Break long line (E501)
2. Fix mypy errors:
   - Line 136: Fix return type incompatibility (returns dict but should return bool)
   - Investigate function signature and fix either return statement or return type annotation
3. Verify all checks pass:
   ```bash
   python -m mypy mk8/business/crossplane_manager.py
   python -m flake8 mk8/business/crossplane_manager.py
   python -m pytest tests/unit/business/test_crossplane_manager.py -v
   ```
4. Commit: `fix(crossplane-manager): fix return type and line length`

---

#### Module 9: mk8/business/bootstrap_manager.py
**Issues**: 9 flake8, 2 mypy, 0 test failures (but low coverage)
**Estimated Time**: 2 hours

**Tasks**:
1. Fix flake8 errors:
   - Line 7: Remove unused import `ClusterNotFoundError` (F401)
   - Lines 52, 91, 278, 299: Break long lines (E501)
   - Lines 144, 147, 148, 209: Fix f-strings missing placeholders (F541) - convert to regular strings
2. Fix mypy errors:
   - Line 121: Already fixed by installing types-PyYAML in Module 1
   - Line 283: Fix `PrerequisiteStatus.running` attribute error
     - Check PrerequisiteStatus model definition
     - Either add `running` attribute or fix the reference
3. Run existing tests (should pass):
   ```bash
   python -m pytest tests/unit/business/test_bootstrap_manager.py -v
   ```
4. Verify all checks pass:
   ```bash
   python -m mypy mk8/business/bootstrap_manager.py
   python -m flake8 mk8/business/bootstrap_manager.py
   python -m pytest tests/unit/business/test_bootstrap_manager.py -v
   ```
5. Commit: `fix(bootstrap-manager): resolve linting and type errors`

---

#### Module 10: mk8/business/crossplane_installer.py
**Issues**: 1 flake8, 12 mypy, 0 test failures (but low coverage)
**Estimated Time**: 3 hours

**Tasks**:
1. Fix flake8 errors:
   - Line 160: Break long line (E501)
2. Fix mypy errors (HIGH PRIORITY - these are actual bugs):
   - Line 61: Fix CredentialManager constructor call - add missing arguments (file_io, aws_client, output)
   - Lines 81, 87, 146, 182, 186, 190, 221, 233, 245, 255: Fix "bool not callable" errors (10 occurrences)
     - These are likely method calls that should be `self.method()` not `self.method`
   - Lines 377, 378: Fix `AWSCredentials.session_token` attribute errors
     - Check AWSCredentials model definition
     - Either add session_token field or remove references
3. Run existing tests (should pass):
   ```bash
   python -m pytest tests/unit/business/test_crossplane_installer.py -v
   ```
4. Verify all checks pass:
   ```bash
   python -m mypy mk8/business/crossplane_installer.py
   python -m flake8 mk8/business/crossplane_installer.py
   python -m pytest tests/unit/business/test_crossplane_installer.py -v
   ```
5. Commit: `fix(crossplane-installer): fix constructor calls and method invocations`

---

#### Module 11: mk8/business/verification.py (test file issues)
**Issues**: 0 flake8 in source, 2 flake8 in tests, 0 mypy, 0 test failures
**Estimated Time**: 30 minutes

**Tasks**:
1. Fix flake8 errors in test files:
   - tests/unit/business/test_verification_models.py line 130: Break long line (E501)
   - tests/unit/business/test_verification_properties.py line 189: Break long line (E501)
2. Verify all checks pass:
   ```bash
   python -m mypy mk8/business/verification.py
   python -m flake8 mk8/business/verification.py tests/unit/business/test_verification*.py
   python -m pytest tests/unit/business/test_verification*.py -v
   ```
3. Commit: `fix(verification): resolve line length issues in tests`

---

### Priority 3: CLI Layer

#### Module 12: mk8/cli/commands/config.py
**Issues**: 2 flake8, 0 mypy, 1 test failure
**Estimated Time**: 1.5 hours

**Tasks**:
1. Fix flake8 errors:
   - Lines 95, 99: Break long lines (E501)
2. Fix unit test (DO NOT DELETE):
   - tests/unit/cli/test_main.py::test_config_command_routes_correctly
   - Mock click.prompt to avoid interactive prompt
   - Mock CredentialManager to avoid actual credential operations
3. Verify all checks pass:
   ```bash
   python -m mypy mk8/cli/commands/config.py
   python -m flake8 mk8/cli/commands/config.py
   python -m pytest tests/unit/cli/test_config_command.py -v
   python -m pytest tests/unit/cli/test_main.py::TestCommandRouting::test_config_command_routes_correctly -v
   ```
4. Commit: `fix(cli-config): resolve line length and test mocking issues`

---

#### Module 13: mk8/cli/commands/crossplane.py
**Issues**: 3 flake8, 1 mypy, 0 test failures (but low coverage)
**Estimated Time**: 1.5 hours

**Tasks**:
1. Fix flake8 errors:
   - Line 215: Fix f-string missing placeholders (F541)
   - Lines 248, 251: Break long lines (E501)
2. Fix mypy errors:
   - Line 57: Fix CredentialManager constructor call - add missing arguments (file_io, aws_client)
3. Run existing tests (should pass):
   ```bash
   python -m pytest tests/unit/cli/test_crossplane_command.py -v
   ```
4. Verify all checks pass:
   ```bash
   python -m mypy mk8/cli/commands/crossplane.py
   python -m flake8 mk8/cli/commands/crossplane.py
   python -m pytest tests/unit/cli/test_crossplane_command.py -v
   ```
5. Commit: `fix(cli-crossplane): fix constructor call and linting issues`

---

### Priority 4: Final Verification

#### Task 14: Run Full Test Suite
**Estimated Time**: 30 minutes

**Tasks**:
1. Run all quality checks on entire codebase:
   ```bash
   python -m black mk8/ tests/
   python -m flake8 mk8/ tests/
   python -m mypy mk8/
   python -m pytest tests/unit/ -v --cov=mk8 --cov-report=term-missing
   ```
2. Verify results:
   - ✅ Black: No files reformatted
   - ✅ Flake8: 0 violations
   - ✅ Mypy: 0 errors
   - ✅ Pytest: All tests passing
   - ⚠️ Coverage: Will still be ~53% (coverage improvement is separate effort)
3. If any issues found, go back to relevant module and fix
4. Commit: `chore: verify all quality checks pass`

---

#### Task 15: Update Documentation
**Estimated Time**: 30 minutes

**Tasks**:
1. Update `.claude/QUALITY-ISSUES-ASSESSMENT.md`:
   - Mark all issues as resolved
   - Update status to PASSING
   - Add "Resolved" section with commit references
2. Update `AGENTS.md` if any new patterns discovered
3. Commit: `docs: update quality assessment with resolution status`
4. Push all commits to remote

---

## Summary

### Total Estimated Time
- **Modules 1-6 (Integrations)**: 5.5 hours
- **Modules 7-11 (Business Logic)**: 8.5 hours
- **Modules 12-13 (CLI)**: 3 hours
- **Tasks 14-15 (Verification)**: 1 hour
- **Total**: 18 hours

### Module Order
1. kubectl_client (critical, has test failures)
2. kind_client
3. helm_client
4. aws_client
5. kubeconfig
6. file_io
7. credential_manager
8. crossplane_manager
9. bootstrap_manager
10. crossplane_installer (most complex)
11. verification
12. config (CLI)
13. crossplane (CLI)
14. Full verification
15. Documentation update

### Key Principles
- ✅ Fix by module, not by tool
- ✅ Order: mypy → flake8 → tests → verify → commit
- ✅ DO NOT delete tests
- ✅ DO NOT change tests unless clearly wrong
- ✅ Commit after each module
- ✅ Run all three checks before committing

### Success Criteria
- ✅ Flake8: 0 violations
- ✅ Mypy: 0 errors
- ✅ Pytest: 100% tests passing (329+ tests)
- ⚠️ Coverage: ~53% (improvement is separate project)

---

## Notes

**Coverage Improvement**: Not included in this task list. Coverage is currently 53.39% because bootstrap and crossplane features lack tests. Writing comprehensive tests for these modules would add 8-12 hours and is a separate effort that should be tracked in a different task list.

**Type Stubs**: Install once at the beginning (Module 1), benefits all subsequent modules.

**Test Philosophy**: Tests are the source of truth. If a test fails, first verify the test is correct. Only modify tests if they are clearly testing the wrong behavior or have incorrect mocks.
