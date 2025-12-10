# Reusable WSL Testing Pattern for AI-Assisted Projects

This document describes a reusable pattern for isolating bash testing on Windows using WSL, designed for projects that use AI agents for development and testing.

## Problem Statement

When working with AI agents on Windows:
- Running `bash` directly uses the user's default WSL instance
- This exposes personal credentials (AWS, kubeconfigs, etc.)
- AI agents may inadvertently access or modify personal data
- Testing should be isolated from the user's development environment

## Solution: Isolated WSL Testing Pattern

Create a dedicated WSL instance for testing with:
- Configuration-driven setup
- Platform-agnostic test runners
- Automatic platform detection
- No hardcoded paths or user-specific settings

## Files to Copy to New Projects

### 1. Configuration File: `.test-config.json`

```json
{
  "wsl": {
    "instanceName": "project-test",
    "distribution": "Ubuntu-24.04",
    "setupScript": "scripts/setup-wsl-env.sh"
  },
  "testing": {
    "framework": "bats",
    "testDirectory": "tests",
    "shellcheckPaths": ["scripts/*.sh", "lib/*.sh"]
  }
}
```

**Customize:**
- `instanceName`: Change to `<your-project>-test`
- `setupScript`: Path to your WSL setup script
- `testDirectory`: Where your tests live
- `shellcheckPaths`: Paths to check with shellcheck

### 2. Universal Test Runner (Bash): `scripts/test-runner.sh`

Copy the entire `scripts/test-runner.sh` file from this project.

**Features:**
- Detects platform (Linux/macOS/WSL/Windows)
- Loads configuration from `.test-config.json`
- Runs tests natively on Linux/macOS
- Warns if in wrong WSL instance
- Supports test framework and shellcheck

**No modifications needed** - it reads from `.test-config.json`

### 3. Universal Test Runner (PowerShell): `scripts/run-tests.ps1`

Copy the entire `scripts/run-tests.ps1` file from this project.

**Features:**
- Detects and validates WSL instance
- Loads configuration from `.test-config.json`
- Provides setup command for WSL instance
- Converts Windows paths to WSL paths automatically
- Delegates to bash test runner inside WSL

**No modifications needed** - it reads from `.test-config.json`

### 4. WSL Setup Script: `scripts/setup-wsl-env.sh`

Create a setup script for your project's specific needs:

```bash
#!/usr/bin/env bash
# Setup script for <project>-test WSL instance

set -euo pipefail

echo "Setting up <project> testing environment..."

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install your testing tools
sudo apt-get install -y bats shellcheck

# Install project-specific tools
# sudo apt-get install -y docker.io kubectl helm
# ... add your tools here ...

echo "Setup complete!"
```

### 5. Steering File: `.claude/steering/wsl-testing.md`

Copy the steering file from this project and customize:

```markdown
---
inclusion: always
---

# WSL Testing Environment

## CRITICAL: Never Run Bash Directly on Windows

**⚠️ ABSOLUTE RULE: On Windows, NEVER execute bash commands directly.**

### Forbidden Commands on Windows
[Copy from this project's steering file]

### Required Commands on Windows
[Copy from this project's steering file]

## Configuration

- **WSL Instance**: `<your-project>-test` (from `.test-config.json`)
- **Purpose**: Isolated testing environment
- **Credential Isolation**: No access to user's personal credentials

## AI Agent Guidelines
[Copy the decision tree and command patterns from this project]
```

### 6. Setup Documentation: `WSL-SETUP.md`

Create a setup guide for your project:

```markdown
# WSL Testing Environment Setup

## Quick Setup

1. Create WSL instance:
   ```powershell
   wsl --install -d Ubuntu-24.04 --name <project>-test
   ```

2. Run setup:
   ```powershell
   .\scripts\run-tests.ps1 -Setup
   ```

3. Run tests:
   ```powershell
   .\scripts\run-tests.ps1
   ```

[Add project-specific setup steps]
```

## Integration Steps

### Step 1: Copy Files

```bash
# In your new project
mkdir -p scripts .claude/steering

# Copy these files from mk8 project:
cp /path/to/mk8/.test-config.json .
cp /path/to/mk8/scripts/test-runner.sh scripts/
cp /path/to/mk8/scripts/run-tests.ps1 scripts/
cp /path/to/mk8/.claude/steering/wsl-testing.md .claude/steering/
```

### Step 2: Customize Configuration

Edit `.test-config.json`:

```json
{
  "wsl": {
    "instanceName": "myproject-test",  // ← Change this
    "distribution": "Ubuntu-24.04",
    "setupScript": "scripts/setup-wsl-env.sh"  // ← Verify path
  },
  "testing": {
    "framework": "bats",  // or "pytest", "jest", etc.
    "testDirectory": "tests",  // ← Your test directory
    "shellcheckPaths": ["scripts/*.sh"]  // ← Your bash scripts
  }
}
```

### Step 3: Create Setup Script

Create `scripts/setup-wsl-env.sh` with your project's dependencies:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Setting up myproject testing environment..."

