"""
Tests for MCP tool category system.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Account
from apps.mcp.categories import ToolCategoryResolver
from apps.mcp.models import AgentPolicy, MCPApiKey, ProjectPolicy, ToolCategory, ToolCategoryMapping, UserPolicy
from apps.mcp.permissions import MCPPermissionChecker

User = get_user_model()


class TestToolCategoryResolver(TestCase):
    """Tests for ToolCategoryResolver."""

    def setUp(self):
        """Set up test data."""
        # Create account
        self.account = Account.objects.create(name="Test Account")

        # Create user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass")

        # Create API key
        key, prefix, key_hash = MCPApiKey.generate_key()
        self.api_key = MCPApiKey.objects.create(
            account=self.account, name="Test Key", key_prefix=prefix, key_hash=key_hash, mode="power"
        )

        # Create categories
        self.cat_read = ToolCategory.objects.create(
            account=self.account, key="system.read", name="System Read", risk_level="low"
        )
        self.cat_write = ToolCategory.objects.create(
            account=self.account, key="system.write", name="System Write", risk_level="medium"
        )
        self.cat_admin = ToolCategory.objects.create(account=self.account, key="admin", name="Admin", risk_level="high")

        # Create mappings
        ToolCategoryMapping.objects.create(account=self.account, tool_key_pattern="*_list", category=self.cat_read)
        ToolCategoryMapping.objects.create(account=self.account, tool_key_pattern="*_get", category=self.cat_read)
        ToolCategoryMapping.objects.create(account=self.account, tool_key_pattern="*_create", category=self.cat_write)
        ToolCategoryMapping.objects.create(account=self.account, tool_key_pattern="*_delete", category=self.cat_admin)

    def test_get_tool_categories(self):
        """Test tool category lookup via patterns."""
        resolver = ToolCategoryResolver(account_id=self.account.id)

        # Tool matching *_list pattern
        cats = resolver.get_tool_categories("salesforce_contact_list")
        self.assertIn("system.read", cats)

        # Tool matching *_create pattern
        cats = resolver.get_tool_categories("hubspot_deal_create")
        self.assertIn("system.write", cats)

        # Tool matching *_delete pattern
        cats = resolver.get_tool_categories("admin_user_delete")
        self.assertIn("admin", cats)

    def test_uncategorized_tools_blocked(self):
        """Uncategorized tools should be blocked when categories are enforced."""
        # Create agent policy with restricted categories
        AgentPolicy.objects.create(account=self.account, api_key=self.api_key, allowed_categories=["system.read"])

        resolver = ToolCategoryResolver(account_id=self.account.id, api_key_id=self.api_key.id)

        # Uncategorized tool should be blocked
        self.assertFalse(resolver.is_tool_allowed("random_unknown_tool"))

        # Categorized and allowed tool should pass
        self.assertTrue(resolver.is_tool_allowed("salesforce_contact_list"))

    def test_agent_policy_restricts_categories(self):
        """Agent policy should restrict available categories."""
        AgentPolicy.objects.create(account=self.account, api_key=self.api_key, allowed_categories=["system.read"])

        resolver = ToolCategoryResolver(account_id=self.account.id, api_key_id=self.api_key.id)

        result = resolver.get_effective_categories()

        self.assertTrue(result.is_restricted)
        self.assertIn("system.read", result.effective_categories)
        self.assertNotIn("system.write", result.effective_categories)

    def test_project_policy_intersection(self):
        """Project policy should intersect with agent policy."""
        # Agent allows read and write
        AgentPolicy.objects.create(
            account=self.account, api_key=self.api_key, allowed_categories=["system.read", "system.write"]
        )

        # Project only allows read
        ProjectPolicy.objects.create(
            account=self.account, project_identifier="PROJ-123", name="Test Project", allowed_categories=["system.read"]
        )

        resolver = ToolCategoryResolver(
            account_id=self.account.id, api_key_id=self.api_key.id, project_identifier="PROJ-123"
        )

        result = resolver.get_effective_categories()

        # Intersection should only include read
        self.assertTrue(result.is_restricted)
        self.assertIn("system.read", result.effective_categories)
        self.assertNotIn("system.write", result.effective_categories)

    def test_user_policy_intersection(self):
        """User policy should intersect with other policies."""
        # Agent allows all
        AgentPolicy.objects.create(
            account=self.account, api_key=self.api_key, allowed_categories=["system.read", "system.write", "admin"]
        )

        # User only allows read and write
        UserPolicy.objects.create(
            account=self.account, user=self.user, allowed_categories=["system.read", "system.write"]
        )

        resolver = ToolCategoryResolver(account_id=self.account.id, api_key_id=self.api_key.id, user_id=self.user.id)

        result = resolver.get_effective_categories()

        # Admin should be removed by user policy
        self.assertIn("system.read", result.effective_categories)
        self.assertIn("system.write", result.effective_categories)
        self.assertNotIn("admin", result.effective_categories)

    def test_null_policy_no_restriction(self):
        """Null allowed_categories means no restriction from that layer."""
        # Project with null (no restriction)
        ProjectPolicy.objects.create(
            account=self.account,
            project_identifier="PROJ-456",
            name="Open Project",
            allowed_categories=None,  # No restriction
        )

        resolver = ToolCategoryResolver(account_id=self.account.id, project_identifier="PROJ-456")

        result = resolver.get_effective_categories()

        # Should have no restriction
        self.assertFalse(result.is_restricted)
        self.assertTrue(result.all_allowed)

    def test_empty_list_means_all_allowed(self):
        """Empty list in agent policy means all categories allowed."""
        AgentPolicy.objects.create(
            account=self.account,
            api_key=self.api_key,
            allowed_categories=[],  # Empty = all allowed
        )

        resolver = ToolCategoryResolver(account_id=self.account.id, api_key_id=self.api_key.id)

        result = resolver.get_effective_categories()

        # Empty list = no restriction
        self.assertFalse(result.is_restricted)

    def test_filter_tools(self):
        """Test filtering a list of tools."""
        AgentPolicy.objects.create(account=self.account, api_key=self.api_key, allowed_categories=["system.read"])

        resolver = ToolCategoryResolver(account_id=self.account.id, api_key_id=self.api_key.id)

        tools = [
            "salesforce_contact_list",  # system.read - allowed
            "salesforce_contact_get",  # system.read - allowed
            "salesforce_contact_create",  # system.write - blocked
            "unknown_tool",  # uncategorized - blocked
        ]

        allowed = resolver.filter_tools(tools)

        self.assertIn("salesforce_contact_list", allowed)
        self.assertIn("salesforce_contact_get", allowed)
        self.assertNotIn("salesforce_contact_create", allowed)
        self.assertNotIn("unknown_tool", allowed)

    def test_project_pattern_matching(self):
        """Test project identifier pattern matching."""
        ProjectPolicy.objects.create(
            account=self.account,
            project_identifier="PROJ-*",
            name="All PROJ Projects",
            allowed_categories=["system.read"],
        )

        resolver = ToolCategoryResolver(account_id=self.account.id, project_identifier="PROJ-123")

        result = resolver.get_effective_categories()

        self.assertTrue(result.is_restricted)
        self.assertIn("system.read", result.effective_categories)


class TestMCPPermissionCheckerWithCategories(TestCase):
    """Tests for MCPPermissionChecker category integration."""

    def setUp(self):
        """Set up test data."""
        self.account = Account.objects.create(name="Test Account")

        key, prefix, key_hash = MCPApiKey.generate_key()
        self.api_key = MCPApiKey.objects.create(
            account=self.account, name="Test Key", key_prefix=prefix, key_hash=key_hash, mode="power"
        )

        # Create categories
        self.cat_read = ToolCategory.objects.create(
            account=self.account, key="system.read", name="System Read", risk_level="low"
        )

        # Create mapping
        ToolCategoryMapping.objects.create(account=self.account, tool_key_pattern="*_list", category=self.cat_read)

        # Create restrictive agent policy
        AgentPolicy.objects.create(account=self.account, api_key=self.api_key, allowed_categories=["system.read"])

    def test_permission_checker_respects_categories(self):
        """Permission checker should respect category restrictions."""
        checker = MCPPermissionChecker(account_id=self.account.id, mode="power", api_key_id=self.api_key.id)

        # Allowed tool (system.read category)
        result = checker.can_call_tool("salesforce_contact_list", "system_read")
        self.assertTrue(result.allowed)

        # Blocked tool (no matching category)
        result = checker.can_call_tool("salesforce_contact_create", "system_write")
        self.assertFalse(result.allowed)
        self.assertIn("categories", result.reason.lower())

    def test_blocked_tools_take_precedence(self):
        """Blocked tools should be denied even if category allows."""
        checker = MCPPermissionChecker(
            account_id=self.account.id, mode="power", blocked_tools=["salesforce_*"], api_key_id=self.api_key.id
        )

        # Should be blocked by pattern even though category allows
        result = checker.can_call_tool("salesforce_contact_list", "system_read")
        self.assertFalse(result.allowed)
        self.assertIn("blocked", result.reason.lower())

    def test_get_tool_list_filter_includes_resolver(self):
        """Tool list filter should include category resolver."""
        checker = MCPPermissionChecker(account_id=self.account.id, mode="power", api_key_id=self.api_key.id)

        filter_opts = checker.get_tool_list_filter()

        self.assertIn("category_resolver", filter_opts)
        self.assertIsNotNone(filter_opts["category_resolver"])
