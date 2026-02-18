"""
URL configuration for Adapterly - MCP Tool Gateway.

Routes for system connections, MCP protocol, and administration.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.mcp.api.transport import mcp_endpoint

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Authentication
    path("auth/", include("allauth.urls")),
    # Core (landing, dashboard)
    path("", include("apps.core.urls")),
    # Account management
    path("account/", include("apps.accounts.urls")),
    # Systems (adapters, integrations)
    path("systems/", include("apps.systems.urls")),
    # Help
    path("help/", include("apps.help.urls")),
    # Projects
    path("projects/", include("apps.mcp.project_urls")),
    # MCP Gateway
    path("mcp/", include("apps.mcp.urls")),
    path("mcp/v1/", mcp_endpoint, name="mcp-protocol"),  # MCP Streamable HTTP
    # API endpoints
    path("api/", include("apps.accounts.api.urls")),
    path("api/mcp/", include("apps.mcp.api.urls")),
    path("api/systems/", include("apps.systems.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
