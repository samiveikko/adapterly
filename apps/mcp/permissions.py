"""
MCP Permission system with Safe/Power mode support and category-based access control.
"""

from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from apps.mcp.categories import ToolCategoryResolver

if TYPE_CHECKING:
    from apps.mcp.models import AgentProfile

logger = logging.getLogger(__name__)


@dataclass
class PermissionResult:
    """Result of a permission check."""

    allowed: bool
    reason: str = ""


class MCPPermissionChecker:
    """
    Permission checker for MCP tool calls.

    Supports two modes:
    - Safe Mode: Only read operations allowed
    - Power Mode: All operations allowed based on tool-specific permissions

    Also supports category-based access control via ToolCategoryResolver or AgentProfile.
    """

    def __init__(
        self,
        account_id: int,
        mode: str = "safe",
        allowed_tools: list | None = None,
        blocked_tools: list | None = None,
        api_key_id: int | None = None,
        project_identifier: str | None = None,
        user_id: int | None = None,
        profile: AgentProfile | None = None,
        allowed_categories: list | None = None,
    ):
        """
        Initialize permission checker.

        Args:
            account_id: The account ID to check permissions for
            mode: Either "safe" or "power"
            allowed_tools: List of allowed tool patterns (fnmatch)
            blocked_tools: List of blocked tool patterns (fnmatch)
            api_key_id: Optional API key ID for category resolution
            project_identifier: Optional project identifier for category resolution
            user_id: Optional user ID for category resolution
            profile: Optional AgentProfile for profile-based access control
            allowed_categories: Optional list of category keys to test (overrides policy lookup)
        """
        self.account_id = account_id
        self.mode = mode.lower()
        self.allowed_tools = allowed_tools or []
        self.blocked_tools = blocked_tools or []
        self.profile = profile
        self.allowed_categories = allowed_categories  # For testing unsaved form values

        # Initialize category resolver
        self.category_resolver = ToolCategoryResolver(
            account_id=account_id, api_key_id=api_key_id, project_identifier=project_identifier, user_id=user_id
        )

        if self.mode not in ("safe", "power"):
            raise ValueError(f"Invalid mode: {mode}. Must be 'safe' or 'power'")

    def can_call_tool(self, tool_name: str, tool_type: str) -> PermissionResult:
        """
        Check if a tool call is allowed.

        Args:
            tool_name: Name of the tool (e.g., "salesforce_contact_create")
            tool_type: Type of tool - one of:
                - "system_read": System read operations
                - "system_write": System write operations
                - "resource": Resource access (read-only)
                - "context": Context management tools

        Returns:
            PermissionResult with allowed status and reason
        """
        # Check blocked tools first (from profile or direct)
        if self._matches_patterns(tool_name, self.blocked_tools):
            return PermissionResult(allowed=False, reason=f"Tool '{tool_name}' is explicitly blocked")

        # Check profile-based restrictions (if profile exists)
        if self.profile:
            # Get tool's categories
            tool_categories = self.category_resolver.get_tool_categories(tool_name)
            if not self.profile.is_tool_allowed(tool_name, tool_categories):
                return PermissionResult(
                    allowed=False, reason=f"Tool '{tool_name}' not allowed by profile '{self.profile.name}'"
                )
        elif self.allowed_categories is not None:
            # Test mode: use provided categories directly
            if len(self.allowed_categories) > 0:
                tool_categories = self.category_resolver.get_tool_categories(tool_name)
                if not tool_categories:
                    return PermissionResult(allowed=False, reason=f"Tool '{tool_name}' has no category assigned")
                if not any(cat in self.allowed_categories for cat in tool_categories):
                    return PermissionResult(
                        allowed=False,
                        reason=f"Tool '{tool_name}' not in allowed categories ({', '.join(self.allowed_categories)})",
                    )
            # If allowed_categories is empty list, all tools are allowed (no category restriction)
        else:
            # Legacy: Check category-based restrictions via category resolver
            if not self.category_resolver.is_tool_allowed(tool_name):
                return PermissionResult(allowed=False, reason=f"Tool '{tool_name}' not in allowed categories")

        # Resource access (read-only) is always allowed
        if tool_type == "resource":
            return PermissionResult(allowed=True)

        # System read operations are always allowed
        if tool_type == "system_read":
            return PermissionResult(allowed=True)

        # System write operations depend on mode
        if tool_type == "system_write":
            if self.mode == "safe":
                return PermissionResult(allowed=False, reason="Write operations require Power Mode in Safe Mode")
            else:
                # Power mode - check specific permissions
                return self._check_tool_permission(tool_name)

        # Unknown tool type - deny by default
        return PermissionResult(allowed=False, reason=f"Unknown tool type: {tool_type}")

    def _check_tool_permission(self, tool_name: str) -> PermissionResult:
        """
        Check tool-specific permissions in Power Mode.
        """
        # If allowed_tools is empty, all non-blocked tools are allowed
        if not self.allowed_tools:
            return PermissionResult(allowed=True)

        # Check if tool matches any allowed pattern
        if self._matches_patterns(tool_name, self.allowed_tools):
            return PermissionResult(allowed=True)

        return PermissionResult(allowed=False, reason=f"Tool '{tool_name}' not in allowed list")

    def _matches_patterns(self, tool_name: str, patterns: list) -> bool:
        """Check if tool name matches any pattern."""
        for pattern in patterns:
            if fnmatch.fnmatch(tool_name, pattern):
                return True
        return False

    def get_tool_list_filter(self) -> dict:
        """
        Get filter for listing available tools.

        Returns dict with:
            - include_write: Whether to include write tools
            - allowed_patterns: Patterns to include
            - blocked_patterns: Patterns to exclude
            - category_resolver: ToolCategoryResolver for category filtering
        """
        return {
            "include_write": self.mode == "power",
            "allowed_patterns": self.allowed_tools,
            "blocked_patterns": self.blocked_tools,
            "category_resolver": self.category_resolver,
        }


