# AI Agent Context Guide

This file provides orientation for AI agents working on the mk8 project. Read this first when starting a new session.

## Quick Project Overview

**mk8** is a Python CLI tool for managing Kubernetes infrastructure on AWS using a multi-tier cluster architecture with Crossplane. It automates the creation of:
1. Local bootstrap cluster (kind)
2. AWS management cluster (EKS)
3. AWS workload clusters (EKS)

**Version**: 0.1.0 (Alpha)
**Language**: Python 3.8+
**Development**: Spec-driven, test-driven development (TDD)

## Essential Reading (In Order)

### 1. Start Here - Project Documentation
```
README.md                              # Installation, quick start, development setup
.claude/steering/product.md            # What mk8 does, architecture, features
.claude/steering/tech.md               # Tech stack, coding standards, best practices
.claude/steering/structure.md          # Project organization, module architecture
```

### 2. Specifications (Feature Design)
```
.claude/specs/                         # All feature specifications
├── mk8-cli/                          # CLI framework (COMPLETE)
│   ├── requirements.md               # EARS format requirements
│   ├── design.md                     # Architecture and components
│   └── tasks.md                      # Implementation plan
├── aws-credentials-management/       # AWS credential handling (PLANNED)
├── kubeconfig-file-handling/         # kubectl config management (PLANNED)
└── local-bootstrap-cluster/          # Bootstrap cluster lifecycle (PLANNED)
```

### 3. Implementation Status
```
mk8/                                   # Main package
├── cli/                              # ✅ COMPLETE - CLI framework
│   ├── main.py                       # Entry point, Click setup, routing
│   ├── output.py                     # Output formatting
│   └── commands/                     # Command handlers
│       └── version.py                # ✅ COMPLETE
├── core/                             # ✅ COMPLETE - Core infrastructure
│   ├── errors.py                     # Exception hierarchy, exit codes
│   ├── logging.py                    # Logger with verbose support
│   └── version.py                    # Semantic versioning
├── business/                         # 🚧 EMPTY - Future business logic
└── integrations/                     # 🚧 EMPTY - Future external clients
```

### 4. Tests (50 tests, 82.44% coverage)
```
tests/
├── unit/                             # ✅ All passing
│   ├── cli/                          # CLI layer tests
│   └── core/                         # Core layer tests
└── integration/                      # 🚧 Future integration tests
```

## Development Context

### Current State
- **CLI Framework**: ✅ Complete with 82.44% test coverage
- **Installer MVP**: 🚧 In Progress (1/15 tasks complete, PrerequisiteResults implementation needed)
- **Project Structure**: ✅ Complete
- **Specs**: 10 features (1 complete, 1 in progress, 1 planned, 6 requirements-only, 1 deprecated)
- **Virtual Environment**: `.venv/` (Python 3.12.3)

### Active Development
- Following **Spec-Driven Development** (Requirements → Design → Tasks → Implementation)
- Following **Test-Driven Development** (Red-Green-Refactor)
- Using **Click** for CLI framework
- Code style: **Black** (line-length=88)
- Type checking: **mypy** (strict mode)
- Coverage requirement: **80% minimum**

### Spec-Driven Workflow
This project uses a three-phase methodology for feature development:

1. **Requirements Phase**: User stories with EARS format acceptance criteria
2. **Design Phase**: Architecture, components, data models, Mermaid diagrams
3. **Tasks Phase**: Numbered implementation tasks with requirement traceability

**Key Rules**:
- Never skip phases (Requirements → Design → Tasks)
- Each phase requires explicit approval before proceeding
- Tasks are executed one at a time with status tracking
- All specs live in `.claude/specs/{feature-name}/`
- Status files track progress for in-progress features

### Key Workflows

**Running Tests**:
```bash
.venv/bin/pytest tests/unit/ -v              # All tests with coverage
.venv/bin/pytest tests/unit/cli/ -v --no-cov # CLI tests only
.venv/bin/pytest --cov=mk8 --cov-report=html # With HTML report
```

