# Getting Started with Adapterly

Welcome to Adapterly! This tutorial will help you understand what Adapterly is, how it works, and how to get started with your first automation.

---

## What is Adapterly?

**Adapterly** is an AI-powered integration platform that helps you connect different systems and automate data flows between them. Think of it as a bridge that connects your business tools and makes them work together automatically.

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **No coding required** | Build automations through an intuitive interface |
| **Connect any API** | Works with REST APIs, webhooks, and custom integrations |
| **AI-powered** | AI assistant helps with automation and external agents can use your integrations |
| **Reliable** | Built-in error handling, retries, and monitoring |
| **Secure** | Credentials stored encrypted, audit logging, role-based access |

### Common Use Cases

- **Data synchronization** - Keep data in sync between CRM, spreadsheets, and databases
- **Report generation** - Automatically collect data and generate reports
- **Process automation** - Trigger actions based on events in other systems
- **AI agent backends** - Provide integrations as tools for AI assistants

---

## How Adapterly Works

Adapterly uses a simple but powerful model:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   SYSTEMS   │ ──▶ │ INTEGRATIONS│ ──▶ │  MCP TOOLS  │
│ (your APIs) │     │ (connections)│     │ (AI access) │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 1. Systems

A **System** represents an external service you want to connect to. This could be:

- A SaaS product (Salesforce, HubSpot, Google Sheets)
- Your own internal API
- Any REST-based service

Each system has:
- **Resources** - Data types (contacts, deals, projects)
- **Actions** - Operations (list, get, create, update, delete)
- **Authentication** - API keys, OAuth, or custom auth

**Example:** A "Salesforce" system might have a "Contacts" resource with "list" and "create" actions.

### 2. Integrations

**Integrations** connect your systems and enable data flow between them:

- Each system exposes resources and actions
- MCP tools are auto-generated for AI agent access
- API tokens control access and permissions

**Example:** Connecting Salesforce and Google Sheets so an AI agent can read contacts and update spreadsheets.

### 3. MCP Tools

**MCP Tools** are auto-generated functions that AI agents can use to interact with your connected systems:

- Each system's resources and actions become callable tools
- Tools follow the naming pattern: `{system}_{resource}_{action}`
- All tool calls are logged and auditable

---

## Quick Start Guide

### Step 1: Add Your First System

1. Go to **Systems** in the navigation
2. Click **Add System**
3. Choose a type:
   - **OpenAPI** - Upload a spec file (recommended for REST APIs)
   - **Manual** - Define resources and actions yourself
4. Configure authentication
5. Test the connection

### Step 2: Configure Resources

1. Review the discovered resources and actions
2. Test individual endpoints
3. Verify data is returned correctly

### Step 3: Test via MCP

1. Generate an API key for MCP access
2. Connect Claude or another AI agent
3. Ask the agent to list available tools
4. Test reading data from your connected systems

### Step 4: Integrate

Once tested, you can:
- **Use via MCP** - AI agents can access your systems as tools
- **Use via API** - Call system endpoints directly
- **Share access** - Invite team members with appropriate roles

---

## Understanding Variables

Variables help configure your integrations dynamically.

### Variable Syntax

```yaml
# Environment variable (secret)
api_key: "${env:MY_API_KEY}"

# Configuration variable
sheet_id: "${var:target_sheet}"
```

### Common Patterns

```yaml
# Use environment variable for sensitive data
params:
  apiKey: "${env:SERVICE_API_KEY}"

# Use configuration variable
params:
  spreadsheetId: "${var:sheet_id}"
```

---

## For AI Agents (MCP)

Adapterly exposes your connected systems as tools for AI agents via the **Model Context Protocol (MCP)**.

### How It Works

1. Connect systems and configure resources
2. Enable MCP access for your account
3. Generate an API key for the agent
4. The agent can discover and call your system tools

### Example Agent Flow

```
User: "Get me the latest sales report"
    │
    ▼
Agent: Calls "salesforce_reports_get" tool in Adapterly
    │
    ▼
Adapterly: Fetches the data from Salesforce, returns results
    │
    ▼
Agent: Formats and presents the report to user
```

### Security

- Agents use scoped API keys
- All calls are logged in the audit log
- Category-based access control limits what agents can do
- Tools can require specific context (account, user)

---

## Client Apps (External Integration)

For building custom integrations, Adapterly provides a **Client Apps** API.

### What Client Apps Can Do

| Capability | Description |
|------------|-------------|
| Manage accounts | Create and update accounts via external_id |
| Manage workspaces | Organize integrations into isolated spaces |
| Execute operations | Run system operations and get results |
| Create sessions | Generate login tokens for your users |

### API Authentication

Client Apps use Bearer token authentication:

```bash
curl -H "Authorization: Bearer ca_live_abc123..." \
     https://your-instance/api/v1/client/workspaces/
```

### Typical Integration Flow

1. **Create a Client App** in the Adapterly UI
2. **Save the API key** (shown only once)
3. **Configure scopes** (what the app can do)
4. **Integrate** using the REST API

---

## Best Practices

### Integration Design

1. **Keep resources focused** - Each resource should represent one entity
2. **Use meaningful names** - Clear naming helps AI agents understand tools
3. **Handle errors** - Configure retry logic for external calls
4. **Test incrementally** - Verify connections after each change

### Security

1. **Use environment variables** for secrets, never hardcode
2. **Limit scopes** - Give agents only the access they need
3. **Review audit logs** - Monitor for unexpected activity
4. **Rotate keys** periodically

### Performance

1. **Use pagination** - Fetch data in chunks for large datasets
2. **Cache when possible** - Store frequently used reference data
3. **Batch operations** - Update many records in one call when supported

---

## Getting Help

- **Documentation** - You're reading it! Explore other sections.
- **FAQ** - Common questions and answers
- **Troubleshooting** - Solutions to common problems

---

## Next Steps

Now that you understand the basics:

1. **[Core Concepts](/help/en/concepts/)** - Deep dive into systems and integrations
2. **[Guides](/help/en/guides/)** - Step-by-step instructions for specific tasks
3. **[Recipes](/help/en/recipes/)** - Copy-paste examples for common use cases
4. **[MCP & Agents](/help/en/mcp/)** - Learn about AI agent integration
