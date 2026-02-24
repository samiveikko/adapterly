"""
Tool category resolution and filtering for MCP.

This module provides the core category-based access control system for MCP tools.
External agents only see and can call tools in their allowed categories.
"""

import fnmatch
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CategoryResolutionResult:
    """Result of category resolution showing effective permissions."""

    effective_categories: set[str] | None  # None = no restriction (all allowed)
    agent_categories: list[str] | None
    project_categories: list[str] | None
    user_categories: list[str] | None
    is_restricted: bool = True

    @property
    def all_allowed(self) -> bool:
        """Check if all categories are allowed (no restriction)."""
        return self.effective_categories is None


class ToolCategoryResolver:
    """
    Resolves tool categories and determines effective permissions.

    Combines agent, project, and user policies using intersection semantics:
    - null/None policy = no restriction for that layer
    - empty list = all categories allowed for that layer
    - effective = agent ∩ project ∩ user
    """

    def __init__(
        self,
        account_id: int,
        api_key_id: int | None = None,
        project_identifier: str | None = None,
        user_id: int | None = None,
    ):
        """
        Initialize the category resolver.

        Args:
            account_id: Account ID for scoping
            api_key_id: Optional API key ID to load agent policy
            project_identifier: Optional project identifier to load project policy
            user_id: Optional user ID to load user policy
        """
        self.account_id = account_id
        self.api_key_id = api_key_id
        self.project_identifier = project_identifier
        self.user_id = user_id

        # Cached data
        self._mappings = None
        self._effective_result = None

    def get_tool_categories(self, tool_key: str) -> list[str]:
        """
        Get the categories that a tool belongs to.

        Args:
            tool_key: The tool name/key to look up

        Returns:
            List of category keys the tool belongs to
        """
        if self._mappings is None:
            self._load_mappings()

        categories = []
        for pattern, category_key in self._mappings:
            if fnmatch.fnmatch(tool_key, pattern):
                categories.append(category_key)

        return list(set(categories))  # Remove duplicates

    def get_effective_categories(self) -> CategoryResolutionResult:
        """
        Calculate the effective allowed categories.

        Resolution:
            effective = agent_allowed ∩ project_allowed ∩ user_allowed
            null means "no restriction" for that layer

        Returns:
            CategoryResolutionResult with effective categories
        """
        if self._effective_result is not None:
            return self._effective_result

        agent_cats = self._get_agent_categories()
        project_cats = self._get_project_categories()
        user_cats = self._get_user_categories()

        # Start with agent categories
        if agent_cats is None or len(agent_cats) == 0:
            # Empty list or None = no restriction from agent
            effective: set[str] | None = None
        else:
            effective = set(agent_cats)

        # Intersect with project categories if specified
        if project_cats is not None:
            if effective is None:
                effective = set(project_cats) if project_cats else None
            elif project_cats:
                effective = effective.intersection(project_cats)
            # If project_cats is empty list, keep current effective (no additional restriction)

        # Intersect with user categories if specified
        if user_cats is not None:
            if effective is None:
                effective = set(user_cats) if user_cats else None
            elif user_cats:
                effective = effective.intersection(user_cats)
            # If user_cats is empty list, keep current effective (no additional restriction)

        self._effective_result = CategoryResolutionResult(
            effective_categories=effective,
            agent_categories=agent_cats,
            project_categories=project_cats,
            user_categories=user_cats,
            is_restricted=effective is not None,
        )

        return self._effective_result

    def is_tool_allowed(self, tool_key: str) -> bool:
        """
        Check if a tool is allowed based on category restrictions.

        A tool is allowed if:
        1. It has at least one category, AND
        2. At least one of its categories is in the effective allowed set

        Uncategorized tools are blocked.

        Args:
            tool_key: The tool name/key to check

        Returns:
            True if the tool is allowed, False otherwise
        """
        effective_result = self.get_effective_categories()

        # If no restriction, all tools are allowed
        if effective_result.all_allowed:
            return True

        # Get tool's categories
        tool_categories = self.get_tool_categories(tool_key)

        # Uncategorized tools are blocked
        if not tool_categories:
            logger.debug(f"Tool '{tool_key}' blocked: uncategorized")
            return False

        # Check if any tool category is in effective allowed set
        effective_cats = effective_result.effective_categories
        for cat in tool_categories:
            if cat in effective_cats:
                return True

        logger.debug(f"Tool '{tool_key}' blocked: categories {tool_categories} not in allowed {effective_cats}")
        return False

    def filter_tools(self, tool_keys: list[str]) -> list[str]:
        """
        Filter a list of tool keys to only include allowed tools.

        Args:
            tool_keys: List of tool names/keys to filter

        Returns:
            List of allowed tool keys
        """
        return [key for key in tool_keys if self.is_tool_allowed(key)]

    def _load_mappings(self):
        """Load tool-to-category mappings from database."""
        from apps.mcp.models import ToolCategoryMapping

        self._mappings = list(
            ToolCategoryMapping.objects.filter(account_id=self.account_id)
            .select_related("category")
            .values_list("tool_key_pattern", "category__key")
        )

    def _get_agent_categories(self) -> list[str] | None:
        """Get allowed categories from agent policy."""
        if not self.api_key_id:
            return None

        from apps.mcp.models import AgentPolicy

        try:
            policy = AgentPolicy.objects.get(account_id=self.account_id, api_key_id=self.api_key_id)
            return policy.allowed_categories
        except AgentPolicy.DoesNotExist:
            return None

    def _get_project_categories(self) -> list[str] | None:
        """Get allowed categories from project policy."""
        if not self.project_identifier:
            return None

        from apps.mcp.models import ProjectPolicy

        # Try exact match first
        try:
            policy = ProjectPolicy.objects.get(
                account_id=self.account_id, project_identifier=self.project_identifier, is_active=True
            )
            return policy.allowed_categories
        except ProjectPolicy.DoesNotExist:
            pass

        # Try pattern match
        policies = ProjectPolicy.objects.filter(account_id=self.account_id, is_active=True)
        for policy in policies:
            if fnmatch.fnmatch(self.project_identifier, policy.project_identifier):
                return policy.allowed_categories

        return None

    def _get_user_categories(self) -> list[str] | None:
        """Get allowed categories from user policy."""
        if not self.user_id:
            return None

        from apps.mcp.models import UserPolicy

        try:
            policy = UserPolicy.objects.get(account_id=self.account_id, user_id=self.user_id, is_active=True)
            return policy.allowed_categories
        except UserPolicy.DoesNotExist:
            return None
