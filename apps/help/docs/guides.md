# Guides

Step-by-step instructions for common tasks.

## Adding a New System via YAML Adapter

Systems are defined as YAML adapter files in `adapters/<industry>/<system>.yaml`.

### Adapter YAML Structure

```yaml
system:
  name: "My System"
  alias: "my_system"
  industry: "general"
  website: "https://example.com"

interfaces:
  - name: "REST API"
    alias: "api"
    base_url: "https://api.example.com/v1"
    auth_type: "api_key"
    resources:
      - name: "Projects"
        alias: "projects"
        actions:
          - name: "List Projects"
            alias: "list"
            method: "GET"
            path: "/projects"
            is_mcp_enabled: true
            mcp_mode: "safe"
          - name: "Create Project"
            alias: "create"
            method: "POST"
            path: "/projects"
            is_mcp_enabled: true
            mcp_mode: "power"
```

### Steps

1. Create the YAML file in the appropriate industry folder
2. Run `python manage.py load_adapters` to import
3. The system and its tools will be available immediately
4. Connect credentials and make a test call to confirm

---

## Configuring Credentials

Each system requires credentials configured per account.

### API Key Authentication

1. Go to **Systems** → select system → **Configure**
2. Select auth type: **API Key**
3. Enter:
   - **Header name** (e.g., `X-API-Key`, `Authorization`)
   - **Key value**
4. Click **Test Connection**

### Bearer Token Authentication

1. Select auth type: **Bearer Token**
2. Enter your pre-generated access token
3. Click **Test Connection**

### OAuth 2.0

1. Select auth type: **OAuth 2.0**
2. Enter:
   - **Token URL** (e.g., `https://api.example.com/oauth/token`)
   - **Username** / **Client ID**
   - **Password** / **Client Secret**
3. Adapterly automatically obtains, caches, and refreshes tokens
4. Click **Test Connection**

### DRF Token Authentication

1. Select auth type: **DRF Token**
2. Enter **username** and **password**
3. Adapterly obtains and caches the token automatically

### Basic Authentication

1. Select auth type: **Basic**
2. Enter **username** and **password**
3. Credentials are Base64-encoded automatically

---

## Setting Up a Project

Projects scope which systems and tools are available to AI agents.

### Creating a Project

1. Go to **Projects** → **Create New**
2. Enter project name and optional description
3. Save the project

### Adding Integrations

1. Open the project
2. Click **Add Integration**
3. Select the system to include
4. Repeat for each system this project needs

### Restricting Tool Categories

1. Open the project settings
2. Under **Allowed Categories**, select which categories are permitted
3. Tools outside these categories will be blocked for this project

---

## Creating and Managing API Keys

### Create an API Key

1. Go to **MCP Gateway** → **API Keys**
2. Click **Create API Key**
3. Configure:
   - **Name** - Descriptive name (e.g., "Claude - E18 Project")
   - **Mode** - Safe (read-only) or Power (read/write)
   - **Project** (optional) - Bind to a specific project
   - **Agent Profile** (optional) - Apply a permission profile
4. Copy the key (`ak_live_xxx`) - shown only once

### Manage Keys

- **Revoke**: Immediately disables the key
- **Rotate**: Create a new key and revoke the old one
- Keys are visible in MCP Gateway → API Keys

---

## Deploying a Standalone Gateway

For on-premise or edge deployments, run Adapterly as a standalone Docker gateway.

### Prerequisites

- Docker and Docker Compose installed
- Network access to the control plane (adapterly.ai) for initial sync

### Setup

1. Clone the gateway package:
   ```bash
   cd /opt/adapterly/adapterly-gateway
   docker compose up -d
   ```

2. Open the Setup Wizard at `http://your-host:8080/setup/`

3. Register with the control plane:
   - Enter your control plane URL
   - Authenticate with your account credentials
   - The gateway syncs adapter specs and API keys

4. Configure credentials:
   - Enter system credentials directly in the gateway admin UI
   - Credentials never leave the gateway

5. Point AI agents to the gateway's MCP endpoint:
   ```
   http://your-host:8080/mcp/v1/
   ```

---

## Testing Connections

### Connection Test

1. Go to **Systems** → select your system → **Configure**
2. Enter credentials
3. Click **Test Connection**
4. Green checkmark = success, system becomes "confirmed"

### Testing via MCP

1. Connect an AI agent with your API key
2. Ask: "List all tools" or "List projects from [system]"
3. Verify data is returned correctly
