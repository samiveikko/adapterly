"""
Management command to sync tool categories.

Creates default categories and auto-maps existing tools to categories
based on tool_type and system.
"""

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Account
from apps.mcp.models import ToolCategory, ToolCategoryMapping

# Default categories to create
DEFAULT_CATEGORIES = [
    {
        "key": "system.read",
        "name": "System Read",
        "description": "Read-only access to external system data",
        "risk_level": "low",
    },
    {
        "key": "system.write",
        "name": "System Write",
        "description": "Write access to external system data",
        "risk_level": "medium",
    },
    {
        "key": "admin",
        "name": "Administration",
        "description": "Administrative operations and configuration changes",
        "risk_level": "high",
    },
]


# Default tool mappings (pattern -> category key)
DEFAULT_MAPPINGS = [
    # System tools - read operations (patterns)
    ("*_list", "system.read"),
    ("*_get", "system.read"),
    ("*_read", "system.read"),
    ("*_search", "system.read"),
    ("*_query", "system.read"),
    ("*_fetch", "system.read"),
    ("*_view", "system.read"),
    # System tools - write operations (patterns)
    ("*_create", "system.write"),
    ("*_update", "system.write"),
    ("*_delete", "system.write"),
    ("*_add", "system.write"),
    ("*_remove", "system.write"),
    ("*_modify", "system.write"),
    ("*_edit", "system.write"),
    ("*_set", "system.write"),
    ("*_post", "system.write"),
    ("*_put", "system.write"),
    ("*_patch", "system.write"),
]


class Command(BaseCommand):
    help = "Sync tool categories and create default mappings"

    def add_arguments(self, parser):
        parser.add_argument("--account", type=int, help="Account ID to sync (default: all accounts)")
        parser.add_argument("--create-only", action="store_true", help="Only create categories, do not create mappings")
        parser.add_argument("--force", action="store_true", help="Overwrite existing categories and mappings")

    def handle(self, *args, **options):
        account_id = options.get("account")
        create_only = options.get("create_only", False)
        force = options.get("force", False)

        if account_id:
            try:
                accounts = [Account.objects.get(id=account_id)]
            except Account.DoesNotExist:
                raise CommandError(f"Account {account_id} does not exist")
        else:
            accounts = Account.objects.filter(is_active=True)

        for account in accounts:
            self.stdout.write(f"Processing account: {account.name} (ID: {account.id})")
            self.sync_account(account, create_only, force)

        self.stdout.write(self.style.SUCCESS("Done!"))

    def sync_account(self, account, create_only, force):
        """Sync categories and mappings for a single account."""

        # Create default categories
        categories_created = 0
        categories_updated = 0
        category_map = {}

        for cat_data in DEFAULT_CATEGORIES:
            category, created = ToolCategory.objects.get_or_create(
                account=account,
                key=cat_data["key"],
                defaults={
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "risk_level": cat_data["risk_level"],
                },
            )

            if created:
                categories_created += 1
                self.stdout.write(f"  Created category: {cat_data['key']}")
            elif force:
                category.name = cat_data["name"]
                category.description = cat_data["description"]
                category.risk_level = cat_data["risk_level"]
                category.save()
                categories_updated += 1
                self.stdout.write(f"  Updated category: {cat_data['key']}")

            category_map[cat_data["key"]] = category

        self.stdout.write(f"  Categories: {categories_created} created, {categories_updated} updated")

        if create_only:
            return

        # Create default mappings
        mappings_created = 0
        mappings_skipped = 0

        for pattern, category_key in DEFAULT_MAPPINGS:
            category = category_map.get(category_key)
            if not category:
                self.stdout.write(
                    self.style.WARNING(f"  Skipping mapping {pattern}: category {category_key} not found")
                )
                continue

            mapping, created = ToolCategoryMapping.objects.get_or_create(
                account=account,
                tool_key_pattern=pattern,
                category=category,
                defaults={
                    "is_auto": True,
                },
            )

            if created:
                mappings_created += 1
            else:
                mappings_skipped += 1

        self.stdout.write(f"  Mappings: {mappings_created} created, {mappings_skipped} already existed")
