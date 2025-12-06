# mk8 - Manage Kubernetes Infrastructure on AWS

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Code Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](htmlcov/index.html)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()

**A command-line tool for managing Kubernetes infrastructure on AWS using a multi-tier cluster architecture with Crossplane and GitOps.**

**Version:** 0.1.0 (Alpha - Active Development)

---

## 🎯 Project Vision

mk8 automates the creation and management of production-ready Kubernetes infrastructure on AWS using modern cloud-native patterns. It implements a multi-tier architecture where infrastructure is managed as code through Crossplane, and applications are deployed via GitOps with ArgoCD.

### Why mk8?

**The Problem:** Setting up production Kubernetes on AWS is complex, requiring expertise in:
- AWS infrastructure (VPCs, IAM, EKS)
- Kubernetes cluster management
- Crossplane for infrastructure as code
- GitOps workflows with ArgoCD
- Security best practices

**The Solution:** mk8 automates this entire process with a single CLI tool that:
- ✅ Validates prerequisites and AWS credentials
- ✅ Creates a local bootstrap cluster with Crossplane
- ✅ Provisions an AWS management cluster via Crossplane
- ✅ Sets up GitOps workflows with ArgoCD
- ✅ Manages workload clusters declaratively
- ✅ Provides safe, atomic operations with comprehensive error handling

---

## 🏗️ Architecture

mk8 implements a three-tier cluster architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  1. Bootstrap Cluster (Local - kind)                        │
│     • Temporary cluster on your machine                     │
│     • Installs Crossplane with AWS provider                 │
│     • Provisions management cluster                         │
│     • Deleted after management cluster is ready             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Management Cluster (AWS - EKS)                          │
│     • Provisioned by bootstrap cluster via Crossplane       │
│     • Runs Crossplane for infrastructure management         │
│     • Runs ArgoCD for GitOps workflows                      │
│     • Manages workload clusters declaratively               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Workload Clusters (AWS - EKS)                           │
│     • Application clusters for different environments       │
│     • Created and managed by management cluster             │
│     • Deployed via GitOps (ArgoCD)                          │
│     • Examples: dev, staging, production                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Current Status

mk8 is in **active development** with core functionality complete and tested.

### ✅ Completed Features

| Feature | Status | Tests | Coverage |
|---------|--------|-------|----------|
| **CLI Framework** | ✅ Complete | 50 tests | 100% |
| **Prerequisite Verification** | ✅ Complete | 53 tests | 97% |
| **AWS Credentials Management** | ✅ Complete | 121 tests | 100% |
| **Kubeconfig File Handling** | ✅ Complete | 49 tests | 100% |

**Total:** 273 tests passing with 95%+ overall coverage

### 🚧 In Development

- **Local Kind Cluster Management** - Design complete, implementation starting
- **Crossplane Bootstrap** - Requirements defined
- **GitOps Repository Setup** - Requirements defined
- **ArgoCD Bootstrap** - Requirements defined

### 📋 Roadmap

1. ✅ **Phase 1: Foundation** (Complete)
   - CLI framework with Click
   - Error handling and logging
   - Prerequisite checking
   - AWS credential management
   - Kubeconfig management

2. 🚧 **Phase 2: Bootstrap Cluster** (In Progress)
   - Local kind cluster lifecycle
   - Crossplane installation
   - AWS provider configuration

3. 📋 **Phase 3: Management Cluster** (Planned)
   - EKS cluster provisioning via Crossplane
   - ArgoCD installation
   - GitOps repository setup

4. 📋 **Phase 4: Workload Clusters** (Planned)
   - Declarative cluster management
   - Multi-environment support
   - Application deployment workflows

---

## 🚀 Installation

### Prerequisites

