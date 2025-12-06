# Technical Stack and Guidelines

## Technology Stack

### Core Technologies
- **Language**: Python 3.8+
- **CLI Framework**: Click 8.0+ (decorator-based, hierarchical commands)
- **Testing**: pytest 7.0+ with pytest-cov, pytest-mock
- **Package Management**: pip with setuptools/pyproject.toml

### External Dependencies
- **AWS SDK**: boto3 (AWS API interactions)
- **Configuration**: PyYAML (YAML parsing)
- **HTTP**: requests (general HTTP client)

### Development Tools
- **Formatter**: Black (line-length=88)
- **Linter**: flake8 (PEP 8 compliance)
- **Type Checker**: mypy (strict type checking)
- **Version Control**: Git

### External Tools (Runtime Dependencies)
- **Docker**: Required for kind clusters
- **kind**: Kubernetes in Docker for local clusters
- **kubectl**: Kubernetes command-line tool
- **Crossplane**: Infrastructure provisioning (installed automatically)

## Code Organization

### Package Structure
```
mk8/
├── cli/              # CLI interface layer
│   ├── commands/     # Command implementations
│   ├── main.py       # Entry point and routing
│   └── output.py     # Output formatting
├── core/             # Core infrastructure
│   ├── errors.py     # Exception hierarchy
│   ├── logging.py    # Logging configuration
│   └── version.py    # Version management
├── business/         # Business logic (future)
└── integrations/     # External tool clients (future)
```

### Layered Architecture
1. **CLI Layer**: Click-based parsing, routing, help system
2. **Command Layer**: Command handlers (bootstrap, config, version)
3. **Business Logic**: Core functionality (cluster mgmt, credentials)
4. **Integration Layer**: External clients (kind, kubectl, AWS, Crossplane)
5. **Infrastructure**: File I/O, environment, logging

## Development Guidelines

### Test-Driven Development (TDD)
**Always follow Red-Green-Refactor cycle**:
1. **Red**: Write failing test first
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve code while keeping tests green

**Coverage Requirements**:
- Minimum 80% overall coverage (enforced by pytest)
- 100% coverage for critical paths (error handling, security)
- Run tests before every commit

### Code Style

**Python Style** (PEP 8 + Black):
```python
# Good: Black-formatted, type hints, docstrings
def format_error(message: str, suggestions: List[str]) -> str:
    """
    Format error message with suggestions.

    Args:
        message: Error description
        suggestions: List of remediation steps

    Returns:
        Formatted error string
    """
    lines = [f"Error: {message}"]
    # ... implementation
```

**Type Hints**:
- Required on all function signatures
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` for collections
- mypy strict mode enabled

**Docstrings**:
- Required for all public functions and classes
- Google or NumPy style
- Include Args, Returns, Raises sections

### Error Handling

**Custom Exception Hierarchy**:
```python
MK8Error (base)
├── PrerequisiteError      # Missing dependencies
├── ValidationError        # Invalid input
├── CommandError          # Execution failures
└── ConfigurationError    # Config issues
```

**Error Message Format**:
```
Error: <Clear description>

[Optional context]

Suggestions:
  • <Specific remediation step>
  • <Alternative solution>
```

**Exit Codes**:
- 0: Success
- 1: General error
- 2: Command error
- 3: Validation error
- 4: Prerequisite error
- 5: Configuration error
- 130: Keyboard interrupt

### Command Implementation

**Click Patterns**:
```python
@cli.command(context_settings={"allow_interspersed_args": True})
@click.option('--flag', '-f', is_flag=True, help='Description')
@click.pass_context
def command(ctx: click.Context, flag: bool) -> None:
    """Command description with examples."""
    # Implementation
```

**Context Usage**:
- Store verbose flag, logger, output formatter in context
- Pass context through command hierarchy
- Access via `ctx.obj['key']`

### Testing Patterns

**Unit Tests**:
```python
class TestFeature:
    """Tests for Feature class."""

    def test_specific_behavior(self) -> None:
        """Test that specific behavior works correctly."""
        # Arrange
        feature = Feature()

        # Act
        result = feature.method()

        # Assert
        assert result == expected
```

**CLI Tests**:
```python
def test_command(self) -> None:
    """Test command execution."""
    runner = CliRunner()
    result = runner.invoke(cli, ['command', '--flag'])

    assert result.exit_code == 0
    assert 'expected' in result.output
```

**Mocking**:
- Mock external dependencies (file I/O, APIs, subprocesses)
- Use pytest-mock for fixtures
- Don't mock code under test

### Configuration Management

**Settings Hierarchy** (highest to lowest priority):
1. Command-line arguments
2. Environment variables (MK8_* prefix)
3. Config file (`~/.config/mk8`)
4. Defaults

**Sensitive Data**:
- Never log credentials
- Store in config file with 0600 permissions
- Mask in error messages (show only first/last chars)

### Versioning

**Semantic Versioning** (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Version Location**: `mk8/core/version.py`

## Best Practices

### Do's
✅ Write tests first (TDD)
✅ Use type hints everywhere
✅ Provide clear error messages with suggestions
✅ Mock external dependencies in tests
✅ Follow Black formatting
✅ Keep functions small and focused
✅ Use descriptive variable names
✅ Document public APIs

### Don'ts
❌ Skip tests for "simple" code
❌ Commit code without running tests
❌ Ignore mypy type errors
❌ Use broad exception catches
❌ Hardcode configuration values
❌ Leave commented-out code
❌ Use print() (use logger or output formatter)

## Performance Considerations

- CLI startup time: <500ms target
- Lazy imports for heavy modules
- Cache version info and other static data
- Show progress for operations >2 seconds
- Implement timeouts for network operations

## Security Practices

- Validate all user inputs
- Never pass unsanitized input to shell
- Set restrictive file permissions (0600 for credentials)
- Clear sensitive data from memory when possible
- Use subprocess with shell=False
- Validate external tool outputs

## Dependency Management

**Adding Dependencies**:
1. Add to `setup.py` and `pyproject.toml`
2. Update `requirements.txt`
3. Document why dependency is needed
4. Check license compatibility (Apache 2.0)
5. Pin major versions, allow minor updates

**Updating Dependencies**:
- Test thoroughly after updates
- Check for breaking changes
- Update type stubs if needed
