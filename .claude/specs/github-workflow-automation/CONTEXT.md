# Context and Planning Notes - GitHub Workflow Automation

**Purpose**: This file preserves context from the initial planning discussion that may not be fully captured in the requirements document. Future AI agents should read this file when working on this spec.

## Original Use Case

The GitHub MCP server is being added to enable a specific workflow:

1. **Issue Creation**: Developer discovers a bug or wants a feature while NOT actively developing
2. **Issue Logging**: Developer creates a GitHub issue to capture the work
3. **Agent Discovery**: Later, developer asks AI agent to "look for open issues"
4. **Agent Development**: Agent picks an issue, works through it using spec-driven development
5. **PR Creation**: Agent creates a pull request with the changes
6. **Review & Merge**: Agent (or human) reviews, approves, and merges the PR
7. **Issue Closure**: Issue is automatically closed when PR merges

This creates a seamless asynchronous development workflow where issues can be logged anytime and worked on later.

## Credential Management Strategy

### GitHub PAT Storage

**Decision**: Use environment variable approach as primary method.

**Rationale**:
- Simple and works across all platforms
- Easy to configure in CI/CD environments
- No additional dependencies
- Can be set in shell profile for persistence

**Implementation**:
```bash
# In ~/.bashrc or ~/.zshrc
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

**Alternative Considered**: GitHub CLI credential helper
- More secure (uses OS keychain)
- Requires `gh` CLI to be installed and configured
- May be added as optional enhancement later

### MCP Configuration Location

**Decision**: Store in `.kiro/settings/mcp.json` (workspace-level)

**Rationale**:
- Workspace-specific configuration
- Doesn't pollute user-level settings
- Can be different per project
- Follows Kiro conventions

**Example Configuration**:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## Integration with mk8 Development Workflow

### Spec-Driven Development Integration

When an agent works on a GitHub issue, it should:

1. Create a feature branch: `issue-{number}-{slug}`
2. Follow the standard spec workflow:
   - Create requirements.md
   - Create design.md  
   - Create tasks.md
   - Execute tasks one at a time
3. Commit changes incrementally
4. Create PR when complete

### Branch Naming Convention

**Format**: `issue-{number}-{short-description}`

**Examples**:
- `issue-42-add-eks-support`
- `issue-123-fix-bootstrap-timeout`
- `issue-7-improve-error-messages`

### PR Description Template

PRs should include:
- Link to issue: "Closes #123"
- Summary of changes
- Link to spec documents if applicable
- Testing performed
- Any breaking changes

## GitHub MCP Server Details

### Official Package

**Package**: `@modelcontextprotocol/server-github`
**Source**: https://github.com/modelcontextprotocol/servers/tree/main/src/github
**Maintained by**: Anthropic (MCP team)

### Required Token Scopes

The GitHub PAT must have these scopes:
- `repo` - Full control of private repositories (includes read/write for code, issues, PRs)
- `read:org` - Read organization membership (if using org repos)
- `workflow` - Update GitHub Actions workflows (if needed)

### Capabilities

The GitHub MCP server provides:
- **Issues**: Create, read, update, close, comment
- **Pull Requests**: Create, read, update, merge, comment, request reviews
- **Repositories**: Read files, search code
- **Labels**: Create, read, apply to issues/PRs
- **Milestones**: Read, assign to issues
- **Reviews**: Request reviews, read review status

## Future Enhancements

### Potential Additions (Not in Initial Scope)

1. **GitHub Actions Integration**
   - Trigger workflows from agent
   - Monitor workflow status
   - React to workflow failures

2. **Advanced PR Management**
   - Handle merge conflicts automatically
   - Rebase branches
   - Cherry-pick commits

3. **Issue Templates**
   - Use GitHub issue templates
   - Validate issue format
   - Auto-label based on template

4. **Project Board Integration**
   - Move issues across project boards
   - Update issue status
   - Track progress

5. **GitHub Apps**
   - Migrate from PAT to GitHub App for better security
   - More granular permissions
   - Better audit trail

## Design Phase Considerations

When moving to the design phase, consider:

### Architecture Decisions

1. **MCP Server Installation**
   - How to install the MCP server (npm, npx, etc.)
   - Version pinning strategy
   - Update mechanism

2. **Configuration Management**
   - How to validate MCP configuration
   - How to test connectivity
   - Error messages for misconfiguration

3. **Agent Workflow**
   - How agents discover issues (query patterns)
   - How agents decide which issue to work on
   - How agents track progress

4. **Error Handling**
   - Rate limit handling strategy
   - Retry logic for transient failures
   - Fallback mechanisms

### Testing Strategy

1. **Unit Tests**
   - Mock GitHub API responses
   - Test error handling
   - Test credential validation

2. **Integration Tests**
   - Test against real GitHub API (test repo)
   - Test full workflow (issue → PR → merge)
   - Test error scenarios (rate limits, auth failures)

3. **Manual Testing**
   - Document manual testing procedures
   - Create test issues in mk8 repo
   - Verify agent can complete workflow

## Unresolved Questions

These questions should be addressed during requirements review:

1. **Multi-Repository Support**
   - Should agents work across multiple repos?
   - How to configure multiple repo access?

2. **Issue Assignment**
   - Should agents assign issues to themselves?
   - How to prevent multiple agents working on same issue?

3. **PR Review Requirements**
   - Should agents wait for human review?
   - Can agents approve their own PRs?
   - What checks must pass before merge?

4. **Branch Protection**
   - How to handle branch protection rules?
   - Should agents be able to bypass protections?

5. **Notification Strategy**
   - Should agents notify humans at certain points?
   - How to configure notification preferences?

## Related Documentation

- ADR-003: Decision to use GitHub MCP server
- ADR-004: Decision to use kubectl/AWS CLI for testing (related spec)
- `.claude/specs/prototype/`: Example of spec-driven development workflow
- `AGENTS.md`: Overall agent workflow documentation

## Notes for Future Agents

When working on this spec:

1. **Read ADR-003 first** - Understand why GitHub MCP was chosen
2. **Review existing specs** - Follow the same structure as prototype spec
3. **Test incrementally** - Set up MCP server and test basic operations before full implementation
4. **Consider security** - GitHub PAT has broad permissions, handle carefully
5. **Document examples** - Include example agent interactions in design doc