Before installing mk8, ensure you have:

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Docker** - [Install Docker](https://docs.docker.com/engine/install/)
- **kubectl** - [Install kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- **kind** - [Install kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- **AWS Account** - With appropriate permissions for EKS

### From Source

```bash
# Clone the repository
git clone https://github.com/your-org/mk8.git
cd mk8

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check version
mk8 --version

# Verify prerequisites
mk8 verify

# Verify with detailed output
mk8 verify --verbose
```

---

## 📖 Usage

### Verify Prerequisites

Check that all required tools are installed and configured:

```bash
# Basic verification
$ mk8 verify
✓ mk8 is installed
✓ All prerequisites satisfied

# Detailed verification
$ mk8 verify --verbose
✓ mk8 is installed
✓ All prerequisites satisfied

Detailed Status:
docker: ✓ None (/usr/bin/docker)
kind: ✓ None (/usr/local/bin/kind)
kubectl: ✓ None (/usr/bin/kubectl)

Verification complete!
```

### Configure AWS Credentials

Set up AWS credentials for Crossplane:

```bash
# Interactive configuration
$ mk8 config
AWS credentials not found in config file.

Choose credential source:
  1. Enter credentials manually
  2. Use environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)

Choice: 1
AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key: ********
AWS Region [us-east-1]: us-west-2

✓ Credentials validated successfully
✓ Account ID: 123456789012
✓ Credentials saved to ~/.mk8/config.yaml
✓ Crossplane secret synchronized

# Update existing credentials
$ mk8 config
✓ Credentials validated successfully
✓ Account ID: 123456789012
✓ Crossplane secret synchronized
```

### Bootstrap Cluster Management (Coming Soon)

```bash
# Create local bootstrap cluster
mk8 bootstrap create

# Check cluster status
mk8 bootstrap status

# Delete bootstrap cluster
mk8 bootstrap delete
```

---

## 🧪 Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=mk8 --cov-report=html

# Run specific test suite
pytest tests/unit/cli/
pytest tests/unit/integrations/
pytest tests/unit/business/
```

### Code Quality

mk8 maintains high code quality standards:

```bash
# Format code (required before commit)
black mk8/ tests/

# Lint code
flake8 mk8/ tests/

# Type checking
mypy mk8/

# Run all quality checks
black mk8/ tests/ && flake8 mk8/ tests/ && mypy mk8/ && pytest
```

### Project Structure

```
mk8/
├── mk8/                          # Main package
│   ├── cli/                      # CLI interface
│   │   ├── commands/             # Command implementations
│   │   │   ├── config.py         # AWS credentials command
│   │   │   ├── verify.py         # Prerequisite verification
│   │   │   └── version.py        # Version command
│   │   ├── main.py               # CLI entry point
│   │   └── output.py             # Output formatting
│   ├── core/                     # Core infrastructure
│   │   ├── errors.py             # Exception hierarchy
│   │   ├── logging.py            # Logging configuration
│   │   └── version.py            # Version management
│   ├── business/                 # Business logic
│   │   ├── credential_manager.py # AWS credential orchestration
│   │   ├── crossplane_manager.py # Crossplane secret sync
│   │   └── verification.py       # Installation verification
│   └── integrations/             # External tool clients
│       ├── aws_client.py         # AWS STS validation
│       ├── file_io.py            # Secure file operations
│       ├── kubeconfig.py         # Kubeconfig management
│       └── prerequisites.py      # Prerequisite checking
├── tests/                        # Comprehensive test suite
│   ├── unit/                     # Unit tests (273 tests)
│   │   ├── cli/                  # CLI tests
│   │   ├── core/                 # Core tests
│   │   ├── business/             # Business logic tests
│   │   └── integrations/         # Integration tests
│   └── integration/              # End-to-end tests (planned)
├── .claude/                      # AI-assisted development
│   ├── specs/                    # Feature specifications
│   └── steering/                 # Development guidelines
├── setup.py                      # Package configuration
├── pyproject.toml                # Modern Python packaging
└── requirements.txt              # Dependencies
```

### Testing Philosophy

mk8 uses a comprehensive testing approach:

- **Unit Tests**: Test individual components in isolation
- **Property-Based Tests**: Use Hypothesis to validate correctness properties across all valid inputs (100+ examples per property)
- **Integration Tests**: Test component interactions (planned)
- **Coverage Target**: 80% minimum, currently 95%+

Example property test:
```python
@given(
    docker_installed=st.booleans(),
    kind_installed=st.booleans(),
    kubectl_installed=st.booleans(),
)
@settings(max_examples=100)
def test_property_prerequisite_check_completeness(
    self, docker_installed, kind_installed, kubectl_installed
):
    """Verify all three prerequisites are always checked."""
    # Test runs 100 times with different combinations
    # Validates correctness property holds for all inputs
```

---

## 🤝 Contributing

Contributions are welcome! mk8 follows a spec-driven development process:

### Development Process

1. **Specifications First**: Features are designed in `.claude/specs/` with:
   - Requirements (EARS format)
   - Design (architecture, data models, correctness properties)
   - Tasks (implementation plan)

2. **Test-Driven Development**: Write tests before implementation
   - Unit tests for specific behaviors
   - Property tests for correctness guarantees

3. **Quality Standards**:
   - All tests must pass
   - Code coverage ≥ 80%
   - Black formatting
   - Flake8 linting
   - Mypy type checking

### Contribution Workflow

```bash
# 1. Fork and clone
git clone https://github.com/your-username/mk8.git
cd mk8

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes with tests
# - Write tests first (TDD)
# - Implement feature
# - Ensure all quality checks pass

# 4. Run quality checks
black mk8/ tests/
flake8 mk8/ tests/
mypy mk8/
pytest --cov=mk8

# 5. Commit and push
git commit -m "feat: add my feature"
git push origin feature/my-feature

# 6. Create pull request
```

### Commit Message Format

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring

---

## 📚 Documentation

- **Specifications**: `.claude/specs/` - Detailed feature specifications
- **Design Documents**: Each spec includes architecture and design decisions
- **API Documentation**: Inline docstrings with type hints
- **Development Guide**: `AGENTS.md` - Guide for AI-assisted development

---

## 🔒 Security

mk8 implements security best practices:

- ✅ Secure file permissions (0o600 for credentials, 0o700 for directories)
- ✅ Secret masking in logs and output
- ✅ AWS credential validation before use
- ✅ Atomic file operations to prevent corruption
- ✅ Automatic backups before modifications
- ✅ Input validation and sanitization

---

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

mk8 is built with:
- [Click](https://click.palletsprojects.com/) - CLI framework
- [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) - AWS SDK
- [PyYAML](https://pyyaml.org/) - YAML processing
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-based testing
- [pytest](https://pytest.org/) - Testing framework

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/mk8/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/mk8/discussions)

---

**Note**: mk8 is in active development (Alpha). APIs and commands may change. Not recommended for production use yet.
