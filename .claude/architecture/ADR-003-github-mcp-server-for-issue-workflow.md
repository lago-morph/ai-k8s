# ADR-003: GitHub MCP Server for Issue-Driven Development Workflow

## Status

ACCEPTED

## Date

2024-12-09

## Context

The mk8 project uses AI agents extensively for development. Currently, when issues are discovered outside of active development sessions, there's no streamlined way to:

1. Capture issues in a structured format (GitHub Issues)
2. Have AI agents discover and work on open issues
3. Create pull requests from agent-driven development
4. Review, merge, and close issues programmatically

This creates friction in the development workflow, especially for:
- Issues discovered during testing or production use
- Asynchronous development where issues are logged for later work
- Maintaining traceability between issues, code changes, and PRs

The Model Context Protocol (MCP) provides a standardized way for AI agents to interact with external systems. The official GitHub MCP server (`@modelcontextprotocol/server-github`) offers structured access to GitHub's API, enabling agents to:
- Read and create issues
- Manage pull requests
- Access repository files
- Search code and issues

## Decision

We will integrate the official GitHub MCP server (`@modelcontextprotocol/server-github`) into the mk8 development workflow to enable AI agents to:

1. **Discover work**: Query open GitHub issues to find tasks
2. **Develop solutions**: Work through issues using the spec-driven development process
3. **Create PRs**: Generate pull requests with changes
4. **Complete workflow**: Review, merge, and close issues programmatically

**Authentication**: GitHub Personal Access Token (PAT) stored as an environment variable or in OS-level credential storage.

**Scope**: The MCP server will be configured with permissions to:
- Read repository contents
- Create, read, and update issues
- Create, read, and update pull requests
- Manage labels and milestones

## Consequences

### Positive

- **Seamless workflow**: Issues → Development → PR → Merge becomes fully agent-driven
- **Traceability**: Clear link between issues, commits, and PRs
- **Asynchronous development**: Issues can be logged anytime, worked on later
- **Standardized interface**: MCP provides consistent API for agents
- **Official support**: Using the official MCP server ensures compatibility and updates
- **Reduced context switching**: Agents can manage entire workflow without human intervention

### Negative

- **Token management**: Requires secure storage of GitHub PAT
- **Permission scope**: PAT needs broad permissions (repo, issues, PRs)
- **Rate limiting**: GitHub API rate limits may affect agent operations
- **Dependency**: Adds external dependency on MCP server maintenance
- **Learning curve**: Team needs to understand MCP configuration

### Neutral

- **Alternative exists**: Could use GitHub CLI (`gh`) instead, but MCP provides better agent integration
- **Configuration overhead**: Requires MCP server setup and configuration

## Alternatives Considered

### Alternative 1: GitHub CLI (`gh`)

**Description**: Use the official GitHub CLI tool for issue and PR management.

**Pros:**
- Official GitHub tool
- Well-documented and mature
- No additional dependencies beyond CLI
- Familiar to developers

**Cons:**
- Requires parsing CLI output (text/JSON)
- Less structured for agent consumption
- No standardized protocol like MCP
- More complex error handling

**Why not chosen**: MCP provides a more structured, agent-friendly interface with better error handling and type safety.

### Alternative 2: Direct GitHub API Calls

**Description**: Have agents make direct HTTP requests to GitHub's REST/GraphQL API.

**Pros:**
- No intermediary dependencies
- Full control over API interactions
- Maximum flexibility

**Cons:**
- Requires implementing authentication, pagination, error handling
- More code to maintain
- No standardization across different tools
- Reinventing functionality MCP already provides

**Why not chosen**: MCP server already implements best practices for GitHub API interaction, reducing maintenance burden.

### Alternative 3: GitHub Actions Workflow Dispatch

**Description**: Use GitHub Actions to trigger workflows that create issues/PRs.

**Pros:**
- Native GitHub integration
- No local dependencies
- Audit trail in Actions logs

**Cons:**
- Asynchronous, harder for agents to get feedback
- Limited to GitHub Actions environment
- More complex to debug
- Doesn't help with reading/discovering issues

**Why not chosen**: Doesn't solve the discovery problem and adds unnecessary complexity.

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- `.claude/specs/github-workflow-automation/` - Implementation spec
- Related to: ADR-004 (Testing verification tools)

## Notes

- The GitHub PAT should have `repo`, `read:org`, and `workflow` scopes
- Consider using GitHub Apps for more granular permissions in the future
- MCP server configuration will be stored in `.kiro/settings/mcp.json` (workspace-level)
- This ADR focuses on the decision to use GitHub MCP; implementation details are in the spec
