# Adapterly

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![CI](https://github.com/samiveikko/adapterly/actions/workflows/ci.yml/badge.svg)](https://github.com/samiveikko/adapterly/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)

AI-powered integration platform for fragmented industries. Connect 67 pre-built adapters for construction, logistics, and general business tools, and let AI agents query everything through MCP.

## Features

### Industry Verticals

| Industry | Systems | Examples |
|----------|---------|----------|
| **Construction** | 47 systems | Procore, Infrakit, Congrid, Tekla, Dalux, Solibri |
| **Logistics** | 13 systems | DHL, Posti, Bring, nShift, Unifaun, DB Schenker |
| **General** | 7 systems | Slack, Teams, SharePoint, Google Drive, DocuSign |

### Core Capabilities

- **Pre-built Adapters** - 67 systems ready to connect (Infrakit, Congrid, Procore, Unifaun, Posti, etc.)
- **MCP Gateway** - Native Model Context Protocol support for Claude, ChatGPT, Cursor, and other AI agents
- **Confirmation Status** - Adapters start "unconfirmed" until first successful API call proves they work
- **Multiple Auth Methods** - OAuth2, API keys, Basic auth, browser session (XHR)
- **GraphQL Support** - Native handling for GraphQL APIs alongside REST
- **Project Scoping** - Isolate integrations and credentials per project

## Architecture

```
AI Agents (Claude, ChatGPT, etc.)
       ↓ (MCP protocol)
┌──────────────────────────────────────┐
│  Adapterly MCP Gateway               │
│  ├── System Tools (auto-generated)   │
│  ├── Project Scoping                 │
│  └── Audit Logging                   │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│  Adapter Layer                       │
│  ├── REST APIs                       │
│  ├── GraphQL APIs                    │
│  └── Browser Session (XHR)           │
└──────────────────────────────────────┘
       ↓
External Systems (Infrakit, Unifaun, etc.)
```

## System Confirmation Status

All adapters have a confirmation status:

| Status | Meaning |
|--------|---------|
| **Unconfirmed** | Adapter built from API docs, awaiting first real test |
| **Confirmed** | Successfully made API call with real credentials |

Confirmation happens automatically when you connect a system and make your first successful API call.

## MCP Tools

### System Tools (Auto-generated)

Tools are generated automatically from adapter definitions:

```
{system}_{resource}_{action}
```

Examples:
- `infrakit_projects_list` - List Infrakit projects
- `unifaun_shipments_create` - Create shipment in Unifaun
- `congrid_observations_list` - List quality observations

### MCP Modes

| Mode | Description |
|------|-------------|
| **Safe** (default) | Read-only access to all systems |
| **Power** | Full read/write access |

## Quick Start

### 1. Configure Claude Desktop

```json
{
  "mcpServers": {
    "adapterly": {
      "url": "https://api.adapterly.ai/mcp",
      "apiKey": "your-api-key"
    }
  }
}
```

### 2. Connect Systems

1. Go to Systems dashboard
2. Choose from 67 pre-built adapters
3. Configure OAuth or API key credentials
4. System becomes "confirmed" after first successful call

### 3. Query with AI

```
User: "Show me all quality issues for E18 project"

AI: Using Congrid adapter...
    Found 12 observations across 3 categories.
```

## Industry Systems

### Construction (47 systems)

| System | Type | Country |
|--------|------|---------|
| Infrakit | Project Management | FI |
| Congrid | Quality Management | FI |
| Procore | Project Management | US |
| Autodesk ACC | Project Management | US |
| Tekla Structures | BIM | FI |
| Solibri | BIM Checking | FI |
| Dalux | Quality Management | DK |
| Sitedrive | Scheduling | FI |
| Admicom Ultima | ERP | FI |
| Trimble Connect | BIM | US |
| Oracle Primavera P6 | Scheduling | US |
| Bentley Synchro | 4D Scheduling | US |
| SAP | ERP | DE |
| ... and 34 more | | |

### Logistics (13 systems)

| System | Type | Country |
|--------|------|---------|
| DHL | Shipping | DE |
| Posti | Carrier | FI |
| Bring | Carrier | NO |
| nShift | Multi-carrier | SE |
| Unifaun | Shipping | SE |
| DB Schenker | Freight | DE |
| DSV | Freight | DK |
| Matkahuolto | Carrier | FI |
| Cargoson | Shipping | EE |
| Consignor | Shipping | NO |
| Ongoing WMS | Warehouse | SE |
| Kuehne + Nagel | Freight | CH |
| Transporeon | Freight Platform | DE |

### General / Cross-Industry (7 systems)

| System | Type | Country |
|--------|------|---------|
| Microsoft Teams | Collaboration | US |
| Slack | Communication | US |
| Microsoft SharePoint | Storage | US |
| Google Drive | Storage | US |
| Google Sheets | Storage | US |
| Microsoft Power BI | Analytics | US |
| DocuSign | e-Signatures | US |

## Development

### Requirements

- Python 3.10+
- Django 5.2+
- PostgreSQL (or SQLite for dev)
- FastAPI (for MCP server)

### Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Run FastAPI MCP Server

```bash
uvicorn fastapi_app.main:app --reload
```

### Management Commands

```bash
# Check all adapters for OpenAPI spec changes (used as daily cron)
python manage.py check_adapter_updates

# Skip email notification (useful for manual/debug runs)
python manage.py check_adapter_updates --no-notify

# Send a test email to verify SMTP configuration
python manage.py test_email admin@example.com
```

To receive email notifications when spec changes are detected, set the env var:

```bash
ADAPTER_UPDATE_NOTIFY_EMAILS=["admin@adapterly.ai"]
```

Changed adapters can be reviewed at `/admin/systems/pending-refreshes/`.

### Add New Adapter

1. Create YAML adapter definition or migration with System, Interface, Resources, Actions
2. Run migration or `load_adapters`
3. Connect with credentials
4. First successful call confirms the adapter

## API Structure

```
System (e.g., "Infrakit")
├── Interface (e.g., "api" - REST, GraphQL, XHR)
│   ├── Resource (e.g., "projects")
│   │   ├── Action (e.g., "list", "get", "create")
│   │   └── Action (e.g., "update", "delete")
│   └── Resource (e.g., "logpoints")
│       └── Action (...)
└── AccountSystem (per-account credentials)
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means:
- You can use, modify, and distribute this software
- If you modify and deploy it as a service, you must share your modifications under AGPL-3.0
- See [LICENSE](LICENSE) for the full license text

### Why AGPL?

We chose AGPL to ensure transparency and prevent closed-source forks while still allowing the community to use, learn from, and contribute to the codebase
