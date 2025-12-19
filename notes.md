Add spec: prototype.  Only shell script, check safety in every script.  one script per thing.  refer to other docs.

Add spec: safety.  check that only AWS have access to is ephemeral environment from pluralsight and I do not have access to others any other way.  check that I do not have access to any other clusteres.  check all repo access, limited to only desired ones, no other github keys.

add spec self-test framework: scripts to set up auto testing in my terminal with shell scripts, clear instructions, auto enhanced every time a feature is completed

## Completed Spec Creation (2024-12-09)

### github-workflow-automation (DRAFT)
- **Status**: Draft requirements created, not yet reviewed
- **Location**: `.claude/specs/github-workflow-automation/`
- **Files**: requirements.md, CONTEXT.md
- **ADR**: ADR-003 (GitHub MCP server decision)
- **Purpose**: Enable AI agents to manage GitHub issue → development → PR → merge workflow
- **Key Decision**: Use official GitHub MCP server (`@modelcontextprotocol/server-github`)
- **Next Steps**: Review requirements, refine, proceed to design phase

### testing-verification-tools (DRAFT)
- **Status**: Draft requirements created, not yet reviewed
- **Location**: `.claude/specs/testing-verification-tools/`
- **Files**: requirements.md, CONTEXT.md, SCOPE-DECISIONS.md
- **ADR**: ADR-004 (kubectl/AWS CLI decision)
- **Purpose**: Provide read-only verification of K8s and AWS resources during integration testing
- **Key Decisions**: 
  - Use kubectl CLI (not K8s MCP server - maturity concerns)
  - Use AWS CLI (not AWS MCP server - better for ephemeral credentials)
  - Read-only access via RBAC and IAM policies
- **Deferred Decisions**: 
  - Integration test framework scope (minimal vs helpers vs full framework)
  - IAM policy creation approach (manual vs script vs agent)
  - Credential validation strategy
- **Next Steps**: Review requirements, resolve scope questions, proceed to design phase

### Architecture Decision Records Created
- **ADR-003**: GitHub MCP Server for Issue-Driven Development Workflow
- **ADR-004**: kubectl and AWS CLI for Read-Only Testing Verification

### Updated Files
- `.claude/specs/SPECS-STATUS.md` - Added both draft specs to tracking
- `.claude/architecture/` - Added ADR-003 and ADR-004

### Notes for Future Sessions
- Both specs marked as DRAFT - NOT REVIEWED
- Context files preserve discussion details not in requirements
- SCOPE-DECISIONS.md in testing-verification-tools captures deferred decisions
- Can pick up requirements review later by reading CONTEXT.md files
- ADRs explain the "why" behind tool choices