sudo apt-get update
sudo apt-get upgrade -y

# Install testing framework
sudo apt-get install -y bats shellcheck

# Install project-specific tools
# ... add your dependencies ...

echo "Setup complete!"
```

### Step 4: Update Steering File

Edit `.claude/steering/wsl-testing.md`:
- Replace `mk8-test` with your instance name
- Update project-specific paths
- Add project-specific tools to the installed tools list

### Step 5: Test the Setup

```powershell
# Windows
.\scripts\run-tests.ps1 -Setup
.\scripts\run-tests.ps1
```

```bash
# Linux/macOS
./scripts/test-runner.sh
```

## Pattern Benefits

### For Users
- ✅ Personal credentials never exposed to AI agents
- ✅ Isolated testing environment
- ✅ Default WSL instance remains untouched
- ✅ Easy to set up and tear down

### For AI Agents
- ✅ Clear rules about bash execution on Windows
- ✅ Configuration-driven (no hardcoded paths)
- ✅ Platform detection built-in
- ✅ Consistent interface across projects

### For Projects
- ✅ Portable across different machines
- ✅ No user-specific configuration
- ✅ Easy to document and maintain
- ✅ Works on Linux, macOS, and Windows

## Advanced Customization

### Multiple Test Frameworks

If your project uses multiple testing frameworks:

```json
{
  "testing": {
    "bash": {
      "framework": "bats",
      "testDirectory": "tests/bash"
    },
    "python": {
      "framework": "pytest",
      "testDirectory": "tests/python"
    }
  }
}
```

Update test runners to handle multiple frameworks.

### Custom WSL Distributions

For projects requiring specific Linux distributions:

```json
{
  "wsl": {
    "instanceName": "myproject-test",
    "distribution": "Debian",  // or "Alpine", "Fedora", etc.
    "setupScript": "scripts/setup-wsl-env.sh"
  }
}
```

### Project-Specific Credentials

For projects needing test credentials:

```bash
# In setup-wsl-env.sh
mkdir -p ~/.config
cat > ~/.config/myproject-test-creds <<EOF
export TEST_API_KEY="dummy-key-for-testing"
export TEST_DATABASE_URL="postgresql://test:test@localhost/test"
EOF
```

## Troubleshooting

### WSL Instance Not Found

```powershell
# Check existing instances
wsl --list --verbose

# Create if missing
.\scripts\run-tests.ps1 -Setup
```

### Tests Fail on Windows but Pass on Linux

- Check that you're using `.\scripts\run-tests.ps1` on Windows
- Verify WSL instance is set up: `wsl -d <project>-test bash --version`
- Check test framework is installed: `wsl -d <project>-test bats --version`

### Path Issues

The test runners automatically convert Windows paths to WSL paths. If you have issues:
- Ensure you're running from project root
- Check `.test-config.json` paths are relative to project root
- Verify `$WSL_PROJECT_ROOT` conversion in `run-tests.ps1`

## Security Considerations

### What to Put in WSL Test Instance
- ✅ Test/dummy credentials
- ✅ Sample data
- ✅ Development tools

### What NOT to Put in WSL Test Instance
- ❌ Real AWS credentials
- ❌ Production API keys
- ❌ Personal SSH keys
- ❌ Real database credentials

### Credential Isolation Pattern

Use environment variable prefixes for test credentials:

```bash
# Real credentials (user's default WSL)
AWS_ACCESS_KEY_ID="real-key"
AWS_SECRET_ACCESS_KEY="real-secret"

# Test credentials (project-test WSL)
TEST_AWS_ACCESS_KEY_ID="dummy-key"
TEST_AWS_SECRET_ACCESS_KEY="dummy-secret"

# Or project-specific prefix
MYPROJECT_AWS_ACCESS_KEY_ID="test-key"
MYPROJECT_AWS_SECRET_ACCESS_KEY="test-secret"
```

## Maintenance

### Updating the WSL Instance

```powershell
# Update packages
wsl -d <project>-test bash -c "sudo apt-get update && sudo apt-get upgrade -y"

# Reinstall tools
wsl -d <project>-test --cd /mnt/c/path/to/project bash scripts/setup-wsl-env.sh
```

### Resetting the Instance

```powershell
# Backup (optional)
wsl --export <project>-test <project>-test-backup.tar

# Delete
wsl --unregister <project>-test

# Recreate
.\scripts\run-tests.ps1 -Setup
```

## Example Projects Using This Pattern

- **mk8**: Kubernetes infrastructure management (original implementation)
- Add your projects here as you adopt this pattern

## License

This pattern is provided as-is for use in any project. No attribution required.

## Contributing

If you improve this pattern, consider:
1. Documenting your improvements
2. Sharing back with the community
3. Creating a standalone template repository

## Version History

- **v1.0** (2024-12): Initial pattern from mk8 project
  - Configuration-driven setup
  - Universal test runners
  - Platform detection
  - AI agent steering

---

**Questions or improvements?** Open an issue in the mk8 project or your own project using this pattern.