**Code Quality**:
```bash
.venv/bin/black mk8/ tests/                  # Format code
.venv/bin/flake8 mk8/ tests/                 # Lint code
.venv/bin/mypy mk8/                          # Type check
```

**Git Operations**:
```bash
# IMPORTANT: Always disable git pager to avoid blocking
git --no-pager log --oneline -10             # View recent commits
git --no-pager status                        # Check status
git --no-pager diff                          # View changes
git --no-pager log --oneline --graph -10     # View commit graph
```

**Running CLI**:
```bash
.venv/bin/mk8 --help                         # Via installed package
python -m mk8 --help                         # Via module
```

## Architecture Quick Reference

### Layered Architecture
```
CLI Layer          → Click-based parsing, routing, help
Command Layer      → Command handlers (bootstrap, config, version)
Business Logic     → Core functionality (future)
Integration Layer  → External clients (kind, kubectl, AWS) (future)
Infrastructure     → Logging, errors, I/O
```

### Error Handling Pattern
```python
# All custom errors inherit from MK8Error
# Always include suggestions for remediation
raise PrerequisiteError(
    "Docker is not running",
    suggestions=["Start Docker Desktop", "Run 'systemctl start docker'"]
)
```

### Testing Pattern - Token-Efficient TDD

**Batched Test-Driven Development**:
To optimize token usage while maintaining TDD rigor, follow this approach:

1. **Batch Test Creation**: Write all tests for a component/layer at once
2. **Red Phase**: Run tests to verify they all fail
3. **Green Phase**: Implement component to make all tests pass
4. **Refactor**: Clean up code while keeping tests green

**Why This Works**:
- Reduces context switching between test and implementation
- Allows seeing full test suite structure upfront
- Minimizes file reads and redundant explanations
- Maintains TDD benefits (tests first, fail-pass cycle)
- More efficient token usage without sacrificing correctness

**Implementation Order**:
- Group by architectural layer (data models → integrations → business logic → CLI)
- Complete one component fully before moving to next
- Property tests can replace many unit tests (one property = dozens of examples)
- Defer integration tests to checkpoints between major phases

**Example**:
```python
# Phase 1: Write all tests for FileIO
def test_read_config_file(): ...
def test_write_config_file(): ...
def test_secure_permissions(): ...

# Phase 2: Run tests (all should fail)
# Phase 3: Implement FileIO to pass all tests
# Phase 4: Refactor if needed

## Common Tasks

### Adding a New Feature
1. Read spec: `.claude/specs/<feature>/requirements.md`
2. Read design: `.claude/specs/<feature>/design.md`
3. Follow tasks: `.claude/specs/<feature>/tasks.md`
4. Write tests first (TDD)
5. Implement incrementally
6. Maintain >80% coverage

### Understanding a Module
1. Read module docstring
2. Check tests: `tests/unit/<module>/test_*.py`
3. Review related spec if exists

### Finding Configuration
- **Package**: `setup.py`, `pyproject.toml`
- **Testing**: `pyproject.toml` [tool.pytest.ini_options]
- **Linting**: `.flake8`
- **Type Checking**: `pyproject.toml` [tool.mypy]
- **Formatting**: `pyproject.toml` [tool.black]
- **Claude Code**: `.claude/settings.json`

## Important Patterns

### File Structure Conventions
- **Tests mirror source**: `tests/unit/cli/test_main.py` ↔ `mk8/cli/main.py`
- **One test class per source class**: `class TestFeature` tests `class Feature`
- **Descriptive test names**: `test_method_with_invalid_input_raises_error`

### Documentation Requirements
- **Docstrings**: All public functions and classes
- **Type hints**: All function signatures (mypy strict mode)
- **Error messages**: Always include suggestions
- **Comments**: Only for non-obvious logic

### Import Organization
```python
# Standard library
import sys
from typing import Optional

# Third-party
import click
from dataclasses import dataclass

