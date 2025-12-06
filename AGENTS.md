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
- **Project Structure**: ✅ Complete
- **Specs**: 4 features documented (1 implemented, 3 planned)
- **Virtual Environment**: `.venv/` (Python 3.12.3)

### Active Development
- Following **Test-Driven Development** (Red-Green-Refactor)
- Using **Click** for CLI framework
- Code style: **Black** (line-length=88)
- Type checking: **mypy** (strict mode)
- Coverage requirement: **80% minimum**

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

### Testing Pattern
```python
# 1. RED: Write failing test
def test_feature():
    assert feature.method() == expected

# 2. GREEN: Implement to pass
def method():
    return expected

# 3. REFACTOR: Improve while keeping green
```

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

# Install/reinstall
.venv/bin/pip install -e ".[dev]"

# Run CLI
.venv/bin/mk8 --help
.venv/bin/mk8 version
```

## Session Start Checklist

When starting a new session:
- [ ] Read this file (AGENTS.md)
- [ ] Skim `.claude/steering/product.md` for project context
- [ ] Skim `.claude/steering/tech.md` for coding standards
- [ ] Check `.claude/specs/` for relevant feature specs
- [ ] Run tests to verify environment: `.venv/bin/pytest tests/unit/ -v`
- [ ] Understand current task from user or review spec tasks.md files
