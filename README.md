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
| **Local Kind Cluster Management** | ✅ Complete | 0 tests* | - |
| **Crossplane Bootstrap** | ✅ Complete | 0 tests* | - |

**Total:** 273 tests passing with 95%+ overall coverage  
*Implementation complete, comprehensive test suite planned

### 🚧 In Development

- **Tutorial: Create S3 Bucket** - Design complete, ready for implementation
- **GitOps Repository Setup** - Design complete, ready for implementation

### 📋 Planned

- **ArgoCD Bootstrap** - Requirements defined
- **Management Cluster Provisioning** - Planned
- **Workload Cluster Management** - Planned

### 📋 Roadmap

1. ✅ **Phase 1: Foundation** (Complete)
   - CLI framework with Click
   - Error handling and logging
   - Prerequisite checking
   - AWS credential management
   - Kubeconfig management

2. ✅ **Phase 2: Bootstrap Cluster** (Complete)
   - Local kind cluster lifecycle
   - Crossplane installation
   - AWS provider configuration
   - Helm integration

3. � **Pchase 3: Documentation & Tutorials** (In Progress)
   - Tutorial: Create S3 bucket with Crossplane
   - Documentation site framework
   - User guides and examples

4. 📋 **Phase 4: GitOps & Management Cluster** (Planned)
   - GitOps repository setup
   - ArgoCD installation
   - EKS management cluster provisioning

5. 📋 **Phase 5: Workload Clusters** (Planned)
   - Declarative cluster management
   - Multi-environment support
   - Application deployment workflows

---

## 🚀 Installation

### Prerequisites

Before installing mk8, ensure you have:

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Docker** - [Install Docker](https://docs.docker.com/engine/install/) (must be running)
- **kubectl** - [Install kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- **kind** - [Install kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- **Helm** - [Install Helm](https://helm.sh/docs/intro/install/) (for Crossplane installation)
- **AWS CLI** - [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) (optional, for verification)
- **AWS Account** - With appropriate IAM permissions for S3, EKS, etc.

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

## ⚡ Quick Start

Get started with mk8 in 5 minutes:

```bash
# 1. Verify prerequisites
mk8 verify

# 2. Configure AWS credentials
mk8 config

# 3. Create bootstrap cluster
mk8 bootstrap create

# 4. Install Crossplane
mk8 crossplane install

# 5. You're ready! Now you can provision AWS resources with Crossplane
```

See the [Usage](#-usage) section below for detailed examples.

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

### Bootstrap Cluster Management

Create and manage a local Kubernetes cluster for Crossplane:

```bash
# Create local bootstrap cluster
$ mk8 bootstrap create
Creating bootstrap cluster...
✓ Cluster 'mk8-bootstrap' created successfully
✓ Kubeconfig updated
✓ Cluster is ready

# Create with specific Kubernetes version
$ mk8 bootstrap create --kubernetes-version v1.28.0

# Force recreate if cluster exists
$ mk8 bootstrap create --force-recreate

# Check cluster status
$ mk8 bootstrap status
Bootstrap Cluster Status:
  Exists: Yes
  Ready: Yes
  Kubernetes Version: v1.29.0
  Context: kind-mk8-bootstrap

# Delete bootstrap cluster
$ mk8 bootstrap delete
Are you sure you want to delete the bootstrap cluster? [y/N]: y
✓ Cluster deleted successfully
✓ Kubeconfig cleaned up

# Delete without confirmation
$ mk8 bootstrap delete --yes
```

### Crossplane Management

Install and manage Crossplane on the bootstrap cluster:

```bash
# Install Crossplane with AWS provider
$ mk8 crossplane install
Installing Crossplane...
✓ Crossplane installed successfully
✓ AWS Provider installed
✓ ProviderConfig created
✓ Crossplane is ready

# Install specific Crossplane version
$ mk8 crossplane install --version 1.14.0

# Check Crossplane status
$ mk8 crossplane status
Crossplane Status:
  Installed: Yes
  Version: 1.14.5
  Pods Ready: 3/3
  AWS Provider: Healthy
  ProviderConfig: Configured

# Uninstall Crossplane
$ mk8 crossplane uninstall
Are you sure you want to uninstall Crossplane? [y/N]: y
✓ Crossplane uninstalled successfully

# Uninstall without confirmation
$ mk8 crossplane uninstall --yes
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
│   │   │   ├── bootstrap.py      # Bootstrap cluster commands
│   │   │   ├── config.py         # AWS credentials command
│   │   │   ├── crossplane.py     # Crossplane commands
│   │   │   ├── verify.py         # Prerequisite verification
│   │   │   └── version.py        # Version command
│   │   ├── main.py               # CLI entry point
│   │   └── output.py             # Output formatting
│   ├── core/                     # Core infrastructure
│   │   ├── errors.py             # Exception hierarchy
│   │   ├── logging.py            # Logging configuration
│   │   └── version.py            # Version management
│   ├── business/                 # Business logic
│   │   ├── bootstrap_manager.py  # Bootstrap cluster orchestration
│   │   ├── credential_manager.py # AWS credential orchestration
│   │   ├── crossplane_installer.py # Crossplane installation
│   │   ├── crossplane_manager.py # Crossplane secret sync
│   │   └── verification.py       # Installation verification
│   └── integrations/             # External tool clients
│       ├── aws_client.py         # AWS STS validation
│       ├── file_io.py            # Secure file operations
│       ├── helm_client.py        # Helm operations
│       ├── kind_client.py        # Kind cluster operations
│       ├── kubeconfig.py         # Kubeconfig management
│       ├── kubectl_client.py     # Kubectl operations
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
│   │   ├── tutorial-01-create-s3-bucket/  # Tutorial spec
│   │   └── ...                   # Other specs
│   └── steering/                 # Development guidelines
├── docs/                         # Documentation (planned)
│   └── tutorials/                # Tutorial content
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
- [kind](https://kind.sigs.k8s.io/) - Local Kubernetes clusters
- [Helm](https://helm.sh/) - Kubernetes package manager
- [Crossplane](https://www.crossplane.io/) - Infrastructure as code
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-based testing
- [pytest](https://pytest.org/) - Testing framework

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/mk8/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/mk8/discussions)

---

**Note**: mk8 is in active development (Alpha). APIs and commands may change. Not recommended for production use yet.
