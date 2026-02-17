"""
Django Admin configuration for MCP models.
"""

import fnmatch

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html

from apps.mcp.categories import ToolCategoryResolver
from apps.mcp.models import (
    AgentPolicy,
    AgentProfile,
    ErrorDiagnostic,
    MCPApiKey,
    MCPAuditLog,
    MCPSession,
    Project,
    ProjectIntegration,
    ProjectMapping,
    ProjectPolicy,
    ToolCategory,
    ToolCategoryMapping,
    UserPolicy,
)


@admin.register(MCPAuditLog)
class MCPAuditLogAdmin(admin.ModelAdmin):
    """Admin for MCP audit logs."""

    list_display = [
        "timestamp",
        "account",
        "tool_name",
        "tool_type",
        "success_badge",
        "duration_ms",
        "mode",
        "transport",
    ]
    list_filter = ["success", "tool_type", "mode", "transport", "timestamp", "account"]
    search_fields = ["tool_name", "session_id", "error_message"]
    readonly_fields = [
        "account",
        "user",
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
    ordering = ["-timestamp"]
    date_hierarchy = "timestamp"

    def success_badge(self, obj):
        if obj.success:
            return format_html('<span style="color: green; font-weight: bold;">✓</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗</span>')

    success_badge.short_description = "OK"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow superusers to delete old logs
        return request.user.is_superuser


@admin.register(MCPSession)
class MCPSessionAdmin(admin.ModelAdmin):
    """Admin for MCP sessions."""

    list_display = [
        "session_id_short",
        "account",
        "user",
        "mode",
        "transport",
        "is_active",
        "tool_calls_count",
        "last_activity",
    ]
    list_filter = ["is_active", "mode", "transport", "account"]
    search_fields = ["session_id", "user__username"]
    readonly_fields = ["session_id", "created_at", "last_activity", "tool_calls_count"]
    ordering = ["-last_activity"]

    def session_id_short(self, obj):
        return f"{obj.session_id[:16]}..."

    session_id_short.short_description = "Session ID"

    actions = ["deactivate_sessions"]

    @admin.action(description="Deactivate selected sessions")
    def deactivate_sessions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} sessions deactivated.")


@admin.register(MCPApiKey)
class MCPApiKeyAdmin(admin.ModelAdmin):
    """Admin for MCP API keys."""

    list_display = [
        "name",
        "account",
        "key_prefix",
        "project_link",
        "is_admin_badge",
        "mode",
        "is_active",
        "last_used_at",
        "expires_status",
        "created_at",
    ]
    list_filter = ["is_active", "is_admin", "mode", "project", "account"]
    search_fields = ["name", "key_prefix", "project__slug", "project__name"]
    readonly_fields = ["key_prefix", "key_hash", "created_at", "last_used_at"]
    ordering = ["-created_at"]
    autocomplete_fields = ["project", "profile"]

    fieldsets = (
        (None, {"fields": ("name", "account", "created_by")}),
        (
            "Key Info",
            {"fields": ("key_prefix", "key_hash"), "description": "The full API key is only shown once when created."},
        ),
        (
            "Project Binding",
            {
                "fields": ("project", "is_admin"),
                "description": "Bind token to a project. Admin tokens are for management only.",
            },
        ),
        ("Permissions", {"fields": ("profile", "mode", "allowed_tools", "blocked_tools")}),
        ("Status", {"fields": ("is_active", "expires_at", "last_used_at", "created_at")}),
    )

    def project_link(self, obj):
        if obj.project:
            return format_html('<a href="/admin/mcp/project/{}/change/">{}</a>', obj.project.id, obj.project.slug)
        return format_html('<span style="color: gray;">—</span>')

    project_link.short_description = "Project"

    def is_admin_badge(self, obj):
        if obj.is_admin:
            return format_html('<span style="color: orange; font-weight: bold;">Admin</span>')
        return format_html('<span style="color: gray;">—</span>')

    is_admin_badge.short_description = "Admin"

    def expires_status(self, obj):
        if not obj.expires_at:
            return format_html('<span style="color: gray;">Never</span>')
        if obj.expires_at < timezone.now():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Valid</span>')

    expires_status.short_description = "Expires"

    actions = ["deactivate_keys", "activate_keys"]

    @admin.action(description="Deactivate selected API keys")
    def deactivate_keys(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} API keys deactivated.")

    @admin.action(description="Activate selected API keys")
    def activate_keys(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} API keys activated.")


