---
inclusion: always
---

# WSL Testing Environment

## Overview

This project uses a **dedicated WSL instance** for testing to ensure credential isolation and environment consistency. This instance is separate from the user's default WSL environment.

## WSL Instance Details

- **Instance Name**: `mk8-test`
- **Distribution**: Ubuntu 24.04 LTS
- **Purpose**: Isolated testing environment for mk8 prototype and integration tests
- **Credential Isolation**: This instance does NOT have access to user's personal AWS credentials or kubeconfigs

## CRITICAL: Never Run Bash Directly on Windows

**⚠️ ABSOLUTE RULE: On Windows, NEVER execute bash commands directly.**

Running `bash` on Windows will use the user's default WSL instance, which:
- ❌ Violates credential isolation
- ❌ Accesses personal AWS credentials and kubeconfigs
- ❌ Is explicitly forbidden for this project

### Forbidden Commands on Windows

```powershell
# ❌ NEVER DO THIS - Uses default WSL instance
bash script.sh
bash -c "command"
sh script.sh

# ❌ NEVER DO THIS - Uses default WSL without instance specification
wsl bash script.sh
wsl command

# ❌ NEVER DO THIS - Direct BATS execution
bats tests/unit/test.bats
```

### Required Commands on Windows

```powershell
# ✅ ALWAYS DO THIS - Uses isolated instance
wsl -d mk8-test bash script.sh
wsl -d mk8-test --cd /path/to/project bash script.sh

# ✅ BEST PRACTICE - Use the universal test runner
.\scripts\run-tests.ps1
.\scripts\run-tests.ps1 test_crossplane.bats
.\scripts\run-tests.ps1 -Shellcheck
```

## When to Use WSL

AI agents should use the isolated WSL instance when:

1. Running BATS tests for the prototype (`prototype/tests/`)
2. Running shellcheck on bash scripts
3. Testing kind cluster operations
4. Running integration tests that require Docker/Kubernetes
5. Any bash script execution that needs a Unix environment

**Platform Detection Required:** Always detect the platform first and use appropriate commands.

## How to Use the WSL Instance

### Universal Test Runner (Recommended)

**Always use the universal test runner scripts** - they handle platform detection automatically:

```powershell
# Windows PowerShell
.\scripts\run-tests.ps1                    # Run all tests
.\scripts\run-tests.ps1 test_file.bats     # Run specific test
.\scripts\run-tests.ps1 -Shellcheck        # Run shellcheck
.\scripts\run-tests.ps1 -Setup             # Set up WSL instance
```

```bash
# Linux/macOS or inside WSL
./scripts/test-runner.sh                   # Run all tests
./scripts/test-runner.sh test_file.bats    # Run specific test
./scripts/test-runner.sh --shellcheck      # Run shellcheck
```

### Direct WSL Commands (Advanced)

Only if you need to run commands outside the test runner:

```powershell
# Run a single command in isolated instance
wsl -d mk8-test <command>

# Examples:
wsl -d mk8-test --cd /mnt/c/path/to/project bats tests/unit/test.bats
wsl -d mk8-test --cd /mnt/c/path/to/project shellcheck lib/*.sh

# Start an interactive session
wsl -d mk8-test
```

**Note:** The universal test runner automatically converts Windows paths to WSL paths.

### Accessing Windows Files

Windows drives are mounted at `/mnt/`:
- `C:\Users\...` → `/mnt/c/Users/...`
- Project root is accessible from WSL

### Important Notes

