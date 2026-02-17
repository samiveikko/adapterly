# Recipes

Ready-to-use copy-paste examples for common use cases. All examples follow Adapterly Spec 1.0.

## Sync A → B

Sync data from source to target: list, transform, write.

```yaml
name: Sync Infrakit → Google Sheets
version: "1.0.0"
description: Sync project list from Infrakit to Google Sheets

variables:
  sheet_id: "${env:GOOGLE_SHEET_ID}"

schedule:
  cron: "0 6 * * *"
  timezone: "Europe/Helsinki"

error_handling:
  default_action: fail
  notify_on_fail:
    channel: email
    to: "${env:ALERT_EMAIL}"

steps:
  - id: list_projects
    type: read
    config:
      system: infrakit
      resource: projects
      action: list
      params:
        fetch_all_pages: true
    on_error:
      action: retry
      retry_count: 3
      retry_delay_seconds: 10

  - id: transform_to_rows
    type: transform
    config:
      language: python
      code: |
        rows = [["ID", "Name", "Created", "Status"]]
        for p in projects:
            status = "Archived" if p.get("archived") else "Active"
            rows.append([
                p["uuid"],
                p.get("name", ""),
                p.get("timestamp", ""),
                status
            ])
        return rows
      inputs:
        projects: "${steps.list_projects.output.data}"

  - id: update_sheet
    type: write
    config:
      system: google_sheets
      resource: sheets
      action: update
      params:
        spreadsheetId: "${var:sheet_id}"
        range: "Projects!A1"
        values: "${steps.transform_to_rows.output.data}"
```

---

## Alert When Condition Met

Check on schedule and send alert if condition is true.

```yaml
name: Large Data Alert
version: "1.0.0"
description: Alert if projects exceed 100

schedule:
  cron: "0 8 * * *"
  timezone: "Europe/Helsinki"

steps:
  - id: list_projects
    type: read
    config:
      system: infrakit
      resource: projects
      action: list
      params:
        fetch_all_pages: true

  - id: count_projects
    type: transform
    config:
      language: python
      code: |
        count = len(projects)
        return {"count": count, "should_alert": count > 100}
      inputs:
        projects: "${steps.list_projects.output.data}"

  - id: check_threshold
    type: condition
    config:
      condition: "${steps.count_projects.output.data.should_alert}"
      true_branch: send_alert
      false_branch: skip_alert

  - id: send_alert
    type: notify
    config:
      channel: email
      to: "${env:ALERT_EMAIL}"
      subject: "Alert: ${steps.count_projects.output.data.count} projects"
      body: |
        Project count exceeds threshold of 100.
        Current count: ${steps.count_projects.output.data.count}

  - id: skip_alert
    type: transform
    config:
      language: python
      code: |
        return {"message": "No alert needed", "count": count}
      inputs:
        count: "${steps.count_projects.output.data.count}"
```

---

## Safe Mass Update

Preview changes, get approval, then execute.

```yaml
name: Safe Mass Update
version: "1.0.0"
description: Update projects with user approval

steps:
  - id: list_projects
    type: read
    config:
      system: infrakit
      resource: projects
      action: list
      params:
        fetch_all_pages: true

  - id: filter_outdated
    type: transform
    config:
      language: python
      code: |
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=30)
        outdated = [
            p for p in projects
            if p.get("last_updated") and
               datetime.fromisoformat(p["last_updated"]) < cutoff
        ]
        return outdated
      inputs:
        projects: "${steps.list_projects.output.data}"

  - id: preview_changes
    type: transform
    config:
      language: python
      code: |
        preview = []
        for p in outdated:
            preview.append({
                "id": p["uuid"],
                "name": p.get("name"),
                "action": "Mark as outdated"
            })
        return {
            "count": len(preview),
            "changes": preview[:10],
            "more": len(preview) > 10
        }
      inputs:
        outdated: "${steps.filter_outdated.output.data}"

  - id: confirm_changes
    type: user_input
    config:
      prompt: |
        Updating ${steps.preview_changes.output.data.count} projects.
        Continue?
      options:
        - "Yes, update"
        - "No, cancel"
      timeout_seconds: 3600

  - id: check_confirmation
    type: condition
    config:
      condition: "${steps.confirm_changes.output.data.selected} == 'Yes, update'"
      true_branch: apply_changes
      false_branch: cancelled

  - id: apply_changes
    type: loop
    config:
      items: "${steps.filter_outdated.output.data}"
      concurrency: 5
      steps:
        - id: update_project
          type: write
          config:
            system: infrakit
            resource: projects
            action: update
            params:
              uuid: "${item.uuid}"
              status: "outdated"

  - id: cancelled
    type: transform
    config:
      language: python
      code: |
        return {"status": "cancelled"}
```