class ProjectMappingInline(admin.TabularInline):
    """Inline admin for project mappings."""

    model = ProjectMapping
    extra = 1
    fields = ["system_alias", "external_id", "config"]


class ProjectIntegrationInline(admin.TabularInline):
    """Inline admin for project integrations."""

    model = ProjectIntegration
    extra = 0
    fields = ["system", "credential_source", "external_id", "is_enabled", "notes"]
    autocomplete_fields = ["system"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for MCP Projects."""

    list_display = [
        "name",
        "slug",
        "account",
        "mapping_summary",
        "category_restriction",
        "api_key_count",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "account"]
    search_fields = ["name", "slug", "description", "external_mappings"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProjectIntegrationInline, ProjectMappingInline]

    fieldsets = (
        (None, {"fields": ("account", "name", "slug", "description")}),
        (
            "External System Mappings",
            {
                "fields": ("external_mappings",),
                "description": 'JSON mapping of system aliases to external IDs. Example: {"jira": "PROJ-123", "github": "org/repo"}',
            },
        ),
        (
            "Access Control",
            {
                "fields": ("allowed_categories",),
                "description": "Optional list of allowed category keys. Null = no restriction.",
            },
        ),
        ("Status", {"fields": ("is_active", "created_at", "updated_at")}),
    )

    def mapping_summary(self, obj):
        if not obj.external_mappings:
            return format_html('<span style="color: gray;">None</span>')
        systems = list(obj.external_mappings.keys())
        if len(systems) <= 3:
            return ", ".join(systems)
        return f"{', '.join(systems[:3])}... (+{len(systems) - 3})"

    mapping_summary.short_description = "Systems"

    def category_restriction(self, obj):
        if obj.allowed_categories is None:
            return format_html('<span style="color: gray;">No restriction</span>')
        if not obj.allowed_categories:
            return format_html('<span style="color: red;">None allowed</span>')
        return f"{len(obj.allowed_categories)} categories"

    category_restriction.short_description = "Categories"

    def api_key_count(self, obj):
        count = obj.api_keys.count()
        if count == 0:
            return format_html('<span style="color: gray;">0</span>')
        return count

    api_key_count.short_description = "API Keys"


@admin.register(ProjectMapping)
class ProjectMappingAdmin(admin.ModelAdmin):
    """Admin for detailed project mappings."""

    list_display = ["project", "system_alias", "external_id", "has_config", "created_at"]
    list_filter = ["system_alias", "project__account"]
    search_fields = ["project__name", "project__slug", "system_alias", "external_id"]
    readonly_fields = ["created_at"]
    ordering = ["project__name", "system_alias"]
    autocomplete_fields = ["project"]

    def has_config(self, obj):
        if obj.config:
            return format_html('<span style="color: green;">Yes</span>')
        return format_html('<span style="color: gray;">—</span>')

    has_config.short_description = "Config"


@admin.register(ProjectIntegration)
class ProjectIntegrationAdmin(admin.ModelAdmin):
    """Admin for project integrations."""

    list_display = [
        "project",
        "system",
        "credential_source",
        "external_id_short",
        "is_enabled",
        "created_at",
    ]
    list_filter = [
        "is_enabled",
        "credential_source",
        "project__account",
    ]
    search_fields = [
        "project__name",
        "project__slug",
        "system__alias",
        "system__display_name",
        "external_id",
    ]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["project__name", "system__alias"]
    autocomplete_fields = ["project", "system"]

    fieldsets = (
        (None, {"fields": ("project", "system")}),
        ("Configuration", {"fields": ("credential_source", "external_id", "is_enabled", "custom_config", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def external_id_short(self, obj):
        if not obj.external_id:
            return format_html('<span style="color: gray;">-</span>')
        text = obj.external_id
        if len(text) > 40:
            return text[:37] + "..."
        return text

    external_id_short.short_description = "External ID"


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    """Admin for agent profiles."""

    list_display = ["name", "account", "mode", "category_count", "api_key_count", "is_active", "created_at"]
    list_filter = ["is_active", "mode", "account"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["name"]
    filter_horizontal = ["allowed_categories"]

    fieldsets = (
        (None, {"fields": ("account", "name", "description")}),
        ("Permissions", {"fields": ("mode", "allowed_categories", "include_tools", "exclude_tools")}),
        ("Status", {"fields": ("is_active", "created_at", "updated_at")}),
    )

    def category_count(self, obj):
        count = obj.allowed_categories.count()
        if count == 0:
            return format_html('<span style="color: green;">All</span>')
        return count

    category_count.short_description = "Categories"

    def api_key_count(self, obj):
        return obj.api_keys.count()

    api_key_count.short_description = "API Keys"


@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    """Admin for tool categories."""

    list_display = ["key", "name", "account", "risk_level_badge", "is_global", "mapping_count", "created_at"]
    list_filter = ["risk_level", "is_global", "account"]
    search_fields = ["key", "name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["key"]

    fieldsets = (
        (None, {"fields": ("account", "key", "name", "description")}),
        ("Settings", {"fields": ("risk_level", "is_global")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def risk_level_badge(self, obj):
        colors = {"low": "green", "medium": "orange", "high": "red"}
        color = colors.get(obj.risk_level, "gray")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_risk_level_display())

    risk_level_badge.short_description = "Risk Level"

    def mapping_count(self, obj):
        return obj.mappings.count()

    mapping_count.short_description = "Mappings"


@admin.register(ToolCategoryMapping)
class ToolCategoryMappingAdmin(admin.ModelAdmin):
    """Admin for tool category mappings."""

    list_display = ["tool_key_pattern", "category", "account", "is_auto", "created_at"]
    list_filter = ["is_auto", "category", "account"]
    search_fields = ["tool_key_pattern", "category__key", "category__name"]
    readonly_fields = ["created_at"]
    ordering = ["tool_key_pattern"]
    autocomplete_fields = ["category"]


@admin.register(AgentPolicy)
class AgentPolicyAdmin(admin.ModelAdmin):
    """Admin for agent policies."""

    list_display = ["api_key", "name", "account", "category_count", "created_at", "updated_at"]
    list_filter = ["account"]
    search_fields = ["name", "api_key__name", "api_key__key_prefix"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    autocomplete_fields = ["api_key"]

    def category_count(self, obj):
        cats = obj.allowed_categories or []
        if not cats:
            return format_html('<span style="color: green;">All</span>')
        return len(cats)

    category_count.short_description = "Categories"


@admin.register(ProjectPolicy)
class ProjectPolicyAdmin(admin.ModelAdmin):
    """Admin for project policies."""

    list_display = ["project_identifier", "name", "account", "is_active", "category_restriction", "created_at"]
    list_filter = ["is_active", "account"]
    search_fields = ["project_identifier", "name"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["project_identifier"]

    def category_restriction(self, obj):
        if obj.allowed_categories is None:
            return format_html('<span style="color: gray;">No restriction</span>')
        if not obj.allowed_categories:
            return format_html('<span style="color: green;">All</span>')
        return f"{len(obj.allowed_categories)} categories"

    category_restriction.short_description = "Categories"


@admin.register(UserPolicy)
class UserPolicyAdmin(admin.ModelAdmin):
    """Admin for user policies."""

    list_display = ["user", "account", "is_active", "category_restriction", "created_at", "updated_at"]
    list_filter = ["is_active", "account"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    autocomplete_fields = ["user"]

    def category_restriction(self, obj):
        if obj.allowed_categories is None:
            return format_html('<span style="color: gray;">No restriction</span>')
        if not obj.allowed_categories:
            return format_html('<span style="color: green;">All</span>')
        return f"{len(obj.allowed_categories)} categories"

    category_restriction.short_description = "Categories"


@admin.register(ErrorDiagnostic)
class ErrorDiagnosticAdmin(admin.ModelAdmin):
    """Admin for error diagnostics."""

    list_display = [
        "created_at",
        "system_alias",
        "category_badge",
        "severity_badge",
        "summary_short",
        "status_badge",
        "occurrence_count",
        "has_fix_badge",
    ]
    list_filter = [
        "status",
        "category",
        "severity",
        "system_alias",
        "has_fix",
        "account",
    ]
    search_fields = [
        "system_alias",
        "tool_name",
        "error_message",
        "diagnosis_summary",
    ]
    readonly_fields = [
        "account",
        "system_alias",
        "tool_name",
        "action_name",
        "status_code",
        "error_message",
        "error_data",
        "category",
        "severity",
        "diagnosis_summary",
        "diagnosis_detail",
        "has_fix",
        "fix_description",
        "fix_action",
        "occurrence_count",
        "first_seen_at",
        "last_seen_at",
        "created_at",
    ]
    ordering = ["-last_seen_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Error",
            {
                "fields": (
                    "account",
                    "system_alias",
                    "tool_name",
                    "action_name",
                    "status_code",
                    "error_message",
                    "error_data",
                )
            },
        ),
        (
            "Diagnosis",
            {
                "fields": (
                    "category",
                    "severity",
                    "diagnosis_summary",
                    "diagnosis_detail",
                )
            },
        ),
        (
            "Fix Suggestion",
            {
                "fields": ("has_fix", "fix_description", "fix_action"),
            },
        ),
        (
            "Review",
            {
                "fields": ("status", "review_notes", "reviewed_at"),
            },
        ),
        (
            "Occurrence",
            {
                "fields": ("occurrence_count", "first_seen_at", "last_seen_at", "created_at"),
            },
        ),
    )

    def summary_short(self, obj):
        text = obj.diagnosis_summary or ""
        if len(text) > 80:
            return text[:77] + "..."
        return text

    summary_short.short_description = "Summary"

    def category_badge(self, obj):
        colors = {
            "auth_expired": "red",
            "auth_invalid": "red",
            "auth_permissions": "red",
            "rate_limit": "orange",
            "server_error": "purple",
            "timeout": "orange",
            "connection": "orange",
            "not_found_mapping": "#c90",
            "not_found_path": "#c90",
            "validation_missing": "blue",
            "validation_type": "blue",
        }
        color = colors.get(obj.category, "gray")
        return format_html('<span style="color: {};">{}</span>', color, obj.category)

    category_badge.short_description = "Category"

    def severity_badge(self, obj):
        colors = {"low": "green", "medium": "orange", "high": "red", "critical": "darkred"}
        color = colors.get(obj.severity, "gray")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.severity.upper())

    severity_badge.short_description = "Severity"

    def status_badge(self, obj):
        colors = {
            "pending": "orange",
            "approved": "green",
            "dismissed": "gray",
            "applied": "blue",
            "expired": "lightgray",
        }
        color = colors.get(obj.status, "gray")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.status)

    status_badge.short_description = "Status"

    def has_fix_badge(self, obj):
        if obj.has_fix:
            return format_html('<span style="color: green; font-weight: bold;">Yes</span>')
        return format_html('<span style="color: gray;">—</span>')

    has_fix_badge.short_description = "Fix?"

    def has_add_permission(self, request):
        return False

    actions = ["approve_diagnostics", "dismiss_diagnostics"]

    @admin.action(description="Approve selected diagnostics")
    def approve_diagnostics(self, request, queryset):
        updated = queryset.filter(status="pending").update(status="approved", reviewed_at=timezone.now())
        self.message_user(request, f"{updated} diagnostics approved.")

    @admin.action(description="Dismiss selected diagnostics")
    def dismiss_diagnostics(self, request, queryset):
        updated = queryset.filter(status="pending").update(status="dismissed", reviewed_at=timezone.now())
        self.message_user(request, f"{updated} diagnostics dismissed.")


def category_debug_view(request):
    """
    Admin view for debugging category resolution.
    Accessible at /admin/mcp/category-debug/
    """
    from django.contrib.admin.sites import site

    from apps.accounts.models import Account

    context = dict(site.each_context(request))

    # Get account from request or first available
    account = getattr(request, "account", None)
    if not account:
        account = Account.objects.first()

    if not account:
        context["error"] = "No account found"
        return render(request, "admin/mcp/category_debug.html", context)

    # Get parameters
    api_key_id = request.GET.get("api_key_id")
    project_identifier = request.GET.get("project_identifier", "")
    user_id = request.GET.get("user_id")

    # Convert to int if provided
    if api_key_id:
        try:
            api_key_id = int(api_key_id)
        except ValueError:
            api_key_id = None

    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            user_id = None

    # Get all API keys, projects, users for dropdowns
    context["api_keys"] = MCPApiKey.objects.filter(account=account, is_active=True)
    context["project_policies"] = ProjectPolicy.objects.filter(account=account, is_active=True)
    context["user_policies"] = UserPolicy.objects.filter(account=account, is_active=True).select_related("user")

    # Selected values
    context["selected_api_key_id"] = api_key_id
    context["selected_project"] = project_identifier
    context["selected_user_id"] = user_id

    # Get categories and mappings
    context["categories"] = ToolCategory.objects.filter(account=account)
    context["mappings"] = ToolCategoryMapping.objects.filter(account=account).select_related("category")

    # Get policies if selected
    context["agent_policy"] = None
    context["project_policy"] = None
    context["user_policy"] = None

    if api_key_id:
        try:
            context["agent_policy"] = AgentPolicy.objects.get(account=account, api_key_id=api_key_id)
        except AgentPolicy.DoesNotExist:
            pass

    if project_identifier:
        try:
            context["project_policy"] = ProjectPolicy.objects.get(
                account=account, project_identifier=project_identifier, is_active=True
            )
        except ProjectPolicy.DoesNotExist:
            # Try pattern match
            for p in ProjectPolicy.objects.filter(account=account, is_active=True):
                if fnmatch.fnmatch(project_identifier, p.project_identifier):
                    context["project_policy"] = p
                    context["project_policy_matched"] = True
                    break

    if user_id:
        try:
            context["user_policy"] = UserPolicy.objects.get(account=account, user_id=user_id, is_active=True)
        except UserPolicy.DoesNotExist:
            pass

    # Resolve effective categories
    resolver = ToolCategoryResolver(
        account_id=account.id,
        api_key_id=api_key_id,
        project_identifier=project_identifier if project_identifier else None,
        user_id=user_id,
    )
    result = resolver.get_effective_categories()

    context["resolution"] = {
        "effective_categories": list(result.effective_categories) if result.effective_categories else None,
        "is_restricted": result.is_restricted,
        "all_allowed": result.all_allowed,
    }

    # Test sample tools
    sample_tools = [
        "salesforce_contact_list",
        "salesforce_contact_get",
        "salesforce_contact_create",
        "salesforce_contact_delete",
        "hubspot_deal_list",
        "hubspot_deal_create",
    ]
    tool_access = []
    for tool in sample_tools:
        tool_cats = resolver.get_tool_categories(tool)
        is_allowed = resolver.is_tool_allowed(tool)
        tool_access.append(
            {
                "name": tool,
                "categories": tool_cats,
                "allowed": is_allowed,
            }
        )
    context["tool_access"] = tool_access

    context["title"] = "MCP Category Debug"
    context["account"] = account

    return render(request, "admin/mcp/category_debug.html", context)


# Register custom admin URL
_original_get_urls = admin.site.get_urls


def get_urls_with_mcp_debug():
    """Add MCP category debug URL to admin."""
    custom_urls = [
        path("mcp/category-debug/", staff_member_required(category_debug_view), name="mcp-category-debug"),
    ]
    return custom_urls + _original_get_urls()


admin.site.get_urls = get_urls_with_mcp_debug
