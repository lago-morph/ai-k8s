# Documentation Structure

## Root Level Documentation

### User-Facing
- **README.md** - Project overview, installation, quick start
- **WSL-SETUP.md** - WSL testing environment setup (main guide)
- **REUSABLE-WSL-TESTING-PATTERN.md** - Template for other projects

### Development
- **AGENTS.md** - Complete AI agent development guidelines (single source of truth)
- **CLAUDE.md** - Minimal redirect to AGENTS.md (DO NOT ADD CONTENT HERE)

## AI Agent Steering (.claude/steering/)

**Always included in AI agent context:**

- **wsl-testing.md** - Complete WSL testing guidelines
  - Critical rules (never run bash on Windows)
  - Platform detection requirements
  - Command patterns
  - Configuration approach

- **platform-commands.md** - Command reference
  - Platform detection code
  - Command matrix
  - Decision trees
  - Example implementations

- **ai-agent-checklist.md** - Pre-execution checklist
  - Platform detection verification
  - Command verification
  - Forbidden patterns
  - Self-check questions

- **product.md** - Product context (what mk8 does)
- **tech.md** - Technical standards (Python, testing, etc.)
- **structure.md** - Project organization

## Specifications (.claude/specs/)

- **SPECS-STATUS.md** - Current spec status
- **prototype/** - Prototype spec (requirements, design, tasks)
- Other feature specs...

## Documentation Directory (docs/)

- **WSL-TESTING-INDEX.md** - Navigation guide for WSL docs
- **DOCUMENTATION-STRUCTURE.md** - This file
- **tutorials/** - Tutorial content

## Configuration Files

- **.test-config.json** - WSL and testing configuration
- **pyproject.toml** - Python project configuration
- **setup.py** - Python package setup

## Scripts

- **scripts/run-tests.ps1** - Windows test runner
- **scripts/test-runner.sh** - Linux/macOS test runner
- **prototype/setup-wsl-test-env.sh** - WSL environment setup

## Documentation Principles

### 1. Single Source of Truth
- Each topic has ONE primary document
- Other documents reference it, don't duplicate

### 2. Audience-Specific
- **Users**: README.md, WSL-SETUP.md
- **AI Agents**: .claude/steering/*.md
- **Developers**: AGENTS.md, specs/
- **Other Projects**: REUSABLE-WSL-TESTING-PATTERN.md

### 3. Layered Information
- **Quick Start**: Top of main documents
- **Detailed Guide**: Middle sections
- **Reference**: Bottom or separate files
- **Troubleshooting**: End of guides

### 4. Cross-References
- Use relative links
- Point to primary documents
- Avoid circular references

## Finding Documentation

### "I want to set up WSL testing"
→ [WSL-SETUP.md](../WSL-SETUP.md)

### "I want to use this pattern in another project"
→ [REUSABLE-WSL-TESTING-PATTERN.md](../REUSABLE-WSL-TESTING-PATTERN.md)

### "I'm an AI agent, what are the rules?"
→ `.claude/steering/wsl-testing.md` (auto-included)
→ `.claude/steering/platform-commands.md` (auto-included)

### "I want to understand the project"
→ [README.md](../README.md)

### "I want to contribute"
→ [AGENTS.md](../AGENTS.md)

### "I need a command reference"
→ `.claude/steering/platform-commands.md`

### "I need to navigate WSL docs"
→ [WSL-TESTING-INDEX.md](WSL-TESTING-INDEX.md)

## Maintenance

### Adding New Documentation
1. Determine audience (user/AI/developer)
2. Check if existing doc can be extended
3. If new doc needed, add to appropriate location
4. Update this structure document
5. Add cross-references

### Updating Documentation
1. Update primary document
2. Check for references in other docs
3. Update cross-references if needed
4. Don't duplicate content

### Removing Documentation
1. Check for references (grep)
2. Update references to point elsewhere
3. Remove file
4. Update this structure document
