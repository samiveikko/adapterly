# YAML Reference

Official Adapterly configuration reference documentation.

## Step Types

### read

Reads data from external system.

```yaml
- id: list_items
  type: read
  config:
    system: string              # System name
    resource: string            # Resource name
    action: string              # Action name
    params:
      fetch_all_pages: boolean
      page: integer
      pageSize: integer
```

**Output:**
```yaml
output:
  data: [...]
  meta:
    count: integer
    pages: integer
    duration_ms: integer
    request_id: string
```

### write

Writes data to external system.

```yaml
- id: create_item
  type: write
  config:
    system: string
    resource: string
    action: string              # create, update, delete, bulk_upsert
    params: {...}
```

### transform

Transforms data with Python code.

```yaml
- id: process_data
  type: transform
  config:
    language: python
    code: |
      result = []
      for item in input_data:
          result.append(transform(item))
      return result
    inputs:
      input_data: "${steps.previous.output.data}"
```

### condition

Branches based on condition.

```yaml
- id: check_condition
  type: condition
  config:
    condition: "${steps.count.output.data.value} > 100"
    true_branch: handle_large
    false_branch: handle_small
```

### loop

Iterates over collection.

```yaml
- id: process_items
  type: loop
  config:
    items: "${steps.list.output.data}"
    concurrency: integer
    steps:
      - id: process_one
        type: write
        config: {...}
```

### switch

Multiple condition branches.

```yaml
- id: route_by_type
  type: switch
  config:
    value: "${steps.get_item.output.data.type}"
    cases:
      "typeA": handle_a
      "typeB": handle_b
    default: handle_other
```

### wait

Waits for specified time.

```yaml
- id: delay
  type: wait
  config:
    seconds: integer            # OR
    milliseconds: integer
```

### notify

Sends notification.

```yaml
- id: send_alert
  type: notify
  config:
    channel: string             # email, slack, webhook
    to: string
    subject: string
    body: string
```

### user_input

Requests user input.

```yaml
- id: get_approval
  type: user_input
  config:
    prompt: string
    options:
      - "Approve"
      - "Reject"
    timeout_seconds: integer
```

---

## Template Language

### Variable Types

| Syntax | Description | Example |
|--------|-------------|---------|
| `${var:name}` | Variable | `${var:sheet_id}` |
| `${env:NAME}` | Environment variable | `${env:API_KEY}` |
| `${env:NAME:default}` | With default | `${env:TIMEOUT:30}` |
| `${steps.id.output.data}` | Step output | `${steps.list.output.data}` |

### Path Operations

```yaml
# Full data
"${steps.list.output.data}"

# Specific index
"${steps.list.output.data[0]}"

# Specific field
"${steps.list.output.data[0].name}"

# Nested path
"${steps.get.output.data.user.profile.email}"
```

---

## Error Handling

### Step-level on_error

```yaml
- id: risky_step
  type: read
  config: {...}
  on_error:
    action: retry
    retry_count: 3
    retry_delay_seconds: 5
    retry_backoff: exponential
```

### Global error_handling

```yaml
error_handling:
  default_action: fail
  notify_on_fail:
    channel: email
    to: "${env:ALERT_EMAIL}"
```

### Priority Order

1. Step-level `on_error` if defined
2. Global `error_handling.default_action` if defined
3. Default: `fail`

---

## Schedule

### Cron Syntax

```yaml
schedule:
  cron: "minute hour day month weekday"
  timezone: "Europe/Helsinki"
```

### Examples

```yaml
# Every hour
cron: "0 * * * *"

# Daily at 9 AM
cron: "0 9 * * *"

# Weekdays at 9 AM
cron: "0 9 * * MON-FRI"

# Every 15 minutes
cron: "*/15 * * * *"
```

---

## API Reference

### Authentication

```bash
Authorization: Token your-api-token
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/systems/` | List systems |
| GET | `/api/systems/{id}/` | Get system details |
| POST | `/api/systems/{id}/test/` | Test system connection |
