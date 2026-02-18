"""
URL configuration for Project management pages.

All URLs are under /projects/ namespace.
"""

from django.urls import path

from apps.mcp import project_views

app_name = "projects"

urlpatterns = [
    # Project CRUD
    path("", project_views.project_list, name="list"),
    path("create/", project_views.project_create, name="create"),
    path("<slug:slug>/", project_views.project_detail, name="detail"),
    path("<slug:slug>/edit/", project_views.project_edit, name="edit"),
    path("<slug:slug>/delete/", project_views.project_delete, name="delete"),
    # Project Integrations
    path("<slug:slug>/integrations/", project_views.project_integrations_view, name="integrations"),
    path("<slug:slug>/integrations/add/", project_views.project_integration_add_view, name="integration_add"),
    path(
        "<slug:slug>/integrations/<int:integration_id>/edit/",
        project_views.project_integration_edit_view,
        name="integration_edit",
    ),
    path(
        "<slug:slug>/integrations/<int:integration_id>/remove/",
        project_views.project_integration_remove_view,
        name="integration_remove",
    ),
    # Project-scoped views
    path("<slug:slug>/api-keys/", project_views.project_api_keys_view, name="api_keys"),
    path("<slug:slug>/tools/", project_views.project_tools_view, name="tools"),
    path("<slug:slug>/logs/", project_views.project_logs_view, name="logs"),
]
