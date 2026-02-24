# Troubleshooting

Common errors and their solutions.

## Common Errors

### "Tool not found"

**Cause:** MCP tool not registered or no permissions.

**Fix:**
1. Check that system is configured in Adapterly
2. Verify interface has resources and actions
3. Check API token has permissions
4. Restart Claude Desktop

### "Authentication failed"

**Cause:** Credentials are invalid, expired, or missing.

**Fix:**
1. Go to **Systems** → select system → **Configure**
2. Check/update credentials:
   - OAuth: username and password
   - API Key: key and header name
   - Bearer: token value
3. Click **Test Connection**

### "Timeout"

**Cause:** External API not responding in time.

**Fix:**
1. Check target API status
2. Try smaller request (reduce `pageSize`, remove `fetch_all_pages`)
3. Check network connectivity
4. Increase timeout:
   ```yaml
   - id: slow_request
     type: read
     config:
       timeout_seconds: 120
   ```

### "YAML syntax error"

**Cause:** Formatting error in YAML definition.

**Common issues:**

1. **Wrong indentation:**
   ```yaml
   # Wrong
   steps:
     - id: step1
       config:
        system: foo  # <- 1 space short

   # Correct
   steps:
     - id: step1
       config:
         system: foo
   ```

2. **Tabs vs spaces:**
   ```yaml
   # Wrong - tab character
   steps:
   	- id: step1

   # Correct - 2 spaces
   steps:
     - id: step1
   ```

3. **Missing quotes:**
   ```yaml
   # Wrong
   description: This is: a problem

   # Correct
   description: "This is: ok"
   ```

**Fix:** Use YAML validator, ensure consistent 2-space indentation.

### "Variable not found"

**Cause:** Reference to non-existent variable or path.

**Fix:**
1. Check variable spelling:
   ```yaml
   # Wrong
   "${step.output.data}"

   # Correct
   "${steps.step1.output.data}"
   ```

2. Verify referenced step has executed
3. Check path exists in output

### "Rate limit exceeded"

**Cause:** Too many requests in short time.

**Fix:**
1. Add delays between requests
2. Reduce concurrency
3. Use batch processing

### "No interface configured"

**Cause:** System has no API interfaces.

**Fix:** Use Adapter Wizard to add interface (OpenAPI, HAR, or manual).

---

## Debugging Checklist

### 1. Check Execution Details

1. Go to **Executions** → select failed execution
2. Check **Steps** list for error location
3. Open failed step details

### 2. Examine Inputs and Outputs

Each step shows:
- **Input**: What was given to step
- **Output**: What step returned
- **Error**: Error message (if failed)

### 3. Check Context

Context tab shows:
- All variable values at execution time
- Accumulated step outputs
- Environment variables (redacted)

### 4. Find Request ID

Each API call gets unique `request_id`:
```
request_id: run_123_step_456_req_789
```

Use for tracing in external API logs.

### 5. Test Step Separately

1. Open the configuration
2. Click on failing step
3. Click **Test this step**
4. Provide sample input data
5. Review output

---

## Error Code Reference

### HTTP Errors

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad request | Check parameters |
| 401 | Unauthorized | Update credentials |
| 403 | Forbidden | Check permissions |
| 404 | Not found | Check resource ID/path |
| 429 | Rate limit | Wait and retry |
| 500 | Server error | Retry later |
| 502/503 | Service unavailable | Check API status |
| 504 | Gateway timeout | Increase timeout |

### Adapterly Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `StepNotFound` | Referenced step doesn't exist | Check step ID |
| `CircularDependency` | Steps reference each other in cycle | Fix step chain |
| `InvalidTemplate` | Template syntax error | Check ${...} references |
| `TransformError` | Python code error | Debug code separately |
| `PaginationLimit` | Safety limit exceeded | Use filters or batching |

---

## Log Locations

### Adapterly

| Log | Location |
|-----|----------|
| Execution logs | UI: Executions → select execution |
| MCP calls | UI: Executions → MCP calls |
| System logs | API: `GET /api/logs/` |

### Claude Desktop

| OS | Path |
|----|------|
| Linux | `~/.config/claude/logs/` |
| macOS | `~/Library/Logs/Claude/` |
| Windows | `%APPDATA%\claude\logs\` |

---

## Contact Support

If issue persists:

1. Gather information:
   - Execution ID or request ID
   - Complete error message
   - What you tried to do
   - When issue started

2. Contact:
   - In-app support
   - Email: support@adapterly.ai
