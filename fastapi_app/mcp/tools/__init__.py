"""
MCP Tools module.

Provides tool definitions for the MCP server.
Adapterly focuses on being an MCP Tool Gateway - system connections,
permissions, audit logging, and project mapping.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .datasets import get_dataset_tools
from .diagnostics import get_diagnostic_tools
from .entity import get_entity_tools
from .management import get_management_tools
from .systems import execute_system_tool, get_system_tools

logger = logging.getLogger(__name__)


async def get_all_tools(
    account_id: int, db: AsyncSession | None = None, project_id: int | None = None
) -> list[dict[str, Any]]:
    """
    Get all available tools for an account.

    This combines:
    - Context tools (session management)
    - Management tools (system/project management)
    - System tools (from configured integrations)

    Args:
        account_id: Account ID
        db: Database session
        project_id: Optional project ID for scoping system tools

    Returns:
        List of tool definitions
    """
    tools = []

    # Add built-in context tools
    tools.extend(get_builtin_tools())

    # Add management tools
    tools.extend(get_management_tools())

    # Add entity mapping tools
    tools.extend(get_entity_tools())

    # Add diagnostic tools
    tools.extend(get_diagnostic_tools())

    # Add dataset tools (for working with cached large results)
    tools.extend(get_dataset_tools())

    # Add system tools from database
    if db:
        try:
            system_tools = await get_system_tools(db, account_id, project_id=project_id)
            for tool_def in system_tools:
                # Create handler closure for this tool
                action_id = tool_def["action_id"]
                handler = create_system_tool_handler(action_id)
                tool_def["handler"] = handler
                tools.append(tool_def)
            logger.info(f"Loaded {len(system_tools)} system tools for account {account_id}")
        except Exception as e:
            logger.warning(f"Error loading system tools: {e}")

    return tools


def create_system_tool_handler(action_id: int):
    """Create a handler function for a system tool."""

    async def handler(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
        db = ctx.get("db")
        account_id = ctx.get("account_id")
        project_id = ctx.get("project_id")

        if not db:
            return {"error": "Database session not available"}

        return await execute_system_tool(db, action_id, account_id, kwargs, project_id=project_id)

    return handler


def get_builtin_tools() -> list[dict[str, Any]]:
    """Get built-in tool definitions (context tools only)."""
    return [
        {
            "name": "set_context",
            "description": "Set the execution context (account, project)",
            "tool_type": "context",
            "input_schema": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "integer", "description": "Account ID"},
                    "project_id": {"type": "integer", "description": "Project ID for scoping"},
                },
            },
            "handler": handle_set_context,
        },
        {
            "name": "get_context",
            "description": "Get the current execution context",
            "tool_type": "context",
            "input_schema": {"type": "object", "properties": {}},
            "handler": handle_get_context,
        },
    ]


# Tool handlers


async def handle_set_context(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Handle set_context tool."""
    return {"status": "ok", "context": kwargs}


async def handle_get_context(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Handle get_context tool."""
    project = ctx.get("project")

    result = {
        "account_id": ctx.get("account_id"),
        "user_id": ctx.get("user_id"),
        "session_id": ctx.get("session_id"),
        "project_id": ctx.get("project_id"),
    }

    # Include project details if available
    if project:
        result["project"] = {
            "name": project.name,
            "slug": project.slug,
            "description": project.description or "",
        }

    return result
