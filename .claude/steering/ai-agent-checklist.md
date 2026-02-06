---
inclusion: always
---

# AI Agent Pre-Execution Checklist

Before executing any bash command or test, verify:

## ✅ Platform Detection

- [ ] I have detected the platform (Windows/Linux/macOS)
- [ ] I know which test runner to use based on platform
- [ ] I will NOT assume the platform

## ✅ Windows-Specific Rules

If platform is Windows:

- [ ] I will use `.\scripts\run-tests.ps1`
- [ ] I will NOT use `bash` command
- [ ] I will NOT use `sh` command
- [ ] I will NOT use `wsl` without `-d` flag
- [ ] I will NOT execute BATS directly
- [ ] I will NOT execute shellcheck directly
- [ ] I will NOT hardcode user paths

## ✅ Linux/macOS Rules

If platform is Linux or macOS:

- [ ] I will use `./scripts/test-runner.sh`
- [ ] I can use bash tools directly if needed
- [ ] I will verify tools are installed

## ✅ Configuration

- [ ] I have read `.test-config.json` for settings
- [ ] I am using configured instance name (not hardcoded)
- [ ] I am using configured test directory (not hardcoded)
- [ ] I am using configured setup script (not hardcoded)

## ✅ Command Verification

Before executing, verify the command matches:

### Windows
```powershell
# ✅ CORRECT
.\scripts\run-tests.ps1
.\scripts\run-tests.ps1 test_file.bats
.\scripts\run-tests.ps1 -Shellcheck
.\scripts\run-tests.ps1 -Setup
```

### Linux/macOS
```bash
# ✅ CORRECT
./scripts/test-runner.sh
./scripts/test-runner.sh test_file.bats
./scripts/test-runner.sh --shellcheck
```

## ❌ Forbidden Patterns

I will NOT execute any of these on Windows:

```powershell
# ❌ FORBIDDEN
bash script.sh
sh script.sh
wsl bash script.sh
wsl command
bats tests/unit/test.bats
shellcheck lib/*.sh
wsl -d mk8-test --cd /mnt/c/Users/JonathonManton/...
```

## 🔍 Self-Check Questions

1. **Am I on Windows?**
   - If YES → Use `.\scripts\run-tests.ps1`
   - If NO → Use `./scripts/test-runner.sh`

2. **Am I using bash directly on Windows?**
   - If YES → STOP! Use PowerShell runner instead

3. **Am I hardcoding paths?**
   - If YES → STOP! Read from `.test-config.json`

4. **Am I specifying WSL instance?**
   - If using `wsl` directly → Must include `-d <instance>`
   - Better → Use universal test runner

## 📋 Execution Template

```python
# Template for AI agents
import platform
import subprocess
import json

# 1. Detect platform
system = platform.system()

# 2. Load configuration
with open('.test-config.json') as f:
    config = json.load(f)

# 3. Choose command based on platform
if system == 'Windows':
    cmd = ['.\\scripts\\run-tests.ps1']
else:
    cmd = ['./scripts/test-runner.sh']

# 4. Add arguments if needed
# cmd.append('test_file.bats')

# 5. Execute
subprocess.run(cmd, shell=(system == 'Windows'), check=True)
```

## 🚨 Emergency Stop Conditions

STOP and ask for clarification if:

- [ ] Platform detection fails or returns unexpected value
- [ ] `.test-config.json` is missing or malformed
- [ ] Test runner scripts don't exist
- [ ] User asks to run bash directly on Windows
- [ ] Unsure which command to use

## ✅ Final Verification

Before executing, I confirm:

1. ✅ Platform detected correctly
2. ✅ Using correct test runner for platform
3. ✅ Not using forbidden commands
4. ✅ Not hardcoding paths
5. ✅ Configuration loaded from `.test-config.json`
6. ✅ Command matches approved patterns

## 📚 Reference Documents

- `.claude/steering/wsl-testing.md` - Complete WSL guidelines
- `.claude/steering/platform-commands.md` - Command reference
- `.test-config.json` - Project configuration
- `REUSABLE-WSL-TESTING-PATTERN.md` - Pattern documentation

---

**Remember: When in doubt, use the universal test runner!**
