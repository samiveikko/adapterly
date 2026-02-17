# Frequently Asked Questions

## General

### What is Adapterly?
Adapterly is an AI-powered integration platform. It connects to your external systems (APIs, databases, SaaS apps) and automates data flows between them. It also integrates with Claude AI for intelligent automation.

### Who is Adapterly for?
- Business analysts who need to automate data processes
- Developers who want to quickly connect APIs
- Teams managing data across multiple platforms
- Anyone who needs to automate repetitive tasks

### Do I need to know how to code?
No. Adapterly provides:
- Pre-built system adapters
- Adapter Wizard for auto-configuration
- MCP integration for AI-powered automation

For advanced transformations, you can write Python code in function steps.

## Systems

### How do I connect a new system?
1. Go to **Systems** → **Create New**
2. Use the **Adapter Wizard** to auto-discover endpoints from:
   - OpenAPI/Swagger specification
   - HAR file (recorded API calls)
   - Manual configuration

### What authentication methods are supported?
- OAuth 2.0 (password grant)
- API Key
- Bearer Token
- Basic Authentication
- Session/Cookie (for web apps)

### Why does my connection test fail?
Common causes:
- Incorrect credentials
- API endpoint is down
- Network/firewall restrictions
- Rate limiting

Check the error message for specific details.

### Can I connect to internal/private APIs?
Yes, as long as Adapterly can reach the API endpoint. For on-premise systems, you may need to configure network access.

## Entity Mappings

### What are Entity Mappings?
Entity mappings link the same logical entity across different systems. For example, if "ACME Corp" is project "ACME" in Jira and account "001ABC" in Salesforce, you can create a mapping to track this relationship.

Manage mappings at **Systems** → **Entity Mappings**.

## MCP & AI

### What is MCP?
Model Context Protocol (MCP) is a standard for AI assistants to use external tools. Adapterly acts as an MCP server, giving Claude AI access to your connected systems.

### How does Claude use Adapterly?
When you ask Claude to work with your data, it can:
1. List available tools from Adapterly
2. Call tools to read/write data
3. Present results conversationally

### Is my data safe with AI access?
- All MCP calls use your authenticated session
- Actions are limited to your permissions
- Every tool call is logged
- You can revoke API tokens anytime

### What can Claude do vs. what requires manual setup?
Claude can:
- Read data from configured systems
- Create/update data where permitted
- Check task status

Claude cannot:
- Configure new systems
- Modify system credentials
- Access systems without configured credentials

## Troubleshooting

### "No interface configured"
The system doesn't have any API endpoints defined. Use the Adapter Wizard to add them.

### "Authentication failed"
- Check credentials in System → Configure
- For OAuth, verify username/password
- Regenerate API tokens if needed

### "Connection timeout"
- External API may be slow or down
- Check your network connectivity
- Review rate limit status

### "Rate limit exceeded"
- Too many requests in a short time
- Wait before retrying
- Consider batching operations

### "Variable not found"
- Check variable spelling
- Ensure the referenced step has run
- Verify the output path exists

### "Invalid YAML syntax"
- Check indentation (use spaces, not tabs)
- Verify all quotes are matched
- Use a YAML validator

## Account & Billing

### How do I add team members?
Go to **Account Settings** → **Invite User** and enter their email address.

### What permissions can team members have?
- **Admin** - Full access including system configuration
- **User** - Can manage integrations and view executions

### How do I change my password?
Go to **Profile** → **Change Password**.

## Getting Help

### Where can I report bugs?
Contact support through the application or email.

### Is there a status page?
System status and maintenance notices are posted in the application.

### Can I request new features?
Yes! We love feedback. Submit feature requests through the support channel.
