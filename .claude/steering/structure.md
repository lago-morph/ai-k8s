# Project Structure and Architecture

## Repository Organization

```
ai-k8s/
├── .claude/                    # Claude Code configuration
│   ├── specs/                  # Feature specifications
│   │   ├── aws-credentials-management/
│   │   ├── kubeconfig-file-handling/
│   │   ├── local-bootstrap-cluster/
│   │   └── mk8-cli/
│   ├── steering/               # Steering documents (this file)
│   ├── commands/               # Custom slash commands
│   └── settings.json           # Permissions and settings
├── mk8/                        # Main package
│   ├── cli/                    # CLI interface
│   ├── core/                   # Core functionality
│   ├── business/               # Business logic
│   └── integrations/           # External tool clients
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── .venv/                      # Virtual environment
├── setup.py                    # Package setup
├── pyproject.toml              # Modern Python config
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Development dependencies
└── README.md                   # Documentation
```

## Module Architecture

### mk8.cli - CLI Interface Layer

**Purpose**: Handle command-line parsing, routing, and user interaction

**Components**:
- `main.py`: Entry point, Click group setup, global options, routing
- `output.py`: OutputFormatter class for consistent terminal output
- `commands/`: Individual command implementations
  - `version.py`: Version command handler
  - `bootstrap.py`: Bootstrap commands (future)
  - `config.py`: Config command (future)

**Responsibilities**:
- Parse command-line arguments with Click
- Route commands to appropriate handlers
- Manage command context (verbose, logger, output)
- Handle global options (--verbose, --version, --help)
- Format and display output to user

**Key Classes**:
- `CommandContext`: Shared context (verbose, logger, output)
- `OutputFormatter`: Consistent output formatting

### mk8.core - Core Infrastructure

**Purpose**: Fundamental utilities used throughout the application

**Components**:
- `errors.py`: Exception hierarchy and exit codes
- `logging.py`: Logger configuration and formatters
- `version.py`: Semantic versioning

**Responsibilities**:
- Define application-wide error types
- Provide logging infrastructure
- Manage version information
- Define exit codes

**Key Classes**:
- `MK8Error`: Base exception with suggestion support
- `PrerequisiteError`, `ValidationError`, `CommandError`, `ConfigurationError`
- `ExitCode`: Enum of standard exit codes
- `Version`: Semantic version management
- `VerboseFormatter`: Timestamp-enabled log formatter

### mk8.business - Business Logic (Future)

**Purpose**: Core business logic independent of CLI or external tools

**Planned Components**:
- `cluster_manager.py`: Bootstrap cluster lifecycle
- `credential_manager.py`: AWS credential management
- `kubeconfig_manager.py`: kubectl config file handling

**Responsibilities**:
- Implement core feature logic
- Orchestrate integration layer
- Enforce business rules
- Manage application state

### mk8.integrations - External Tool Clients (Future)

**Purpose**: Interface with external tools and services

**Planned Components**:
- `kind.py`: kind cluster operations
- `kubectl.py`: kubectl interactions
- `crossplane.py`: Crossplane installation/management
- `aws.py`: AWS API client wrapper

**Responsibilities**:
- Wrap external CLI tools (kind, kubectl)
- Handle AWS API calls
- Manage Crossplane operations
- Provide error translation

## Data Flow

### Command Execution Flow
```
User Input
    ↓
CLI Parser (Click)
    ↓
Command Router
    ↓
Command Handler
    ↓
Business Logic
    ↓
Integration Layer
    ↓
External Tools/APIs
```

### Error Flow
```
Exception Raised
    ↓
Exception Type Check
    ↓
├─ MK8Error → Format with suggestions → stderr
├─ ClickException → Let Click handle
└─ Other → Log + Bug report message
    ↓
Exit with appropriate code
```

### Configuration Flow
```
Command Execution
    ↓
Check ~/.config/mk8
    ↓
├─ Found → Use config
├─ Not found → Check MK8_* env vars
│   ↓
│   ├─ Found → Auto-configure
│   └─ Not found → Check AWS_* env vars
│       ↓
│       ├─ Found → Prompt user (3 options)
│       └─ Not found → Prompt for manual entry
```

## Testing Architecture

### Test Organization
```
tests/
├── unit/                      # Fast, isolated tests
│   ├── cli/                   # CLI layer tests
│   │   ├── test_main.py       # Main entry point
│   │   ├── test_output.py     # Output formatter
│   │   └── test_commands.py   # Command handlers
│   └── core/                  # Core layer tests
│       ├── test_errors.py     # Error handling
│       ├── test_logging.py    # Logging
│       └── test_version.py    # Versioning
└── integration/               # End-to-end tests
    └── test_command_flow.py   # Full command execution
```

### Test Strategy
- **Unit Tests**: Test each module in isolation with mocks
- **Integration Tests**: Test interaction between modules
- **CLI Tests**: Use Click's CliRunner for isolated testing
- **Coverage**: Enforce 80% minimum, aim for >90%

## Configuration Files

### pyproject.toml
- Build system configuration
- Tool configurations (black, pytest, mypy, coverage)
- Project metadata and dependencies

### setup.py
- Package setup for pip install
- Entry point definition (`mk8` command)
- Dependencies and classifiers

### .flake8
- Linting rules
- Line length (88, matching Black)
- Exclusions and per-file ignores

## Development Workflow

### File Creation Pattern
1. Create test file first: `tests/unit/module/test_feature.py`
2. Write failing test
3. Create implementation: `mk8/module/feature.py`
4. Make test pass
5. Refactor if needed
6. Run full test suite

### Adding a New Command
1. Define spec in `.claude/specs/<feature>/`
2. Write tests in `tests/unit/cli/test_<command>.py`
3. Implement in `mk8/cli/commands/<command>.py`
4. Register in `mk8/cli/main.py`
5. Add business logic in `mk8/business/`
6. Add integrations in `mk8/integrations/`
7. Update documentation

### Adding a New Feature
1. Create spec directory: `.claude/specs/<feature>/`
2. Write requirements.md (EARS format)
3. Write design.md (architecture, components)
4. Write tasks.md (implementation plan)
5. Implement following TDD
6. Achieve >80% coverage
7. Update README.md

## Architectural Patterns

### Dependency Injection
- Pass dependencies (logger, output, clients) through context
- Avoid global state
- Enable easy mocking in tests

### Error Handling
- Custom exception hierarchy
- Always provide suggestions with errors
- Consistent error formatting

### Separation of Concerns
- CLI: User interaction only
- Business: Core logic, no I/O
- Integrations: External tool/API wrappers

### Command Pattern
- Each CLI command has dedicated handler
- Handlers orchestrate business logic
- Context passed through layers

## Future Architecture

### Planned Additions
- **State Management**: Track cluster states, operations in progress
- **Configuration Schema**: Validate config file format
- **Plugin System**: Allow third-party extensions
- **Async Operations**: Support long-running operations
- **Progress Tracking**: Rich progress bars for operations
- **Rollback Support**: Undo failed operations

### Scalability Considerations
- Keep CLI fast (<500ms startup)
- Support multiple concurrent clusters
- Handle large kubeconfig files efficiently
- Cache external tool availability checks
