"""
URL configuration for MCP API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.mcp.api.views import (
    AgentPolicyViewSet,
    CategoryDebugView,
    EffectiveCategoriesView,
    MCPApiKeyViewSet,
    MCPAuditLogViewSet,
    MCPSessionViewSet,
    ProjectIntegrationViewSet,
    ProjectPolicyViewSet,
    ToolCategoryMappingViewSet,
    ToolCategoryViewSet,
    UserPolicyViewSet,
)

router = DefaultRouter()
router.register(r"api-keys", MCPApiKeyViewSet, basename="mcp-api-key")
router.register(r"sessions", MCPSessionViewSet, basename="mcp-session")
router.register(r"audit-logs", MCPAuditLogViewSet, basename="mcp-audit-log")
router.register(r"categories", ToolCategoryViewSet, basename="mcp-category")
router.register(r"tool-mappings", ToolCategoryMappingViewSet, basename="mcp-tool-mapping")
router.register(r"agent-policies", AgentPolicyViewSet, basename="mcp-agent-policy")
router.register(r"project-policies", ProjectPolicyViewSet, basename="mcp-project-policy")
router.register(r"user-policies", UserPolicyViewSet, basename="mcp-user-policy")
router.register(r"project-integrations", ProjectIntegrationViewSet, basename="mcp-project-integration")

app_name = "mcp-api"

urlpatterns = [
    path("", include(router.urls)),
    path("effective-categories/", EffectiveCategoriesView.as_view(), name="effective-categories"),
    path("category-debug/", CategoryDebugView.as_view(), name="category-debug"),
]