1. **Always specify `-d mk8-test`** when running WSL commands
2. **Never use default WSL instance** (`wsl` without `-d` flag) for this project
3. **Credentials**: Use MK8_* environment variables (not user's AWS credentials)
4. **Isolation**: This instance should only have test/dummy credentials

## Installed Tools

The `mk8-test` instance has these tools pre-installed:

- **BATS**: Bash testing framework
- **shellcheck**: Bash linting
- **Docker**: For kind clusters
- **kind**: Kubernetes in Docker
- **kubectl**: Kubernetes CLI
- **helm**: Kubernetes package manager
- **aws**: AWS CLI (for verification only, no real credentials)

## Setting Up Test Credentials

For integration tests, use the template credentials:

```bash
# Inside mk8-test WSL instance
wsl -d mk8-test

# Copy template to home directory
cp /mnt/c/Users/JonathonManton/Documents/src/ai-k8s/prototype/.config/env-mk8-aws-template ~/.config/env-mk8-aws

# Edit with test credentials (NOT real credentials)
nano ~/.config/env-mk8-aws
```

## Verification

To verify the WSL instance is set up correctly:

```powershell
# Check WSL instances
wsl --list --verbose

# Should show mk8-test in the list

# Test BATS installation
wsl -d mk8-test bats --version

# Test shellcheck installation
wsl -d mk8-test shellcheck --version

# Test Docker
wsl -d mk8-test docker --version
```

## Troubleshooting

### WSL Instance Not Found

```powershell
# List all instances
wsl --list --verbose

# If mk8-test doesn't exist, create it:
wsl --install -d Ubuntu-24.04 --name mk8-test
```

### Docker Not Running

```bash
# Inside mk8-test
sudo service docker start

# Or enable Docker to start automatically
sudo systemctl enable docker
```

### Permission Issues

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in for changes to take effect
exit
wsl -d mk8-test
```

## AI Agent Guidelines

### Platform Detection (REQUIRED)

**ALWAYS detect the platform before running bash commands:**

```python
import platform
import os

system = platform.system()  # 'Windows', 'Linux', 'Darwin'
shell = os.environ.get('SHELL', '')  # Check shell type

if system == 'Windows':
    # Use PowerShell test runner
    use_command = ".\\scripts\\run-tests.ps1"
else:
    # Use bash test runner
    use_command = "./scripts/test-runner.sh"
```

### Decision Tree for AI Agents

```
Is platform Windows?
├─ YES → Use .\scripts\run-tests.ps1
│        NEVER use bash, sh, or wsl without -d flag
│        NEVER assume default WSL instance
│
└─ NO → Is platform Linux/macOS?
         ├─ YES → Use ./scripts/test-runner.sh directly
         │        Tests run natively
         │
         └─ Are we inside WSL?
                  ├─ YES → Check if correct instance
                  │        Use ./scripts/test-runner.sh
                  │
                  └─ NO → Error: Unknown platform
```

### Command Patterns for AI Agents

```powershell
# ✅ CORRECT - Windows (use universal runner)
.\scripts\run-tests.ps1
.\scripts\run-tests.ps1 test_crossplane.bats
.\scripts\run-tests.ps1 -Shellcheck

# ✅ CORRECT - Linux/macOS (use universal runner)
./scripts/test-runner.sh
./scripts/test-runner.sh test_crossplane.bats
./scripts/test-runner.sh --shellcheck

# ❌ WRONG - Direct bash on Windows
bash scripts/test-runner.sh
sh scripts/test-runner.sh
bats tests/unit/test.bats

# ❌ WRONG - WSL without instance specification
wsl bash scripts/test-runner.sh
wsl bats tests/unit/test.bats

# ❌ WRONG - Hardcoded user paths
wsl -d mk8-test --cd /mnt/c/Users/JonathonManton/...

# ✅ CORRECT - Let the script handle paths
.\scripts\run-tests.ps1
```

### Configuration-Driven Approach

The project uses `.test-config.json` for all settings:
- WSL instance name
- Distribution
- Test directories
- Setup scripts

**AI agents should:**
1. Read `.test-config.json` for settings
2. Use universal test runners (`scripts/run-tests.ps1` or `scripts/test-runner.sh`)
3. Never hardcode paths or instance names
4. Never execute bash directly on Windows

## Security Notes

- This WSL instance is isolated from user's personal credentials
- Only test/dummy credentials should be configured
- Real AWS operations should use the Python implementation with proper credential management
- The prototype is for learning and testing only

## Maintenance

To update the mk8-test instance:

```bash
wsl -d mk8-test

# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Update tools as needed
# (kubectl, kind, helm, etc.)
```

To reset the instance if needed:

```powershell
# Export for backup (optional)
wsl --export mk8-test mk8-test-backup.tar

# Unregister (deletes the instance)
wsl --unregister mk8-test

# Reinstall
wsl --install -d Ubuntu-24.04 --name mk8-test
# Then re-run setup steps
```
