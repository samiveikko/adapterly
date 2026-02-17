# MCP Integration

Adapterly integrates with Claude AI through the Model Context Protocol (MCP), enabling intelligent automation where AI can directly interact with your connected systems.

## What is MCP?

The Model Context Protocol (MCP) is a standard that allows AI assistants like Claude to use external tools. Adapterly acts as an MCP server, providing Claude with tools to:

- Read data from your connected systems
- Write and update data
- Monitor task status

## How It Works

```
Claude AI
    ↓ (MCP protocol)
Adapterly MCP Server
    ↓ (authenticated requests)
Your Connected Systems
    (Infrakit, Google Sheets, etc.)
```

1. Claude receives a user request
2. Claude decides which Adapterly tools to use
3. Adapterly authenticates and calls external APIs
4. Results are returned to Claude
5. Claude presents the information to the user

## Available Tools

### System Tools

For each configured system, Adapterly generates MCP tools:

```
{system}_{resource}_{action}
```

**Example tools for Infrakit:**
- `infrakit_projects_list` - List all projects
- `infrakit_projects_get` - Get project details
- `infrakit_logpoints_create` - Create logpoints
- `infrakit_masshaul_get_trips` - Get mass haul trips

### Management Tools

Workspace and account management (requires Power mode):

| Tool | Type | Description |
|------|------|-------------|
| `workspace_create` | write | Create/get workspace by external_id (idempotent) |
| `workspace_list` | read | List account's workspaces |
| `workspace_get` | read | Get workspace details |
| `workspace_add_member` | write | Add user to workspace |
| `workspace_remove_member` | write | Remove user from workspace |
| `workspace_update_role` | write | Update user's role |
| `account_get` | read | Get account details |
| `admin_session_create` | write | Create federated login session |

## Using MCP Tools

### Listing Projects

```
User: "Show me all my Infrakit projects"

Claude uses: infrakit_projects_list()

Claude: "Here are your 5 projects:
1. Highway 101 Extension
2. Bridge Renovation Phase 2
3. Commercial Center Foundation
..."
```

### Creating Data

```
User: "Add a logpoint at coordinates 60.1699, 24.9384"

Claude uses: infrakit_logpoints_create(
    project_uuid="...",
    coordinates=[60.1699, 24.9384],
    description="New survey point"
)

Claude: "I've created the logpoint at the specified location."
```

## MCP Modes

### Safe Mode (Default)

- Read operations allowed
- Write operations blocked

### Power Mode

- All operations allowed
- Required for management tools (workspace_create, etc.)
- Enable via API key settings

## Context Setup

Before using tools, set the execution context:

```
Claude uses: set_context(
    account_id="123",
    workspace_id="ws-uuid-here"
)
```

This establishes which account/workspace you're working with.

## Setting Up MCP

### 1. Generate API Key

1. Go to **MCP Gateway** → **API Keys**
2. Click **Create API Key**
3. Select an Agent Profile (optional) or set mode manually
4. Copy the key (it won't be shown again)

### 2. Connection Options

#### Option A: Streamable HTTP (Remote Agents, Claude.ai)

MCP Streamable HTTP - single endpoint for all JSON-RPC communication:

```
Endpoint: https://adapterly.ai/mcp/v1/
```

**Methods:**
- `POST /mcp/v1/` - Send JSON-RPC message(s)
- `GET /mcp/v1/` - Open SSE stream for server notifications (optional)
- `DELETE /mcp/v1/` - Close session

**Headers:**
- `Authorization: Bearer <api_key>`
- `Content-Type: application/json`
- `Accept: application/json` or `text/event-stream`
- `Mcp-Session-Id: <session_id>` (returned by server, use for subsequent requests)

**Example:**
```javascript
// Send JSON-RPC message
const response = await fetch('https://adapterly.ai/mcp/v1/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ak_live_xxx',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/list',
    params: {}
  })
});

// Get session ID from response header
const sessionId = response.headers.get('Mcp-Session-Id');
const result = await response.json();

// Use session ID for subsequent requests
const response2 = await fetch('https://adapterly.ai/mcp/v1/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ak_live_xxx',
    'Content-Type': 'application/json',
    'Mcp-Session-Id': sessionId
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/call',
    params: { name: 'infrakit_projects_list', arguments: {} }
  })
});
```

#### Option B: stdio (Claude Code, Local Development)

For Claude Code or local CLI usage, run the MCP server directly:

```bash
python manage.py mcp_server \
  --account-id 123 \
  --api-key ak_live_xxx \
  --mode safe
```

**Claude Code configuration** (`~/.claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "adapterly": {
      "command": "python",
      "args": ["manage.py", "mcp_server",
               "--account-id", "123",
               "--api-key", "ak_live_xxx",
               "--mode", "safe"],
      "cwd": "/path/to/workflow-server"
    }
  }
}
```

### 3. Verify Connection

Ask Claude:
> "What Adapterly tools do you have access to?"

Claude should list all available system tools.

## Tool Parameters

Each tool has specific parameters based on its action:

### List Actions
```json
{
  "page": 1,
  "pageSize": 100,
  "fetch_all_pages": true  // Automatically paginate
}
```

### Get Actions
```json
{
  "id": "project-uuid-here"
}
```

### Create Actions
```json
{
  "data": {
    "name": "New Project",
    "description": "Project description"
  }
}
```

## Pagination

For list endpoints with many items, Adapterly handles pagination automatically:

```
User: "Get all logpoints from the project"

Claude uses: infrakit_logpoints_list(
    project_uuid="...",
    fetch_all_pages=true
)
```

**Safety limits:**
- Maximum 100 pages
- Maximum 10,000 items
- 2-minute timeout
- Stops on empty or duplicate pages

## Error Handling

When an MCP tool fails, Claude receives error details:

```json
{
  "error": true,
  "message": "Authentication failed",
  "details": "Token expired or invalid"
}
```

Claude will typically:
1. Explain the error to the user
2. Suggest remediation steps
3. Retry if appropriate

## Best Practices

### 1. Be Specific in Requests
Instead of "get project data", say "list all active Infrakit projects".

### 2. Provide Context
Give Claude the information it needs:
> "Using project ID abc123, create a logpoint at coordinates 60.17, 24.94"

### 3. Review Before Writing
Ask Claude to show you what it will create before actually creating it:
> "Show me the logpoint data you would create, but don't create it yet"

## Security

### Token Permissions
API tokens have the same permissions as the user who created them. Use dedicated service accounts for automation.

### Audit Trail
All MCP tool calls are logged and visible in the Executions section.

### Rate Limiting
MCP calls are subject to the same rate limits as direct API access.

## Troubleshooting

### "Tool not found"
- Check that the system is properly configured
- Verify the interface has the expected resources and actions
- Restart Claude Desktop after configuration changes

### "Authentication failed"
- Regenerate your API token
- Ensure the token is correctly set in environment variables
- Check that credentials are configured for the target system

### "Timeout"
- External API may be slow or unreachable
- Try a smaller request (fewer items)
- Check rate limit status
