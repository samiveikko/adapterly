"""
User-facing views for Project management.

Slug-based URL structure: /projects/<slug>/...
"""

import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from apps.accounts.utils import get_active_account, get_active_account_user
from apps.mcp.models import (
    MCPApiKey,
    MCPAuditLog,
    Project,
    ProjectIntegration,
)


def _get_project_for_account(request, slug):
    """Get a project by slug, scoped to the active account."""
    active_account = get_active_account(request)
    if not active_account:
        return None, None
    project = get_object_or_404(Project, slug=slug, account=active_account)
    return active_account, project


# ============================================================================
# Project CRUD
# ============================================================================


@login_required
def project_list(request):
    """List all projects for the active account."""
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "No active account")
        return redirect("index")

    projects = (
        Project.objects.filter(account=active_account)
        .annotate(
            integration_count=Count("integrations", distinct=True),
            api_key_count=Count("api_keys", distinct=True),
        )
        .order_by("name")
    )

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "projects": projects,
    }

    return render(request, "mcp/project_list.html", context)


@login_required
def project_create(request):
    """Create a new project."""
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "No active account")
        return redirect("index")

    if not active_account_user.is_admin:
        messages.error(request, "Admin access required")
        return redirect("projects:list")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if not name:
            messages.error(request, "Project name is required")
        else:
            slug = slugify(name)[:100]
            if not slug:
                slug = "project"

            # Ensure unique slug within account
            base_slug = slug
            counter = 1
            while Project.objects.filter(account=active_account, slug=slug).exists():
                slug = f"{base_slug}-{counter}"[:100]
                counter += 1

            project = Project.objects.create(
                account=active_account,
                name=name,
                slug=slug,
                description=description,
            )
            messages.success(request, f"Project '{name}' created")
            return redirect("projects:detail", slug=project.slug)

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
    }

    return render(request, "mcp/project_form.html", context)


@login_required
def project_detail(request, slug):
    """Project workspace dashboard."""
    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "No active account")
        return redirect("index")

    integrations = ProjectIntegration.objects.filter(project=project).select_related("system")
    api_keys = MCPApiKey.objects.filter(project=project)
    log_count = MCPAuditLog.objects.filter(account=active_account).count()

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "project": project,
        "integrations": integrations,
        "api_keys": api_keys,
        "integration_count": integrations.count(),
        "api_key_count": api_keys.count(),
        "log_count": log_count,
        "active_tab": "overview",
    }

    return render(request, "mcp/project_detail.html", context)


@login_required
def project_edit(request, slug):
    """Edit a project."""
    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "No active account")
        return redirect("index")

    if not active_account_user.is_admin:
        messages.error(request, "Admin access required")
        return redirect("projects:detail", slug=slug)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not name:
            messages.error(request, "Project name is required")
        else:
            project.name = name
            project.description = description
            project.is_active = is_active
            project.save()
            messages.success(request, f"Project '{name}' updated")
            return redirect("projects:detail", slug=project.slug)

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "project": project,
    }

    return render(request, "mcp/project_form.html", context)


@login_required
@require_POST
def project_delete(request, slug):
    """Delete a project."""
    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "No active account")
        return redirect("index")

    if not active_account_user.is_admin:
        messages.error(request, "Admin access required")
        return redirect("projects:detail", slug=slug)

    project_name = project.name
    project.delete()
    messages.success(request, f"Project '{project_name}' deleted")
    return redirect("projects:list")


# ============================================================================
# Project-scoped Integrations (slug-based wrappers)
# ============================================================================


@login_required
def project_integrations_view(request, slug):
    """List integrations for a project (slug-based)."""
    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "No active account")
        return redirect("index")

    integrations = ProjectIntegration.objects.filter(project=project).select_related("system")

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "project": project,
        "integrations": integrations,
        "active_tab": "integrations",
    }

    return render(request, "mcp/project_integrations.html", context)


@login_required
def project_integration_add_view(request, slug):
    """Add a system integration to a project (slug-based)."""
    from apps.systems.models import AccountSystem, System

    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        messages.error(request, "Admin access required")
        return redirect("projects:list")

    existing_system_ids = ProjectIntegration.objects.filter(project=project).values_list("system_id", flat=True)

    available_systems = (
        System.objects.filter(
            account_configs__account=active_account,
            account_configs__is_enabled=True,
            is_active=True,
        )
        .exclude(id__in=existing_system_ids)
        .distinct()
    )

    if request.method == "POST":
        system_id = request.POST.get("system_id")
        credential_source = request.POST.get("credential_source", "account")
        external_id = request.POST.get("external_id", "").strip()
        notes = request.POST.get("notes", "").strip()

        if not system_id:
            messages.error(request, "System is required")
        else:
            try:
                system = System.objects.get(id=system_id, is_active=True)
            except System.DoesNotExist:
                messages.error(request, "System not found")
                return redirect("projects:integrations", slug=slug)

            accsys_qs = AccountSystem.objects.filter(
                account=active_account,
                system=system,
                is_enabled=True,
            )
            if credential_source == "project":
                accsys_qs = accsys_qs.filter(project=project)
            else:
                accsys_qs = accsys_qs.filter(project__isnull=True)

            if not accsys_qs.exists():
                messages.warning(
                    request,
                    f"No {credential_source}-level credentials found for {system.display_name}. "
                    f"Integration created but may not work until credentials are configured.",
                )

            ProjectIntegration.objects.create(
                project=project,
                system=system,
                credential_source=credential_source,
                external_id=external_id,
                notes=notes,
                is_enabled=True,
            )
            messages.success(request, f"Integration with {system.display_name} added")
            return redirect("projects:integrations", slug=slug)

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "project": project,
        "available_systems": available_systems,
        "active_tab": "integrations",
    }

    return render(request, "mcp/project_integration_form.html", context)


