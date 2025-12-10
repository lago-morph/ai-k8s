# WSL Testing Documentation Index

## For Users (Getting Started)

**Start here:** [WSL-SETUP.md](../WSL-SETUP.md)
- Quick 5-minute setup
- Detailed setup instructions
- Troubleshooting guide
- Running tests

## For AI Agents (Development)

**Always included steering files:**
- `.claude/steering/wsl-testing.md` - Complete WSL guidelines
- `.claude/steering/platform-commands.md` - Command reference
- `.claude/steering/ai-agent-checklist.md` - Pre-execution checklist

**Key rules:**
- ❌ NEVER run `bash` directly on Windows
- ✅ ALWAYS use `.\scripts\run-tests.ps1` on Windows
- ✅ ALWAYS detect platform first

## For Other Projects (Reusability)

**Template:** [REUSABLE-WSL-TESTING-PATTERN.md](../REUSABLE-WSL-TESTING-PATTERN.md)
- Complete pattern documentation
- Files to copy
- Customization guide
- Integration steps

## Quick Reference

### Running Tests

```powershell
# Windows
.\scripts\run-tests.ps1              # Run all tests
.\scripts\run-tests.ps1 test.bats    # Run specific test
.\scripts\run-tests.ps1 -Shellcheck  # Run shellcheck
.\scripts\run-tests.ps1 -Setup       # Set up WSL instance
```

```bash
# Linux/macOS
./scripts/test-runner.sh             # Run all tests
./scripts/test-runner.sh test.bats   # Run specific test
./scripts/test-runner.sh --shellcheck # Run shellcheck
```

### Configuration

Edit `.test-config.json` to customize:
- WSL instance name
- Test framework
- Test directories
- Setup script path

## Documentation Structure

```
Root Directory:
├── WSL-SETUP.md                           # Main setup guide
├── REUSABLE-WSL-TESTING-PATTERN.md        # Template for other projects
├── .test-config.json                      # Configuration
└── scripts/
    ├── run-tests.ps1                      # Windows test runner
    └── test-runner.sh                     # Linux/macOS test runner

AI Agent Steering:
├── .claude/steering/
    ├── wsl-testing.md                     # WSL guidelines
    ├── platform-commands.md               # Command reference
    └── ai-agent-checklist.md              # Pre-execution checklist
```

## See Also

- [AGENTS.md](../AGENTS.md) - Development guidelines
- [README.md](../README.md) - Project overview
- `.test-config.json` - Project configuration
