"""
Serializers for MCP API.
"""

from rest_framework import serializers

from apps.mcp.models import (
    AgentPolicy,
    MCPApiKey,
    MCPAuditLog,
    MCPSession,
    ProjectIntegration,
    ProjectPolicy,
    ToolCategory,
    ToolCategoryMapping,
    UserPolicy,
)


class MCPApiKeySerializer(serializers.ModelSerializer):
    """Serializer for MCP API keys (read)."""

    account_name = serializers.CharField(source="account.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, allow_null=True)

    class Meta:
        model = MCPApiKey
        fields = [
            "id",
            "name",
            "account",
            "account_name",
            "key_prefix",
            "mode",
            "allowed_tools",
            "blocked_tools",
            "is_active",
            "last_used_at",
            "created_at",
            "expires_at",
            "created_by",
            "created_by_username",
        ]
        read_only_fields = [
            "key_prefix",
            "last_used_at",
            "created_at",
            "created_by",
        ]


class MCPApiKeyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating MCP API keys."""

    # The full key is returned only once on creation
    api_key = serializers.CharField(read_only=True)

    class Meta:
        model = MCPApiKey
        fields = [
            "id",
            "name",
            "account",
            "mode",
            "allowed_tools",
            "blocked_tools",
            "expires_at",
            "api_key",  # Returned only on create
        ]

    def create(self, validated_data):
        # Generate key
        key, prefix, key_hash = MCPApiKey.generate_key()

        # Create the API key object
        api_key = MCPApiKey.objects.create(
            key_prefix=prefix, key_hash=key_hash, created_by=self.context["request"].user, **validated_data
        )

        # Attach the full key for response (not saved to DB)
        api_key.api_key = key

        return api_key


class MCPSessionSerializer(serializers.ModelSerializer):
    """Serializer for MCP sessions."""

    account_name = serializers.CharField(source="account.name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True, allow_null=True)

    class Meta:
        model = MCPSession
        fields = [
            "id",
            "session_id",
            "account",
            "account_name",
            "user",
            "username",
            "mode",
            "transport",
            "is_active",
            "created_at",
            "last_activity",
            "tool_calls_count",
        ]
        read_only_fields = [
            "session_id",
            "created_at",
            "last_activity",
            "tool_calls_count",
        ]


class MCPAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for MCP audit logs."""

    account_name = serializers.CharField(source="account.name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True, allow_null=True)

    class Meta:
        model = MCPAuditLog
        fields = [
            "id",
            "account",
            "account_name",
            "user",
            "username",
            "tool_name",
            "tool_type",
            "parameters",
            "result_summary",
            "duration_ms",
            "success",
            "error_message",
            "session_id",
            "transport",
            "mode",
            "timestamp",
        ]
        read_only_fields = fields  # Audit logs are read-only


class MCPAuditLogSummarySerializer(serializers.Serializer):
    """Serializer for audit log summary statistics."""

    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    failed_calls = serializers.IntegerField()
    avg_duration_ms = serializers.FloatField()
    tool_breakdown = serializers.DictField()
    date_range = serializers.DictField()


class ToolCategorySerializer(serializers.ModelSerializer):
    """Serializer for tool categories."""

    class Meta:
        model = ToolCategory
        fields = [
            "id",
            "account",
            "key",
            "name",
            "description",
            "risk_level",
            "is_global",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ToolCategoryMappingSerializer(serializers.ModelSerializer):
    """Serializer for tool category mappings."""

    category_key = serializers.CharField(source="category.key", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = ToolCategoryMapping
        fields = [
            "id",
            "account",
            "tool_key_pattern",
            "category",
            "category_key",
            "category_name",
            "is_auto",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class AgentPolicySerializer(serializers.ModelSerializer):
    """Serializer for agent policies."""

    api_key_name = serializers.CharField(source="api_key.name", read_only=True)
    api_key_prefix = serializers.CharField(source="api_key.key_prefix", read_only=True)

    class Meta:
        model = AgentPolicy
        fields = [
            "id",
            "account",
            "api_key",
            "api_key_name",
            "api_key_prefix",
            "name",
            "allowed_categories",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ProjectPolicySerializer(serializers.ModelSerializer):
    """Serializer for project policies."""

    class Meta:
        model = ProjectPolicy
        fields = [
            "id",
            "account",
            "project_identifier",
            "name",
            "allowed_categories",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class UserPolicySerializer(serializers.ModelSerializer):
    """Serializer for user policies."""

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = UserPolicy
        fields = [
            "id",
            "account",
            "user",
            "username",
            "allowed_categories",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class EffectiveCategoriesSerializer(serializers.Serializer):
    """Serializer for effective categories resolution result."""

    effective_categories = serializers.ListField(child=serializers.CharField(), allow_null=True)
    agent_categories = serializers.ListField(child=serializers.CharField(), allow_null=True)
    project_categories = serializers.ListField(child=serializers.CharField(), allow_null=True)
    user_categories = serializers.ListField(child=serializers.CharField(), allow_null=True)
    is_restricted = serializers.BooleanField()
    all_allowed = serializers.BooleanField()


class ProjectIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for project integrations."""

    system_alias = serializers.CharField(source="system.alias", read_only=True)
    system_name = serializers.CharField(source="system.display_name", read_only=True)
    project_slug = serializers.CharField(source="project.slug", read_only=True)

    class Meta:
        model = ProjectIntegration
        fields = [
            "id",
            "project",
            "project_slug",
            "system",
            "system_alias",
            "system_name",
            "credential_source",
            "external_id",
            "is_enabled",
            "custom_config",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