# Local
from mk8.core.errors import MK8Error
from mk8.cli.output import OutputFormatter
```

## When You Get Stuck

1. **Check specs**: `.claude/specs/<feature>/` for requirements and design
2. **Check steering docs**: `.claude/steering/` for guidelines
3. **Check tests**: Often show usage examples
4. **Check existing code**: Similar patterns elsewhere
5. **Read pyproject.toml**: Tool configurations

## Next Steps (Likely Tasks)

Based on current state, you'll probably work on:

1. **AWS Credentials Management** - Implement `mk8 config` command
   - Spec: `.claude/specs/aws-credentials-management/`
   - Status: Requirements complete, needs design & implementation

2. **kubectl Config Handling** - Safe kubeconfig merging
   - Spec: `.claude/specs/kubeconfig-file-handling/`
   - Status: Requirements complete, needs design & implementation

3. **Bootstrap Cluster** - Implement `mk8 bootstrap` commands
   - Spec: `.claude/specs/local-bootstrap-cluster/`
   - Status: Requirements complete, needs design & implementation

## Key Constraints

- ✅ All file operations allowed within repository
- ✅ pytest, black, flake8, mypy allowed via `.venv/bin/`
- ⚠️ Must follow TDD (write tests first)
- ⚠️ Must maintain 80% coverage minimum
- ⚠️ Must pass all quality checks (black, flake8, mypy)

## Quick Command Reference

```bash
# Testing
.venv/bin/pytest tests/unit/ -v

# Code quality
.venv/bin/black mk8/ tests/
.venv/bin/flake8 mk8/ tests/
.venv/bin/mypy mk8/

# Git (ALWAYS use --no-pager to avoid blocking)
git --no-pager status
git --no-pager log --oneline -10
git --no-pager diff
git add <files>
git commit -m "message"
git push

# Install/reinstall
.venv/bin/pip install -e ".[dev]"

# Run CLI
.venv/bin/mk8 --help
.venv/bin/mk8 version
```

## Session Start Checklist

When starting a new session:
- [ ] Read this file (AGENTS.md)
- [ ] **Check project status**: Read `.claude/specs/SPECS-STATUS.md` to understand what's complete, in progress, and planned
- [ ] **Check active work**: If a spec is in progress, read its `STATUS.md` file (e.g., `.claude/specs/installer/STATUS.md`)
- [ ] Skim `.claude/steering/product.md` for project context
- [ ] Skim `.claude/steering/tech.md` for coding standards
- [ ] Check `.claude/specs/` for relevant feature specs
- [ ] Run tests to verify environment: `.venv/bin/pytest tests/unit/ -v`
- [ ] Understand current task from user or review spec tasks.md files

## Critical Git Usage Rules

**ALWAYS use `--no-pager` flag with git commands to prevent blocking:**

```bash
# ✅ CORRECT - Will not block
git --no-pager log --oneline -10
git --no-pager status
git --no-pager diff
git --no-pager log --oneline --graph -10

# ❌ WRONG - Will block and cause issues
git log --oneline -10
git status
git diff
```

This is critical because the pager (less/more) will block execution waiting for user input.

## Project Status Files

The project uses status tracking files to maintain context across sessions:

### `.claude/specs/SPECS-STATUS.md`
- **Purpose**: High-level overview of all feature specs
- **Contains**: Completion status, task counts, implementation order
- **When to read**: Start of every session to understand project state

### `.claude/specs/{feature-name}/STATUS.md`
- **Purpose**: Detailed status for in-progress features
- **Contains**: Completed work, failing tests, next steps, file structure
- **When to read**: When working on a specific feature
- **Example**: `.claude/specs/installer/STATUS.md` tracks the installer MVP implementation

### Status Indicators
- ✅ **COMPLETE**: Feature fully implemented and tested
- 🚧 **IN PROGRESS**: Active development with partial completion
- 📋 **PLANNED**: Design and tasks complete, ready for implementation
- 📝 **REQUIREMENTS ONLY**: Needs design and task planning
- ⚠️ **INCOMPLETE**: Tests exist but implementation missing
- ❌ **FAILING**: Tests failing, needs attention
