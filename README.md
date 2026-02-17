# Adapterly

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![CI](https://github.com/samiveikko/adapterly/actions/workflows/ci.yml/badge.svg)](https://github.com/samiveikko/adapterly/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)

AI-powered integration platform for fragmented industries. Connect 40+ pre-built adapters for construction and logistics, map entities across systems, and let AI agents query everything with natural language.

## Features

### Industry Verticals

| Industry | Systems | Entity Types |
|----------|---------|--------------|
| **Construction** | 37 systems | project, site, equipment, drawing, inspection |
| **Logistics** | 8 systems | shipment, carrier, warehouse, order, product |

### Core Capabilities

- **Pre-built Adapters** - 40+ systems ready to connect (Infrakit, Congrid, Procore, Unifaun, Posti, etc.)
- **Entity Mapping** - Link the same entity (project, shipment) across multiple systems with different IDs
- **MCP Gateway** - Native Model Context Protocol support for Claude, ChatGPT, Cursor, and other AI agents
- **Confirmation Status** - Adapters start "unconfirmed" until first successful API call proves they work
- **Industry Templates** - Pre-configured term and field mappings for each vertical
- **Multiple Auth Methods** - OAuth2, API keys, Basic auth, browser session (XHR)
- **GraphQL Support** - Native handling for GraphQL APIs alongside REST

## Architecture

```
AI Agents (Claude, ChatGPT, etc.)
       ↓ (MCP protocol)
┌──────────────────────────────────────┐
│  Adapterly MCP Gateway               │
│  ├── System Tools (auto-generated)   │
│  ├── Entity Resolution               │
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

## Entity Mapping

Map the same real-world entity across multiple systems:

```
"E18 Highway Project"
├── Infrakit: uuid="abc-123"
├── Congrid: project_id="456"
└── Visma: project_code="E18-2026"
```

When AI asks about "E18 Project", Adapterly resolves the correct ID for each system automatically.

### Entity Types

**Construction:**
- project, site, equipment, drawing, inspection, user, company

**Logistics:**
- shipment, carrier, warehouse, order, product, route, vehicle, driver

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

### Entity Tools

- `resolve_entity` - Resolve canonical name to system-specific IDs
- `list_entity_types` - List available entity types
- `list_mappings` - List entity mappings for account

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
      "url": "https://api.adapterly.io/mcp",
      "apiKey": "your-api-key"
    }
  }
}
```

### 2. Connect Systems

1. Go to Systems dashboard
2. Choose from 40+ pre-built adapters
3. Configure OAuth or API key credentials
4. System becomes "confirmed" after first successful call

### 3. Map Entities

1. Go to Entity Mappings
2. Create mapping (e.g., "E18 Project")
3. Add system identifiers for each connected system
4. AI can now query across all systems with one name

### 4. Query with AI

```
User: "Show me all quality issues for E18 project"

AI: Resolving E18 project...
    - Congrid: 12 observations
    - Infrakit: 3 logpoints

    Found 15 total issues across systems.
```

## Industry Systems

### Construction (37 systems)

| System | Type | Country |
|--------|------|---------|
| Infrakit | Project Management | FI |
| Congrid | Quality Management | FI |
| Procore | Project Management | US |
| Sitedrive | Scheduling | FI |
| TAKT.ing | Takt Planning | - |
| Admicom | ERP | FI |
| Tekla | BIM | FI |
| Solibri | BIM Checking | FI |
| ... | | |

### Logistics (8 systems)

| System | Type | Country |
|--------|------|---------|
| Unifaun | Shipping | SE |
| Posti | Carrier | FI |
| DB Schenker | Freight | DE |
| Matkahuolto | Carrier | FI |
| Cargoson | Shipping | EE |
| Consignor | Shipping | NO |
| Logiapps WMS | Warehouse | FI |
| Ongoing WMS | Warehouse | SE |

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
ADAPTER_UPDATE_NOTIFY_EMAILS=["admin@adapterly.io"]
```

Changed adapters can be reviewed at `/admin/systems/pending-refreshes/`.

### Add New Adapter

1. Create migration with System, Interface, Resources, Actions
2. Run migration
3. Connect with credentials
4. First successful call confirms the adapter

### Add New Industry

1. Create IndustryTemplate
2. Add relevant EntityTypes
3. Create TermMappings for each system
4. Create FieldMappings for entity fields

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
