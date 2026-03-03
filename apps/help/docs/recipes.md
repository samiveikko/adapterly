# Recipes

Ready-to-use MCP usage examples and AI conversation patterns.

## Listing and Filtering Data

### List All Projects

```
User: "Show me all my Infrakit projects"

AI calls: infrakit_projects_list()

AI: "Here are your projects:
    1. Highway 101 Extension (active)
    2. Bridge Renovation Phase 2 (active)
    3. Commercial Center Foundation (archived)"
```

### Filter by Criteria

```
User: "Show me only active Congrid projects created this year"

AI calls: congrid_projects_list()
AI: [filters results by date and status]

AI: "Found 3 active projects created in 2026:
    1. E18 Bridge Section (started Jan 15)
    2. Metro Station Renovation (started Feb 3)
    3. Harbor Expansion Phase 1 (started Mar 1)"
```

---

## Cross-System Queries

### Combine Data from Multiple Systems

```
User: "Compare the project list from Infrakit with quality observations from Congrid"

AI calls: infrakit_projects_list()
AI calls: congrid_observations_list(project_id="...")

AI: "Here's a summary:
    - Highway 101: 5 open observations (2 critical)
    - Bridge Phase 2: 12 observations (all resolved)
    - Commercial Center: 3 open observations"
```

### Check Shipment Status Across Carriers

```
User: "Check the status of our recent shipments across all carriers"

AI calls: posti_shipments_list(status="in_transit")
AI calls: dhl_shipments_list(status="in_transit")

AI: "Active shipments:
    Posti: 3 packages in transit
    DHL: 1 package in transit, arriving tomorrow"
```

---

## Creating and Updating Records

### Create a New Record

```
User: "Create a new logpoint in the Highway 101 project at coordinates 60.17, 24.94"

AI calls: infrakit_logpoints_create(
    project_uuid="abc-123",
    coordinates=[60.17, 24.94],
    description="New survey point"
)

AI: "Created logpoint at 60.17, 24.94 in Highway 101.
    ID: lp-456-789"
```

### Update Existing Data

```
User: "Update the description of observation OBS-123 in Congrid to 'Resolved - crack sealed'"

AI calls: congrid_observations_update(
    id="OBS-123",
    description="Resolved - crack sealed"
)

AI: "Updated observation OBS-123 with new description."
```

> **Note:** Create and update operations require **Power mode** on your API key.

---

## Using Safe vs Power Mode

### Safe Mode (Read-Only)

Safe mode is the default. Agents can only read data:

```
User: "List all quality observations"
AI calls: congrid_observations_list()  ← Allowed

User: "Create a new observation"
AI calls: congrid_observations_create(...)  ← Blocked
AI: "I can't create observations - my API key is in Safe mode.
    Ask your admin to switch to Power mode if you need write access."
```

### Power Mode (Full Access)

Power mode enables both read and write operations:

```
User: "Create a shipment in Unifaun"
AI calls: unifaun_shipments_create(
    sender={...},
    receiver={...},
    packages=[{weight: 5.2, dimensions: "30x20x15"}]
)

AI: "Shipment created successfully. Tracking number: UF-2026-12345"
```

---

## Project-Scoped Access

### Working Within a Project

When your API key is bound to a project, only that project's systems are available:

```
User: "What tools do you have?"

AI: "I have access to tools for the E18 Highway project:
    - infrakit_projects_list, infrakit_projects_get
    - congrid_observations_list, congrid_observations_get
    - google_sheets_sheets_update"
```

### Listing Available Systems

```
User: "Which systems can I query?"

AI: "Based on my API key, I can access:
    1. Infrakit (Construction) - projects, logpoints, machines
    2. Congrid (Quality) - observations, inspections
    3. Google Sheets - spreadsheet data"
```

---

## Pagination and Large Datasets

### Fetching All Pages

```
User: "Get all logpoints from the project - there might be thousands"

AI calls: infrakit_logpoints_list(
    project_uuid="abc-123",
    fetch_all_pages=true
)

AI: "Retrieved 2,847 logpoints across 29 pages.
    Here's a summary by type:
    - Survey points: 1,200
    - Machine positions: 1,647"
```

### Safety Limits

Automatic pagination has built-in safety limits:
- Maximum 100 pages per request
- Maximum 10,000 items
- 2-minute timeout
- Stops on empty or duplicate pages

---

## Audit and Monitoring

### Checking Recent Activity

```
User: "What API calls were made in the last hour?"

[Admin checks MCP Gateway → Audit Log in the UI]

Recent calls:
- infrakit_projects_list (safe) - 200 OK - 12:05
- congrid_observations_list (safe) - 200 OK - 12:08
- unifaun_shipments_create (power) - 201 Created - 12:15
```
