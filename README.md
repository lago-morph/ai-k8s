# mk8 - Manage Kubernetes Infrastructure on AWS

mk8 is a command-line tool for managing Kubernetes infrastructure on AWS using a multi-tier cluster architecture with Crossplane.

## Architecture

1. **Bootstrap Cluster** (local kind cluster) - Temporary cluster on your local machine that installs Crossplane with AWS credentials
2. **Management Cluster** (AWS) - Provisioned by the bootstrap cluster via Crossplane, manages workload clusters
3. **Workload Clusters** (AWS) - Application clusters created and managed by the management cluster

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/your-org/mk8.git
cd mk8

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Requirements

- Python 3.8 or higher
- Docker (for local bootstrap cluster)
- kubectl
- kind

## Quick Start

```bash
# Configure AWS credentials
mk8 config

# Create local bootstrap cluster
mk8 bootstrap create

# Check bootstrap cluster status
mk8 bootstrap status

# Delete bootstrap cluster when done
mk8 bootstrap delete
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=mk8 --cov-report=html

# Format code
black mk8/ tests/

# Lint code
flake8 mk8/ tests/

# Type check
mypy mk8/
```

### Project Structure

```
mk8/
├── mk8/                    # Main package
│   ├── cli/               # CLI interface
│   │   ├── commands/      # Command implementations
│   │   ├── main.py        # CLI entry point
│   │   ├── output.py      # Output formatting
│   │   └── parser.py      # Command parsing
│   ├── core/              # Core functionality
│   │   ├── errors.py      # Exception definitions
│   │   ├── logging.py     # Logging configuration
│   │   └── version.py     # Version information
│   ├── business/          # Business logic
│   └── integrations/      # External tool clients
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── setup.py              # Package setup
├── pyproject.toml        # Modern Python packaging
└── requirements.txt      # Dependencies
```

## Contributing

Contributions are welcome! Please ensure:

- All tests pass: `pytest`
- Code is formatted: `black mk8/ tests/`
- Code passes linting: `flake8 mk8/ tests/`
- Type checking passes: `mypy mk8/`
- Coverage is maintained: `pytest --cov=mk8`

## License

Apache License 2.0
