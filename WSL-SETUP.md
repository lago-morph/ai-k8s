# WSL Testing Environment Setup Guide

> **Quick Start**: Jump to [5-Minute Setup](#5-minute-setup) if you just want to get started.

## Overview

This project uses a **generalized, reusable pattern** for isolated bash testing on Windows using WSL, designed for AI-assisted development.

### What We Built

1. **`.test-config.json`** - Configuration (WSL instance name, test paths)
2. **`scripts/run-tests.ps1`** - Windows test runner (PowerShell)
3. **`scripts/test-runner.sh`** - Linux/macOS test runner (Bash)
4. **`.claude/steering/wsl-testing.md`** - AI agent guidelines
5. **`.claude/steering/platform-commands.md`** - Command reference

### Key Features

✅ **Credential Isolation** - Separate WSL instance from user's default  
✅ **Platform Detection** - Automatic Windows/Linux/macOS detection  
✅ **Configuration-Driven** - No hardcoded paths or instance names  
✅ **AI Agent Safe** - Clear rules prevent credential leakage  
✅ **Reusable** - Copy to other projects (see [REUSABLE-WSL-TESTING-PATTERN.md](REUSABLE-WSL-TESTING-PATTERN.md))

## Why a Separate WSL Instance?

- **Credential Isolation**: Keeps your personal AWS credentials and kubeconfigs separate
- **Clean Environment**: No interference from existing tools or configurations
- **AI Agent Safety**: AI agents can safely run tests without accessing your personal data
- **Reproducibility**: Consistent testing environment for all contributors

---

## 5-Minute Setup

### Step 1: Create the WSL Instance

```powershell
# In PowerShell (as Administrator if possible)
wsl --install -d Ubuntu-24.04 --name mk8-test
```

If `--name` isn't supported, try:

```powershell
# Install Ubuntu
wsl --install -d Ubuntu-24.04

# Then manually rename or use it as-is and specify with -d flag
```

### Step 2: Initial WSL Setup

When the WSL instance starts for the first time:

1. Create a username (e.g., `mk8test`)
2. Create a password
3. Wait for installation to complete

### Step 3: Run the Setup Script

```powershell
# From PowerShell, in the project root
wsl -d mk8-test --cd /mnt/c/Users/YourUsername/Documents/src/ai-k8s bash prototype/setup-wsl-test-env.sh
```

This will install:
- BATS (testing framework)
- shellcheck (bash linting)
- Docker (for kind)
- kind (Kubernetes in Docker)
- kubectl (Kubernetes CLI)
- helm (package manager)
- AWS CLI (for verification)

### Step 4: Verify Installation

```powershell
# Check WSL instances
wsl --list --verbose

# Should show mk8-test in the list

# Test BATS
wsl -d mk8-test bats --version

# Test the setup
.\prototype\run-tests-wsl.ps1
```

## Running Tests

### Option 1: PowerShell Helper Script (Recommended)

```powershell
# Run all tests
.\prototype\run-tests-wsl.ps1

# Run specific test file
.\prototype\run-tests-wsl.ps1 test_crossplane.bats
```

### Option 2: Direct WSL Commands

```powershell
# Run all unit tests
wsl -d mk8-test --cd /mnt/c/Users/YourUsername/Documents/src/ai-k8s bats prototype/tests/unit/

# Run specific test
wsl -d mk8-test --cd /mnt/c/Users/YourUsername/Documents/src/ai-k8s bats prototype/tests/unit/test_crossplane.bats

# Run shellcheck
wsl -d mk8-test --cd /mnt/c/Users/YourUsername/Documents/src/ai-k8s shellcheck prototype/lib/*.sh
```

### Option 3: Interactive Session

```powershell
# Start interactive session
wsl -d mk8-test

# Inside WSL
cd /mnt/c/Users/YourUsername/Documents/src/ai-k8s
bats prototype/tests/unit/
```

## Setting Up Test Credentials

The prototype uses `MK8_*` prefixed environment variables to avoid credential leakage:

```bash
# Inside mk8-test WSL instance
wsl -d mk8-test

# Create config directory
mkdir -p ~/.config

# Copy template (has dummy credentials)
cp /mnt/c/Users/YourUsername/Documents/src/ai-k8s/prototype/.config/env-mk8-aws-template ~/.config/env-mk8-aws

# Edit with test credentials (NOT your real credentials!)
nano ~/.config/env-mk8-aws
```

Example test credentials (safe to use):

```bash
export MK8_AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export MK8_AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export MK8_AWS_REGION="us-east-1"
```

## Troubleshooting

### WSL Instance Not Found

```powershell
# List all instances
wsl --list --verbose

# If mk8-test doesn't exist, create it
wsl --install -d Ubuntu-24.04 --name mk8-test
```

### Docker Not Running

```bash
# Inside mk8-test
sudo service docker start

# Check status
sudo service docker status
```

### Permission Denied for Docker

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in
exit
wsl -d mk8-test
```

### BATS Not Found

```bash
# Install BATS manually
sudo apt-get update
sudo apt-get install -y bats

# Or run the setup script again
bash /mnt/c/Users/YourUsername/Documents/src/ai-k8s/prototype/setup-wsl-test-env.sh
```

### Path Issues

Make sure to use the correct Windows username in paths:

```powershell
# Find your username
echo $env:USERNAME

# Use it in WSL paths
wsl -d mk8-test --cd /mnt/c/Users/$env:USERNAME/Documents/src/ai-k8s
```

## Maintenance

### Update Packages

```bash
wsl -d mk8-test

sudo apt-get update
sudo apt-get upgrade -y
```

### Reset Instance (if needed)

```powershell
# Backup first (optional)
wsl --export mk8-test mk8-test-backup.tar

# Delete instance
wsl --unregister mk8-test

# Recreate
wsl --install -d Ubuntu-24.04 --name mk8-test

# Re-run setup
wsl -d mk8-test --cd /mnt/c/Users/$env:USERNAME/Documents/src/ai-k8s bash prototype/setup-wsl-test-env.sh
```

## For AI Agents

AI agents working on this project should:

1. **Always use `wsl -d mk8-test`** for bash operations
2. **Never use default WSL** (just `wsl` without `-d`)
3. **Check `.claude/steering/wsl-testing.md`** for detailed guidelines
4. **Use the PowerShell helper script** when possible: `.\prototype\run-tests-wsl.ps1`

## Security Notes

- ✅ This WSL instance is isolated from your personal credentials
- ✅ Only test/dummy credentials should be configured
- ✅ AI agents can safely run tests without credential leakage
- ✅ Your default WSL instance remains untouched
- ⚠️ Never put real AWS credentials in this instance

## Next Steps

After setup:

1. ✅ Run tests: `.\prototype\run-tests-wsl.ps1`
2. ✅ Verify all tests pass
3. ✅ Continue development with confidence

For more details, see `.claude/steering/wsl-testing.md`
