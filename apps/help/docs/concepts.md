# Core Concepts

This page covers Adapterly's core concepts in depth.

## Systems

A system represents an external service that Adapterly connects to. The hierarchy is:

```
System
  └── Interface (API endpoint)
        └── Resource (data entity)
              └── Action (operation)
```

**Example:**
```
Infrakit
  └── Kuura API
        └── projects
              ├── list
              ├── get
              └── create
```

### Interface

An interface defines the API basics:
- **Base URL** - API root address
- **Authentication** - How to authenticate
- **Rate limit** - Request limits

### Resource

A resource is an API data entity, such as `projects`, `users`, or `orders`.

### Action

An action is an operation on a resource:
- `list` - List all
- `get` - Get single
- `create` - Create new
- `update` - Update
- `delete` - Delete

---

## Entity Mappings

Entity mappings allow linking the same logical entity across multiple systems. This is essential for cross-system integrations.

### Structure

```
EntityType (e.g., "company", "project", "user")
  └── EntityMapping (e.g., "ACME Corporation")
        ├── SystemEntityIdentifier (jira: "ACME")
        ├── SystemEntityIdentifier (salesforce: "001ABC")
        └── SystemEntityIdentifier (github: "acme-corp")
```

### Entity Types

| Type | Description |
|------|-------------|
| `project` | Project entity across systems |
| `user` | User/person entity |
| `company` | Company/organization |
| `repository` | Code repository |
| `ticket` | Issue/ticket |
| `contact` | CRM contact |
| `deal` | CRM opportunity/deal |

### Usage Example

```yaml
- id: resolve
  type: resolve_mapping
  config:
    canonical_name: "ACME Corporation"
    entity_type: "company"

- id: use_jira_id
  type: read_data
  config:
    system: jira
    params:
      project: "${resolve.identifiers.jira.id}"
```

---

## Variables and Templating

### Variable Types

| Syntax | Description | Example |
|--------|-------------|---------|
| `${var:name}` | Variable | `${var:sheet_id}` |
| `${env:NAME}` | Environment variable | `${env:API_KEY}` |
| `${env:NAME:default}` | Environment variable with default | `${env:TIMEOUT:30}` |
| `${steps.id.output.data}` | Step output | `${steps.list_projects.output.data}` |

### Standard Output

Each step returns a consistent format:

```yaml
output:
  data: [...]       # Actual payload
  meta:             # Metadata
    count: 150
    pages: 3
    duration_ms: 1250
    request_id: "abc123"
```

---

## Error Handling

### Priority Order

1. **Step-level `on_error`** - If defined
2. **Global `error_handling.default_action`** - If defined
3. **Default: `fail`** - Stop execution

### Step-level Error Handling

```yaml
- id: risky_step
  type: read
  config: {...}
  on_error:
    action: retry          # retry, continue, fail
    retry_count: 3
    retry_delay_seconds: 5
```

### Actions

| Action | Description |
|--------|-------------|
| `fail` | Stop execution immediately |
| `continue` | Skip error and continue to next step |
| `retry` | Retry (retry_count, retry_delay_seconds) |

---

## Pagination and Batch Processing

### Automatic Pagination

Add `fetch_all_pages: true` to fetch all pages automatically:

```yaml
- id: list_all
  type: read
  config:
    system: infrakit
    resource: projects
    action: list
    params:
      fetch_all_pages: true
```

### Safety Limits

- Maximum 100 pages
- Maximum 10,000 items
- 2-minute timeout
- Stops on empty or duplicate pages

---

## Permissions and Roles

### User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: systems, integrations, user management |
| **User** | Create and manage integrations, view executions |
| **Viewer** | Read-only: view systems and executions |

### API Tokens

- Token inherits permissions of the user who created it
- Use separate service accounts for automation
- Tokens can be revoked at any time

---

## Auditing and Logs

### What is Logged

- All task executions
- Inputs and outputs for each step
- API calls to external systems
- MCP tool calls
- User actions (login, changes)

### Retention

- Execution history retained for 90 days by default
- Export execution logs as JSON for archiving
- Critical logs (errors, auth) retained longer

### Request ID

Each API call gets a unique `request_id` for tracing:

```yaml
output:
  meta:
    request_id: "run_123_step_456_req_789"
```