def get_permission_checker(
    account_id: int,
    api_key: str | None = None,
    mode: str | None = None,
    project_identifier: str | None = None,
    user_id: int | None = None,
) -> MCPPermissionChecker:
    """
    Factory function to create a permission checker.

    Args:
        account_id: Account ID
        api_key: Optional API key to load permissions from
        mode: Override mode (if not specified, uses API key's mode or 'safe')
        project_identifier: Optional project identifier for category resolution
        user_id: Optional user ID for category resolution

    Returns:
        Configured MCPPermissionChecker
    """
    from apps.mcp.models import MCPApiKey

    allowed_tools = []
    blocked_tools = []
    resolved_mode = mode or "safe"
    api_key_id = None
    profile = None

    if api_key:
        try:
            # Find matching API key
            prefix = api_key[:10] if len(api_key) >= 10 else api_key
            key_obj = (
                MCPApiKey.objects.select_related("profile")
                .filter(account_id=account_id, key_prefix=prefix, is_active=True)
                .first()
            )

            if key_obj and key_obj.check_key(api_key):
                api_key_id = key_obj.id
                key_obj.mark_used()

                # Check if API key has a profile
                if key_obj.profile and key_obj.profile.is_active:
                    profile = key_obj.profile
                    if not mode:
                        resolved_mode = profile.mode
                    # Profile's include/exclude tools
                    allowed_tools = profile.include_tools or []
                    blocked_tools = profile.exclude_tools or []
                else:
                    # Legacy: use API key's direct settings
                    if not mode:
                        resolved_mode = key_obj.mode
                    allowed_tools = key_obj.allowed_tools or []
                    blocked_tools = key_obj.blocked_tools or []
        except Exception as e:
            logger.warning(f"Failed to load API key permissions: {e}")

    return MCPPermissionChecker(
        account_id=account_id,
        mode=resolved_mode,
        allowed_tools=allowed_tools,
        blocked_tools=blocked_tools,
        api_key_id=api_key_id,
        project_identifier=project_identifier,
        user_id=user_id,
        profile=profile,
    )
