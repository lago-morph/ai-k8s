---
inclusion: always
---

# Platform-Specific Command Reference for AI Agents

## CRITICAL RULES

1. **ALWAYS detect platform before running bash commands**
2. **NEVER run `bash` directly on Windows**
3. **ALWAYS use universal test runners**
4. **NEVER hardcode user paths**

## Platform Detection

```python
import platform
system = platform.system()  # Returns: 'Windows', 'Linux', 'Darwin'
```

```javascript
const os = require('os');
const platform = os.platform();  // Returns: 'win32', 'linux', 'darwin'
```

```bash
# In bash
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="windows"
fi
```

## Command Matrix

| Task | Windows (PowerShell) | Linux/macOS (Bash) |
|------|---------------------|-------------------|
| Run all tests | `.\scripts\run-tests.ps1` | `./scripts/test-runner.sh` |
| Run specific test | `.\scripts\run-tests.ps1 test.bats` | `./scripts/test-runner.sh test.bats` |
| Run shellcheck | `.\scripts\run-tests.ps1 -Shellcheck` | `./scripts/test-runner.sh --shellcheck` |
| Setup WSL | `.\scripts\run-tests.ps1 -Setup` | N/A (not needed) |
| Show help | `.\scripts\run-tests.ps1 -Help` | `./scripts/test-runner.sh --help` |

## Forbidden Commands on Windows

```powershell
# ❌ NEVER - Uses default WSL instance
bash script.sh
sh script.sh
wsl bash script.sh
wsl command

# ❌ NEVER - Direct tool execution
bats tests/unit/test.bats
shellcheck lib/*.sh
pytest tests/

# ❌ NEVER - Hardcoded paths
wsl -d mk8-test --cd /mnt/c/Users/JonathonManton/...
```

## Required Commands on Windows

```powershell
# ✅ ALWAYS - Universal test runner
.\scripts\run-tests.ps1

# ✅ ALWAYS - Specify WSL instance if needed
wsl -d mk8-test bash script.sh

# ✅ ALWAYS - Use configuration
$config = Get-Content .test-config.json | ConvertFrom-Json
$instance = $config.wsl.instanceName
```

## Decision Tree for AI Agents

```
┌─ Detect Platform ─────────────────────────────────────┐
│                                                        │
│  Is system == 'Windows' or platform == 'win32'?       │
│                                                        │
├─ YES ─────────────────────────────────────────────────┤
│                                                        │
│  Use: .\scripts\run-tests.ps1                         │
│                                                        │
│  NEVER use:                                            │
│    - bash                                              │
│    - sh                                                │
│    - wsl without -d flag                               │
│    - direct tool execution (bats, shellcheck)          │
│                                                        │
└────────────────────────────────────────────────────────┘
                         │
                         │
┌─ NO ──────────────────┴────────────────────────────────┐
│                                                        │
│  Is system == 'Linux' or 'Darwin'?                     │
│                                                        │
├─ YES ─────────────────────────────────────────────────┤
│                                                        │
│  Use: ./scripts/test-runner.sh                        │
│                                                        │
│  Can also use tools directly:                          │
│    - bats tests/unit/                                  │
│    - shellcheck lib/*.sh                               │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Example: Running Tests (AI Agent Code)

### Python Example

```python
import platform
import subprocess

def run_tests(test_file=None):
    system = platform.system()
    
    if system == 'Windows':
        cmd = ['.\\scripts\\run-tests.ps1']
        if test_file:
            cmd.append(test_file)
        subprocess.run(cmd, shell=True, check=True)
    else:
        cmd = ['./scripts/test-runner.sh']
        if test_file:
            cmd.append(test_file)
        subprocess.run(cmd, check=True)

# Usage
run_tests()  # Run all tests
run_tests('test_crossplane.bats')  # Run specific test
```

### JavaScript Example

```javascript
const { exec } = require('child_process');
const os = require('os');

function runTests(testFile = null) {
    const platform = os.platform();
    let cmd;
    
    if (platform === 'win32') {
        cmd = '.\\scripts\\run-tests.ps1';
        if (testFile) cmd += ` ${testFile}`;
    } else {
        cmd = './scripts/test-runner.sh';
        if (testFile) cmd += ` ${testFile}`;
    }
    
    exec(cmd, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error: ${error.message}`);
            return;
        }
        console.log(stdout);
    });
}

// Usage
runTests();  // Run all tests
runTests('test_crossplane.bats');  // Run specific test
```

## Configuration-Driven Approach

Always read from `.test-config.json`:

```powershell
# PowerShell
$config = Get-Content .test-config.json | ConvertFrom-Json
$wslInstance = $config.wsl.instanceName
$testDir = $config.testing.testDirectory
```

```bash
# Bash (requires jq)
WSL_INSTANCE=$(jq -r '.wsl.instanceName' .test-config.json)
TEST_DIR=$(jq -r '.testing.testDirectory' .test-config.json)
```

```python
# Python
import json

with open('.test-config.json') as f:
    config = json.load(f)
    wsl_instance = config['wsl']['instanceName']
    test_dir = config['testing']['testDirectory']
```

## Common Mistakes to Avoid

### Mistake 1: Running bash directly on Windows

```powershell
# ❌ WRONG
bash ./scripts/test-runner.sh

# ✅ CORRECT
.\scripts\run-tests.ps1
```

### Mistake 2: Hardcoding paths

```powershell
# ❌ WRONG
wsl -d mk8-test --cd /mnt/c/Users/JonathonManton/Documents/src/ai-k8s bats tests/

# ✅ CORRECT
.\scripts\run-tests.ps1
```

### Mistake 3: Not detecting platform

```python
# ❌ WRONG - Assumes Linux
subprocess.run(['./scripts/test-runner.sh'])

# ✅ CORRECT - Detects platform
system = platform.system()
if system == 'Windows':
    subprocess.run(['.\\scripts\\run-tests.ps1'], shell=True)
else:
    subprocess.run(['./scripts/test-runner.sh'])
```

### Mistake 4: Using default WSL

```powershell
# ❌ WRONG - Uses default WSL instance
wsl bats tests/unit/test.bats

# ✅ CORRECT - Uses isolated instance via runner
.\scripts\run-tests.ps1 test.bats
```

## Quick Reference Card

```
╔════════════════════════════════════════════════════════╗
║  AI Agent Quick Reference: Running Tests               ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  1. Detect platform (Windows/Linux/macOS)              ║
║  2. Use appropriate test runner                        ║
║  3. Never run bash directly on Windows                 ║
║  4. Never hardcode paths or instance names             ║
║                                                        ║
║  Windows:  .\scripts\run-tests.ps1                     ║
║  Linux:    ./scripts/test-runner.sh                    ║
║  macOS:    ./scripts/test-runner.sh                    ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

## Testing This Guidance

To verify you're following these guidelines correctly:

1. **Check platform detection**: Ensure you detect Windows vs Linux/macOS
2. **Check command**: Verify you're using the universal test runner
3. **Check paths**: Ensure no hardcoded user paths
4. **Check WSL usage**: On Windows, verify you're not using `bash` or `wsl` without `-d`

## See Also

- `.claude/steering/wsl-testing.md` - Complete WSL testing guidelines
- `.test-config.json` - Project configuration
- `REUSABLE-WSL-TESTING-PATTERN.md` - Pattern for other projects