---

## Idempotent Upsert

Write safely without duplicates using upsert keys.

```yaml
name: Idempotent Upsert
version: "1.0.0"
description: Create or update items using upsert key

steps:
  - id: get_source_data
    type: read
    config:
      system: source_system
      resource: items
      action: list

  - id: get_existing
    type: read
    config:
      system: target_system
      resource: items
      action: list

  - id: calculate_upserts
    type: transform
    config:
      language: python
      code: |
        existing_map = {item["external_id"]: item for item in existing}

        to_create = []
        to_update = []

        for item in source:
            external_id = item["id"]

            if external_id in existing_map:
                existing = existing_map[external_id]
                if item.get("updated_at") != existing.get("source_updated_at"):
                    to_update.append({
                        "target_id": existing["id"],
                        "data": item
                    })
            else:
                to_create.append({
                    "external_id": external_id,
                    "data": item
                })

        return {
            "to_create": to_create,
            "to_update": to_update,
            "summary": {
                "create_count": len(to_create),
                "update_count": len(to_update)
            }
        }
      inputs:
        source: "${steps.get_source_data.output.data}"
        existing: "${steps.get_existing.output.data}"

  - id: create_new
    type: loop
    config:
      items: "${steps.calculate_upserts.output.data.to_create}"
      concurrency: 10
      steps:
        - id: create_item
          type: write
          config:
            system: target_system
            resource: items
            action: create
            params:
              external_id: "${item.external_id}"
              data: "${item.data}"

  - id: update_existing
    type: loop
    config:
      items: "${steps.calculate_upserts.output.data.to_update}"
      concurrency: 10
      steps:
        - id: update_item
          type: write
          config:
            system: target_system
            resource: items
            action: update
            params:
              id: "${item.target_id}"
              data: "${item.data}"
```

---

## Performance: Batch and Rate Limit

Process large data efficiently while respecting API limits.

```yaml
name: Efficient Mass Sync
version: "1.0.0"
description: Sync thousands of items in batches

variables:
  batch_size: 100
  concurrent_batches: 3
  rate_limit_delay_ms: 200

steps:
  - id: get_all_items
    type: read
    config:
      system: source
      resource: items
      action: list
      params:
        fetch_all_pages: true

  - id: create_batches
    type: transform
    config:
      language: python
      code: |
        batches = []
        for i in range(0, len(items), batch_size):
            batches.append({
                "batch_index": i // batch_size,
                "items": items[i:i + batch_size]
            })
        return batches
      inputs:
        items: "${steps.get_all_items.output.data}"
        batch_size: "${var:batch_size}"

  - id: process_batches
    type: loop
    config:
      items: "${steps.create_batches.output.data}"
      concurrency: "${var:concurrent_batches}"
      rate_limit:
        requests_per_second: 5
      steps:
        - id: process_batch
          type: write
          config:
            system: target
            resource: items
            action: bulk_upsert
            params:
              items: "${batch.items}"

        - id: batch_delay
          type: wait
          config:
            milliseconds: "${var:rate_limit_delay_ms}"
```
