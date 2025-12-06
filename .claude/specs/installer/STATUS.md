# Installer Spec - Current Status

## Overview

The installer spec has been refactored into two separate specs:
- **installer**: MVP - Basic prerequisite checking for Linux only
- **installer-future**: Polished product with multi-platform support and advanced features

## Completed Work

### Data Models (Tasks 1-3)

#### ✅ PrerequisiteStatus (task 1 & 1.1)
- **Location**: `mk8/integrations/prerequisite_models.py`
- **Tests**: `tests/unit/integrations/test_prerequisite_models.py`
- **Status**: COMPLETE with full test coverage (13 tests passing)
- **Note**: Implementation includes `version`, `version_ok`, and `path` fields from the future spec

#### ✅ PrerequisiteResults (task 2)
- **Location**: `mk8/integrations/prerequisite_models.py`
- **Tests**: `tests/unit/integrations/test_prerequisite_results.py`
- **Status**: COMPLETE with full test coverage (14 tests passing)
- **Implemented**: `all_satisfied()`, `get_missing()`, and `get_status_summary()` methods

#### ✅ VerificationResult (task 3)
- **Location**: `mk8/business/verification_models.py`
- **Tests**: Not yet written (task 3.1 is optional)
- **Status**: COMPLETE - Implementation done
- **Implemented**: `is_verified()` method

#### ✅ PlatformInfo (installer-future task 1)
- **Location**: `mk8/integrations/platform_models.py`
- **Tests**: `tests/unit/integrations/test_platform_models.py`
- **Status**: COMPLETE with full test coverage (13 tests passing)
- **Note**: This is from the future spec but was implemented early

## What Needs to Be Done

### Immediate Next Steps (installer MVP)

**Current Progress**: 3 of 15 core tasks complete (20%)

#### Next Task: Task 4 - VerificationError Exception
- Create `VerificationError` exception class extending `MK8Error`
- Location: `mk8/core/errors.py` (add to existing file)
- Optional: Unit tests (task 4.1) and property tests (task 4.2)

#### Remaining Core Tasks:

1. **Task 4**: Implement `VerificationError` exception ⬅️ **NEXT**
   - Add to existing error hierarchy in `mk8/core/errors.py`

2. **Tasks 5-10**: Implement `PrerequisiteChecker` class
   - Create `mk8/integrations/prerequisites.py`
   - Implement tool checking methods (Docker, kind, kubectl)
   - Implement daemon checking for Docker
   - Aggregate all checks in `check_all()` method

3. **Task 11**: Implement basic installation instructions in `VerificationManager`
   - Create `mk8/business/verification.py`
   - Implement `get_installation_instructions()` method
   - Provide installation guidance for each tool

4. **Tasks 12-13**: Complete `VerificationManager` class
   - Implement `verify_mk8_installed()` method
   - Implement complete `verify()` flow
   - Wire together all prerequisite checks

5. **Task 14**: Implement `mk8 verify` CLI command
   - Create `mk8/cli/commands/verify.py`
   - Add command to main CLI group
   - Display results and instructions

6. **Task 15**: Final checkpoint - ensure all tests pass
   - Run full test suite
   - Verify 80%+ coverage
   - Confirm all functionality works

### Future Enhancements (installer-future)

The installer-future spec contains 37 tasks for:
- Multi-platform support (macOS, Windows/WSL2)
- Platform-specific installation instructions
- Interactive installation with prompts
- Automatic prerequisite installation
- Version checking and comparison
- Update detection
- Virtual environment handling
- Advanced error handling
- `mk8 uninstall` command
- Installation logging
- Standalone install.sh script
- PATH configuration

## Test Coverage

### Passing Tests (40 total)
- ✅ `tests/unit/integrations/test_platform_models.py` (13 tests)
- ✅ `tests/unit/integrations/test_prerequisite_models.py` (13 tests)
- ✅ `tests/unit/integrations/test_prerequisite_results.py` (14 tests)

### Tests Not Yet Written
- Task 3.1: Unit tests for `VerificationResult` (optional)
- Task 4.1: Unit tests for `VerificationError` (optional)
- Tasks 5.1-10.1: Unit tests for `PrerequisiteChecker` (optional)
- Task 11.1: Unit tests for installation instructions (optional)
- Tasks 12.1-13.1: Unit tests for `VerificationManager` (optional)
- Task 14.1: Unit tests for verify command (optional)
- Tasks 2.2, 2.3, 3.2, 4.2, 6.2, 10.2, 11.2, 11.3, 12.2: Property-based tests (optional)

## File Structure

```
mk8/
├── integrations/
│   ├── __init__.py
│   ├── platform_models.py          ✅ COMPLETE (future spec)
│   ├── prerequisite_models.py      ✅ COMPLETE (PrerequisiteStatus + PrerequisiteResults)
│   └── prerequisites.py            ⏳ TODO (PrerequisiteChecker - tasks 5-10)
├── business/
│   ├── __init__.py
│   ├── verification_models.py      ✅ COMPLETE (VerificationResult)
│   └── verification.py             ⏳ TODO (VerificationManager - tasks 11-13)
├── core/
│   └── errors.py                   ⏳ TODO (add VerificationError - task 4)
└── cli/
    └── commands/
        └── verify.py               ⏳ TODO (verify command - task 14)

tests/unit/integrations/
├── test_platform_models.py          ✅ PASSING (13 tests)
├── test_prerequisite_models.py      ✅ PASSING (13 tests)
└── test_prerequisite_results.py     ✅ PASSING (14 tests)
```

## How to Continue

### To complete the MVP installer:

1. **Continue with Task 4**: Implement `VerificationError`
   ```bash
   # Add VerificationError to mk8/core/errors.py
   # This extends the existing MK8Error hierarchy
   ```

2. **Then implement PrerequisiteChecker** (tasks 5-10):
   ```bash
   # Create mk8/integrations/prerequisites.py
   # Implement tool checking logic
   # Test with: python -m pytest tests/unit/integrations/ -v --no-cov
   ```

3. **Then implement VerificationManager** (tasks 11-13):
   ```bash
   # Create mk8/business/verification.py
   # Wire together all the pieces
   ```

4. **Finally add CLI command** (task 14):
   ```bash
   # Create mk8/cli/commands/verify.py
   # Test end-to-end: python -m mk8 verify
   ```

5. **Run full test suite** (task 15):
   ```bash
   python -m pytest tests/unit/ -v
   ```

### To work on future enhancements:

1. Open `.claude/specs/installer-future/tasks.md`
2. Note that tasks 1 and 9 are already complete
3. Start with task 2 (OS detection) or task 7 (version parsing)

## Notes

- The `PrerequisiteStatus` model was implemented with extra fields (version, version_ok, path) that are needed for the future spec. This is fine and won't affect the MVP.
- The MVP installer focuses on Linux-only, basic checks, and simple instructions.
- All advanced features (multi-platform, interactive mode, auto-install, etc.) are in the future spec.
- **Testing approach**: Tasks marked with `*` are optional (primarily tests). Core implementation tasks are required. This allows for faster MVP delivery while maintaining the option for comprehensive testing.
- **Property-based testing**: The design includes 9 correctness properties. Property tests are optional but recommended for verifying universal behaviors across all inputs.
- **Test framework**: Property-based tests should use Hypothesis library with minimum 100 iterations per test.
