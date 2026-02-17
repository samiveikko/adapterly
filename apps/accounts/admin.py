from django.contrib import admin

from .models import Account, AccountUser, UserInvitation


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]


@admin.register(AccountUser)
class AccountUserAdmin(admin.ModelAdmin):
    list_display = ["account", "user", "is_admin", "is_current_active", "created_at"]
    list_filter = ["is_admin", "is_current_active", "created_at", "account"]
    search_fields = ["account__name", "user__username", "user__email"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
    list_select_related = ["account", "user"]


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "account", "invited_by", "is_admin", "is_used", "created_at", "expires_at_days"]
    list_filter = ["is_admin", "is_used", "created_at", "account"]
    search_fields = ["email", "account__name", "invited_by__username"]
    readonly_fields = ["token", "created_at"]
    ordering = ["-created_at"]
    list_select_related = ["account", "invited_by"]

    fieldsets = (
        ("Perustiedot", {"fields": ("email", "account", "invited_by", "is_admin")}),
        ("Kutsu", {"fields": ("token", "is_used", "expires_at_days"), "classes": ("collapse",)}),
        ("Ajat", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