@login_required
def project_integration_edit_view(request, slug, integration_id):
    """Edit a project integration (slug-based)."""
    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        messages.error(request, "Admin access required")
        return redirect("projects:list")

    integration = get_object_or_404(ProjectIntegration, id=integration_id, project=project)

    if request.method == "POST":
        credential_source = request.POST.get("credential_source", "account")
        external_id = request.POST.get("external_id", "").strip()
        is_enabled = request.POST.get("is_enabled") == "on"
        notes = request.POST.get("notes", "").strip()

        integration.credential_source = credential_source
        integration.external_id = external_id
        integration.is_enabled = is_enabled
        integration.notes = notes
        integration.save()

        messages.success(request, f"Integration with {integration.system.display_name} updated")
        return redirect("projects:integrations", slug=slug)

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "project": project,
        "integration": integration,
        "active_tab": "integrations",
    }

    return render(request, "mcp/project_integration_form.html", context)


@login_required
@require_POST
def project_integration_remove_view(request, slug, integration_id):
    """Remove a project integration (slug-based)."""
    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        return JsonResponse({"error": "Admin access required"}, status=403)

    integration = get_object_or_404(ProjectIntegration, id=integration_id, project=project)

    system_name = integration.system.display_name
    integration.delete()

    return JsonResponse({"success": True, "message": f"Integration with {system_name} removed"})


# ============================================================================
# Project-scoped API Keys
# ============================================================================


@login_required
def project_api_keys_view(request, slug):
    """API keys for a specific project."""
    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "No active account")
        return redirect("index")

    api_keys = MCPApiKey.objects.filter(project=project).select_related("created_by")

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "project": project,
        "api_keys": api_keys,
        "active_tab": "api_keys",
    }

    return render(request, "mcp/project_api_keys.html", context)


# ============================================================================
# Project-scoped Tools
# ============================================================================


def _sanitize_tool_name(name):
    """Sanitize tool name to be MCP-compliant."""
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    name = name.lower()
    return name


@login_required
def project_tools_view(request, slug):
    """Tools available for a specific project (from its integrations)."""
    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "No active account")
        return redirect("index")

    integrations = ProjectIntegration.objects.filter(project=project, is_enabled=True).select_related("system")

    from apps.systems.models import Action

    tool_groups = []
    for integration in integrations:
        system = integration.system
        actions = Action.objects.filter(
            resource__interface__system=system,
            is_mcp_enabled=True,
            resource__interface__system__is_active=True,
        ).select_related("resource__interface__system")

        tools = []
        for action in actions:
            resource = action.resource
            interface = resource.interface
            tool_name = f"{system.alias}_{resource.alias or resource.name}_{action.alias or action.name}"
            tool_name = _sanitize_tool_name(tool_name)

            method = action.method.upper()
            interface_type = interface.type.upper()
            if interface_type == "GRAPHQL":
                action_name_lower = (action.alias or action.name).lower()
                if any(
                    prefix in action_name_lower
                    for prefix in ["create", "update", "delete", "add", "remove", "set", "mutate"]
                ):
                    tool_type = "system_write"
                else:
                    tool_type = "system_read"
            elif method in ("GET", "HEAD", "OPTIONS"):
                tool_type = "system_read"
            else:
                tool_type = "system_write"

            description = action.description or f"{action.name} on {system.display_name} {resource.name}"
            tools.append(
                {
                    "name": tool_name,
                    "description": description[:200],
                    "tool_type": tool_type,
                }
            )

        if tools:
            tool_groups.append(
                {
                    "system": system.display_name,
                    "system_alias": system.alias,
                    "tools": tools,
                }
            )

    total_tools = sum(len(g["tools"]) for g in tool_groups)

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "project": project,
        "tool_groups": tool_groups,
        "total_tools": total_tools,
        "active_tab": "tools",
    }

    return render(request, "mcp/project_tools.html", context)


# ============================================================================
# Project-scoped Logs
# ============================================================================


@login_required
def project_logs_view(request, slug):
    """Audit logs for a specific project's API keys."""
    active_account, project = _get_project_for_account(request, slug)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "No active account")
        return redirect("index")

    # Filter logs by account (MCPAuditLog doesn't have a direct project FK)
    logs = MCPAuditLog.objects.filter(account=active_account).order_by("-timestamp")

    # Apply filters
    tool_name = request.GET.get("tool_name", "")
    success = request.GET.get("success", "")

    if tool_name:
        logs = logs.filter(tool_name__icontains=tool_name)
    if success == "true":
        logs = logs.filter(success=True)
    elif success == "false":
        logs = logs.filter(success=False)

    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "project": project,
        "page_obj": page_obj,
        "filter_tool_name": tool_name,
        "filter_success": success,
        "active_tab": "logs",
    }

    return render(request, "mcp/project_logs.html", context)
