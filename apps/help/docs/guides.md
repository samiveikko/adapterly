# Guides

Step-by-step instructions for common tasks.

## Adding a New System

### Method 1: OpenAPI/Swagger Spec (Recommended)

1. Go to **Systems** → **Create New**
2. Select **Adapter Wizard** → **OpenAPI**
3. Paste URL to API's OpenAPI spec (e.g., `https://api.example.com/openapi.json`)
4. Adapterly discovers all endpoints automatically
5. Select resources and actions to import
6. Save

### Method 2: HAR File

Record API calls from browser:

1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Perform desired API operations on the website
4. Right-click → **Save all as HAR**
5. In Adapter Wizard, select **HAR file** and upload
6. Adapterly analyzes calls and creates resources

### Method 3: Manual Configuration

1. Go to **Systems** → **Create New**
2. Enter name and description
3. Add interface:
   - Base URL (e.g., `https://api.example.com/v1`)
   - Authentication type
4. Add resources and actions one by one
5. Define parameters in JSON Schema format

---

## Authentication

### API Key

Simplest method. API key sent with each request.

```yaml
auth:
  type: api_key
  header: X-API-Key
  value: "${env:API_KEY}"
```

### Bearer Token

Pre-generated access token.

```yaml
auth:
  type: bearer
  token: "${env:ACCESS_TOKEN}"
```

### OAuth 2.0 Password Grant

Username and password exchanged for token.

```yaml
auth:
  type: oauth2_password
  token_url: "https://api.example.com/oauth/token"
  username: "${env:API_USERNAME}"
  password: "${env:API_PASSWORD}"
```

Adapterly automatically obtains, caches, and refreshes tokens.

### Basic Authentication

Username and password Base64-encoded.

```yaml
auth:
  type: basic
  username: "${env:API_USERNAME}"
  password: "${env:API_PASSWORD}"
```

---

## Testing Connections

### Connection Test

Verify system connectivity:

1. Go to **Systems** → select your system → **Configure**
2. Enter credentials
3. Click **Test Connection**
4. Green checkmark = success

### Verifying Resources

Test that resources are properly configured:

1. Go to **Systems** → select your system
2. Browse available resources and actions
3. Use the MCP tools to test data retrieval
