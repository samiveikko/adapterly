from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html

from .models import (
    AccountSystem,
    Action,
    AuthenticationStep,
    EntityMapping,
    EntityType,
    Interface,
    Resource,
    System,
    SystemEntityIdentifier,
)


@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    list_display = ["display_name", "alias", "system_type", "is_active", "schema_digest_short", "created_at"]
    list_filter = ["system_type", "is_active"]
    search_fields = ["name", "alias", "display_name"]
    actions = ["refresh_from_openapi"]

    @admin.display(description="Schema digest")
    def schema_digest_short(self, obj):
        return obj.schema_digest[:12] if obj.schema_digest else "-"

    @admin.action(description="Refresh adapter from OpenAPI spec")
    def refresh_from_openapi(self, request, queryset):
        from apps.systems.refresh import refresh_adapter

        for system in queryset:
            url = (system.meta or {}).get("openapi_spec_url")
            if not url:
                self.message_user(
                    request,
                    f"{system.alias}: skipped — no meta.openapi_spec_url",
                    level="error",
                )
                continue

            try:
                result = refresh_adapter(system)
            except Exception as exc:
                self.message_user(request, f"{system.alias}: {exc}", level="error")
                continue

            if not result.spec_changed:
                self.message_user(request, f"{system.alias}: no changes (spec unchanged)")
            else:
                self.message_user(
                    request,
                    f"{system.alias}: +{len(result.new_actions)} new, "
                    f"~{len(result.updated_actions)} updated, "
                    f"={len(result.unchanged_actions)} unchanged, "
                    f"-{len(result.removed_actions)} removed",
                )


@admin.register(Interface)
class InterfaceAdmin(admin.ModelAdmin):
    list_display = ["__str__", "system", "type", "requires_browser"]
    list_filter = ["type", "requires_browser"]
    search_fields = ["name", "alias", "system__name"]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ["name", "alias", "interface"]
    search_fields = ["name", "alias"]


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ["name", "alias", "resource", "method"]
    list_filter = ["method"]
    search_fields = ["name", "alias"]


@admin.register(AuthenticationStep)
class AuthenticationStepAdmin(admin.ModelAdmin):
    list_display = ["system", "step_order", "step_type", "step_name", "is_required"]
    list_filter = ["step_type", "is_required"]


@admin.register(AccountSystem)
class AccountSystemAdmin(admin.ModelAdmin):
    list_display = ["account", "system", "project_scope", "is_enabled", "is_verified", "last_verified_at"]
    list_filter = ["is_enabled", "is_verified", "project"]
    search_fields = ["account__name", "system__name", "project__slug"]
    autocomplete_fields = ["project"]

    def project_scope(self, obj):
        if obj.project:
            return format_html('<span style="color: blue;">{}</span>', obj.project.slug)
        return format_html('<span style="color: gray;">shared</span>')

    project_scope.short_description = "Scope"


@admin.register(EntityType)
class EntityTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "display_name", "icon", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "display_name"]


class SystemEntityIdentifierInline(admin.TabularInline):
    model = SystemEntityIdentifier
    extra = 1


@admin.register(EntityMapping)
class EntityMappingAdmin(admin.ModelAdmin):
    list_display = ["canonical_name", "entity_type", "account", "is_active", "created_at"]
    list_filter = ["entity_type", "is_active", "account"]
    search_fields = ["canonical_name", "canonical_id", "description"]
    inlines = [SystemEntityIdentifierInline]


@admin.register(SystemEntityIdentifier)
class SystemEntityIdentifierAdmin(admin.ModelAdmin):
    list_display = ["mapping", "system", "identifier_value", "resource_hint", "is_primary"]
    list_filter = ["system", "is_primary"]
    search_fields = ["identifier_value", "mapping__canonical_name"]


# ---------------------------------------------------------------------------
# Custom admin view: Pending adapter refreshes
# ---------------------------------------------------------------------------


def pending_refreshes_view(request):
    """
    Admin view showing systems whose OpenAPI spec has changed (digest mismatch).

    GET:  Render table of pending systems.
    POST: Either apply refresh for a single system or check all systems.
    """
    from django.contrib import messages
    from django.contrib.admin.sites import site

    from apps.systems.refresh import check_for_updates, refresh_adapter

    context = dict(site.each_context(request))
    context["title"] = "Pending Adapter Refreshes"

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "apply" and request.POST.get("system_id"):
            system_id = request.POST["system_id"]
            try:
                system = System.objects.get(pk=system_id)
                result = refresh_adapter(system)
                # Clear pending flag
                system.refresh_from_db(fields=["meta"])
                system.meta["refresh_pending"] = False
                system.meta.pop("refresh_pending_digest", None)
                system.save(update_fields=["meta"])

                if not result.spec_changed:
                    messages.info(request, f"{system.alias}: no changes (spec unchanged)")
                else:
                    messages.success(
                        request,
                        f"{system.alias}: +{len(result.new_actions)} new, "
                        f"~{len(result.updated_actions)} updated, "
                        f"={len(result.unchanged_actions)} unchanged, "
                        f"-{len(result.removed_actions)} removed",
                    )
            except System.DoesNotExist:
                messages.error(request, "System not found.")
            except Exception as exc:
                messages.error(request, f"Error applying refresh: {exc}")

        elif action == "check_all":
            systems = System.objects.filter(
                meta__openapi_spec_url__isnull=False,
            ).exclude(meta__openapi_spec_url="")
            checked = 0
            pending = 0
            for system in systems:
                try:
                    if check_for_updates(system):
                        pending += 1
                    checked += 1
                except Exception as exc:
                    messages.error(request, f"{system.alias}: {exc}")
            messages.info(request, f"Checked {checked} system(s), {pending} with pending updates.")

        return redirect("admin:systems-pending-refreshes")

    # GET — gather pending systems
    pending_systems = System.objects.filter(meta__refresh_pending=True)
    # Also gather all systems with spec URL for the "check all" button
    has_spec_url = (
        System.objects.filter(
            meta__openapi_spec_url__isnull=False,
        )
        .exclude(meta__openapi_spec_url="")
        .exists()
    )

    context["pending_systems"] = pending_systems
    context["has_spec_url"] = has_spec_url
    return render(request, "admin/systems/pending_refreshes.html", context)


# Register custom admin URL (monkey-patch pattern from mcp/admin.py)
_original_get_urls_systems = admin.site.get_urls


def _get_urls_with_pending_refreshes():
    custom_urls = [
        path(
            "systems/pending-refreshes/",
            staff_member_required(pending_refreshes_view),
            name="systems-pending-refreshes",
        ),
    ]
    return custom_urls + _original_get_urls_systems()


admin.site.get_urls = _get_urls_with_pending_refreshes
