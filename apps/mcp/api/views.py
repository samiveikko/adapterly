"""
API Views for MCP management.
"""

import fnmatch
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mcp.api.serializers import (
    AgentPolicySerializer,
    EffectiveCategoriesSerializer,
    MCPApiKeyCreateSerializer,
    MCPApiKeySerializer,
    MCPAuditLogSerializer,
    MCPSessionSerializer,
    ProjectIntegrationSerializer,
    ProjectPolicySerializer,
    ToolCategoryMappingSerializer,
    ToolCategorySerializer,
    UserPolicySerializer,
)
from apps.mcp.categories import ToolCategoryResolver
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


class AccountScopedMixin:
    """Mixin to scope querysets to the user's active account."""

    def get_queryset(self):
        queryset = super().get_queryset()
        account = getattr(self.request, "account", None)
        if account:
            return queryset.filter(account=account)
        return queryset.none()


class MCPApiKeyViewSet(AccountScopedMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing MCP API keys.

    list: List all API keys for the account
    create: Create a new API key (returns full key only once)
    retrieve: Get API key details
    update: Update API key settings
    destroy: Delete an API key
    """

    queryset = MCPApiKey.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return MCPApiKeyCreateSerializer
        return MCPApiKeySerializer

    def perform_create(self, serializer):
        account = getattr(self.request, "account", None)
        serializer.save(account=account)

    @action(detail=True, methods=["post"])
    def regenerate(self, request, pk=None):
        """Regenerate an API key (creates new key, invalidates old)."""
        api_key = self.get_object()

        # Generate new key
        key, prefix, key_hash = MCPApiKey.generate_key()

        # Update the key
        api_key.key_prefix = prefix
        api_key.key_hash = key_hash
        api_key.save()

        return Response({"api_key": key, "message": "API key regenerated. Save this key - it will not be shown again."})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate an API key."""
        api_key = self.get_object()
        api_key.is_active = False
        api_key.save()
        return Response({"status": "deactivated"})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate an API key."""
        api_key = self.get_object()
        api_key.is_active = True
        api_key.save()
        return Response({"status": "activated"})


class MCPSessionViewSet(AccountScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing MCP sessions.

    Sessions are read-only through the API.
    """

    queryset = MCPSession.objects.all()
    serializer_class = MCPSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["is_active", "mode", "transport"]
    ordering_fields = ["created_at", "last_activity", "tool_calls_count"]
    ordering = ["-last_activity"]

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get active sessions."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def terminate(self, request, pk=None):
        """Terminate (deactivate) a session."""
        session = self.get_object()
        session.is_active = False
        session.save()
        return Response({"status": "terminated"})


class MCPAuditLogViewSet(AccountScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing MCP audit logs.

    Audit logs are read-only.
    """

    queryset = MCPAuditLog.objects.all()
    serializer_class = MCPAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["tool_type", "success", "mode", "transport", "tool_name"]
    search_fields = ["tool_name", "session_id", "error_message"]
    ordering_fields = ["timestamp", "duration_ms"]
    ordering = ["-timestamp"]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get audit log summary statistics."""
        queryset = self.get_queryset()

        # Apply date filter if provided
        days = int(request.query_params.get("days", 7))
        since = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(timestamp__gte=since)

        # Calculate statistics
        stats = queryset.aggregate(
            total_calls=Count("id"),
            successful_calls=Count("id", filter=Q(success=True)),
            failed_calls=Count("id", filter=Q(success=False)),
            avg_duration_ms=Avg("duration_ms"),
        )

        # Tool breakdown
        tool_breakdown = dict(
            queryset.values("tool_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
            .values_list("tool_name", "count")
        )

        # Tool type breakdown
        type_breakdown = dict(
            queryset.values("tool_type").annotate(count=Count("id")).values_list("tool_type", "count")
        )

        return Response(
            {
                "total_calls": stats["total_calls"] or 0,
                "successful_calls": stats["successful_calls"] or 0,
                "failed_calls": stats["failed_calls"] or 0,
                "success_rate": (stats["successful_calls"] / stats["total_calls"] * 100 if stats["total_calls"] else 0),
                "avg_duration_ms": round(stats["avg_duration_ms"] or 0, 2),
                "tool_breakdown": tool_breakdown,
                "type_breakdown": type_breakdown,
                "date_range": {"from": since.isoformat(), "to": timezone.now().isoformat(), "days": days},
            }
        )

    @action(detail=False, methods=["get"])
    def by_session(self, request):
        """Get audit logs grouped by session."""
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response({"error": "session_id parameter required"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(session_id=session_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def errors(self, request):
        """Get recent error logs."""
        limit = min(int(request.query_params.get("limit", 50)), 500)
        queryset = self.get_queryset().filter(success=False)[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ToolCategoryViewSet(AccountScopedMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing tool categories.

    list: List all tool categories for the account
    create: Create a new tool category
    retrieve: Get category details
    update: Update category settings
    destroy: Delete a category
    """

    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["risk_level", "is_global"]
    search_fields = ["key", "name", "description"]
    ordering = ["key"]

    def perform_create(self, serializer):
        account = getattr(self.request, "account", None)
        serializer.save(account=account)


class ToolCategoryMappingViewSet(AccountScopedMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing tool-to-category mappings.

    list: List all mappings for the account
    create: Create a new mapping
    retrieve: Get mapping details
    update: Update mapping
    destroy: Delete a mapping
    """

    queryset = ToolCategoryMapping.objects.select_related("category").all()
    serializer_class = ToolCategoryMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["category", "is_auto"]
    search_fields = ["tool_key_pattern"]
    ordering = ["tool_key_pattern"]

    def perform_create(self, serializer):
        account = getattr(self.request, "account", None)
        serializer.save(account=account)


class AgentPolicyViewSet(AccountScopedMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing agent (API key) policies.

    list: List all agent policies for the account
    create: Create a new policy for an API key
    retrieve: Get policy details
    update: Update policy
    destroy: Delete a policy
    """

    queryset = AgentPolicy.objects.select_related("api_key").all()
    serializer_class = AgentPolicySerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        account = getattr(self.request, "account", None)
        serializer.save(account=account)

    @action(detail=False, methods=["get"], url_path="by-api-key/(?P<api_key_id>[^/.]+)")
    def by_api_key(self, request, api_key_id=None):
        """Get policy for a specific API key."""
        try:
            policy = self.get_queryset().get(api_key_id=api_key_id)
            serializer = self.get_serializer(policy)
            return Response(serializer.data)
        except AgentPolicy.DoesNotExist:
            return Response({"error": "No policy found for this API key"}, status=status.HTTP_404_NOT_FOUND)


class ProjectPolicyViewSet(AccountScopedMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing project policies.

    list: List all project policies for the account
    create: Create a new project policy
    retrieve: Get policy details
    update: Update policy
    destroy: Delete a policy
    """

    queryset = ProjectPolicy.objects.all()
    serializer_class = ProjectPolicySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["is_active"]
    search_fields = ["project_identifier", "name"]
    ordering = ["project_identifier"]

    def perform_create(self, serializer):
        account = getattr(self.request, "account", None)
        serializer.save(account=account)

    @action(detail=False, methods=["get"], url_path="by-identifier/(?P<identifier>.+)")
    def by_identifier(self, request, identifier=None):
        """Get policy for a specific project identifier."""
        try:
            policy = self.get_queryset().get(project_identifier=identifier)
            serializer = self.get_serializer(policy)
            return Response(serializer.data)
        except ProjectPolicy.DoesNotExist:
            return Response({"error": "No policy found for this project"}, status=status.HTTP_404_NOT_FOUND)


class UserPolicyViewSet(AccountScopedMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing user policies.

    list: List all user policies for the account
    create: Create a new user policy
    retrieve: Get policy details
    update: Update policy
    destroy: Delete a policy
    """

    queryset = UserPolicy.objects.select_related("user").all()
    serializer_class = UserPolicySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["is_active"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        account = getattr(self.request, "account", None)
        serializer.save(account=account)

    @action(detail=False, methods=["get"], url_path="by-user/(?P<user_id>[^/.]+)")
    def by_user(self, request, user_id=None):
        """Get policy for a specific user."""
        try:
            policy = self.get_queryset().get(user_id=user_id)
            serializer = self.get_serializer(policy)
            return Response(serializer.data)
        except UserPolicy.DoesNotExist:
            return Response({"error": "No policy found for this user"}, status=status.HTTP_404_NOT_FOUND)


class EffectiveCategoriesView(APIView):
    """
    API endpoint to check resolved effective categories.

    GET /api/mcp/effective-categories/?api_key_id=&project_identifier=&user_id=
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = getattr(request, "account", None)
        if not account:
            return Response({"error": "No account context"}, status=status.HTTP_400_BAD_REQUEST)

        # Get parameters
        api_key_id = request.query_params.get("api_key_id")
        project_identifier = request.query_params.get("project_identifier")
        user_id = request.query_params.get("user_id")

        # Convert to int if provided
        if api_key_id:
            try:
                api_key_id = int(api_key_id)
            except ValueError:
                return Response({"error": "Invalid api_key_id"}, status=status.HTTP_400_BAD_REQUEST)

        if user_id:
            try:
                user_id = int(user_id)
            except ValueError:
                return Response({"error": "Invalid user_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Resolve categories
        resolver = ToolCategoryResolver(
            account_id=account.id, api_key_id=api_key_id, project_identifier=project_identifier, user_id=user_id
        )

        result = resolver.get_effective_categories()

        # Convert to serializable format
        data = {
            "effective_categories": list(result.effective_categories) if result.effective_categories else None,
            "agent_categories": result.agent_categories,
            "project_categories": result.project_categories,
            "user_categories": result.user_categories,
            "is_restricted": result.is_restricted,
            "all_allowed": result.all_allowed,
        }

        serializer = EffectiveCategoriesSerializer(data)
        return Response(serializer.data)


class CategoryDebugView(APIView):
    """
    Debug view to see full category resolution with tool visibility.

    GET /api/mcp/category-debug/?api_key_id=&project_identifier=&user_id=

    Returns:
        - All available categories for the account
        - All tool mappings
        - Effective categories after policy resolution
        - Policy details (agent, project, user)
        - Sample of allowed/blocked tools
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = getattr(request, "account", None)
        if not account:
            return Response({"error": "No account context"}, status=status.HTTP_400_BAD_REQUEST)

        # Get parameters
        api_key_id = request.query_params.get("api_key_id")
        project_identifier = request.query_params.get("project_identifier")
        user_id = request.query_params.get("user_id")

        # Convert to int if provided
        if api_key_id:
            try:
                api_key_id = int(api_key_id)
            except ValueError:
                return Response({"error": "Invalid api_key_id"}, status=status.HTTP_400_BAD_REQUEST)

        if user_id:
            try:
                user_id = int(user_id)
            except ValueError:
                return Response({"error": "Invalid user_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Get all categories
        categories = ToolCategory.objects.filter(account=account).values("id", "key", "name", "risk_level", "is_global")

        # Get all mappings
        mappings = (
            ToolCategoryMapping.objects.filter(account=account)
            .select_related("category")
            .values("id", "tool_key_pattern", "category__key", "is_auto")
        )

        # Get policies
        agent_policy = None
        if api_key_id:
            try:
                policy = AgentPolicy.objects.select_related("api_key").get(account=account, api_key_id=api_key_id)
                agent_policy = {
                    "id": policy.id,
                    "api_key_name": policy.api_key.name,
                    "allowed_categories": policy.allowed_categories,
                }
            except AgentPolicy.DoesNotExist:
                agent_policy = {"error": "No policy found for this API key"}

        project_policy = None
        if project_identifier:
            try:
                policy = ProjectPolicy.objects.get(
                    account=account, project_identifier=project_identifier, is_active=True
                )
                project_policy = {
                    "id": policy.id,
                    "name": policy.name,
                    "project_identifier": policy.project_identifier,
                    "allowed_categories": policy.allowed_categories,
                }
            except ProjectPolicy.DoesNotExist:
                # Try pattern match
                policies = ProjectPolicy.objects.filter(account=account, is_active=True)
                for p in policies:
                    if fnmatch.fnmatch(project_identifier, p.project_identifier):
                        project_policy = {
                            "id": p.id,
                            "name": p.name,
                            "project_identifier": p.project_identifier,
                            "matched_pattern": True,
                            "allowed_categories": p.allowed_categories,
                        }
                        break
                if not project_policy:
                    project_policy = {"error": "No policy found for this project"}

        user_policy_data = None
        if user_id:
            try:
                policy = UserPolicy.objects.select_related("user").get(account=account, user_id=user_id, is_active=True)
                user_policy_data = {
                    "id": policy.id,
                    "username": policy.user.username,
                    "allowed_categories": policy.allowed_categories,
                }
            except UserPolicy.DoesNotExist:
                user_policy_data = {"error": "No policy found for this user"}

        # Resolve effective categories
        resolver = ToolCategoryResolver(
            account_id=account.id, api_key_id=api_key_id, project_identifier=project_identifier, user_id=user_id
        )
        result = resolver.get_effective_categories()

        # Test some sample tools
        sample_tools = [
            "salesforce_contact_list",
            "salesforce_contact_create",
            "hubspot_deal_get",
            "hubspot_deal_delete",
            "admin_user_create",
            "unknown_tool",
        ]
        tool_access = {}
        for tool in sample_tools:
            tool_cats = resolver.get_tool_categories(tool)
            is_allowed = resolver.is_tool_allowed(tool)
            tool_access[tool] = {"categories": tool_cats, "allowed": is_allowed}

        return Response(
            {
                "account": {
                    "id": account.id,
                    "name": account.name,
                },
                "parameters": {
                    "api_key_id": api_key_id,
                    "project_identifier": project_identifier,
                    "user_id": user_id,
                },
                "categories": list(categories),
                "mappings": list(mappings),
                "policies": {
                    "agent": agent_policy,
                    "project": project_policy,
                    "user": user_policy_data,
                },
                "resolution": {
                    "effective_categories": list(result.effective_categories) if result.effective_categories else None,
                    "is_restricted": result.is_restricted,
                    "all_allowed": result.all_allowed,
                },
                "tool_access_samples": tool_access,
            }
        )


class ProjectIntegrationViewSet(AccountScopedMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing project integrations.

    Integrations link projects to systems with credential source and external IDs.
    """

    queryset = ProjectIntegration.objects.select_related("project", "system").all()
    serializer_class = ProjectIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["project", "system", "is_enabled", "credential_source"]
    search_fields = ["system__alias", "system__display_name", "external_id"]
    ordering = ["system__alias"]

    def get_queryset(self):
        queryset = ProjectIntegration.objects.select_related("project", "system")
        account = getattr(self.request, "account", None)
        if account:
            return queryset.filter(project__account=account)
        return queryset.none()

    @action(detail=False, methods=["get"], url_path="by-project/(?P<project_id>[^/.]+)")
    def by_project(self, request, project_id=None):
        """Get integrations for a specific project."""
        queryset = self.get_queryset().filter(project_id=project_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
