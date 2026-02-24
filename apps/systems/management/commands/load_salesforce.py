"""
Management command to load the Salesforce system definition.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load the Salesforce system definition from fixture"

    def handle(self, *args, **options):
        self.stdout.write("Loading Salesforce system definition...")

        try:
            call_command("loaddata", "apps/systems/fixtures/salesforce.json", verbosity=1)
            self.stdout.write(self.style.SUCCESS("Successfully loaded Salesforce system!"))
            self.stdout.write("")
            self.stdout.write("The Salesforce adapter includes:")
            self.stdout.write("  - System: Salesforce CRM")
            self.stdout.write("  - Interface: REST API (v59.0)")
            self.stdout.write("  - Resources: Account, Contact, Lead, Opportunity, Case, Task")
            self.stdout.write("  - Actions: list, get, create, update, delete")
            self.stdout.write("")
            self.stdout.write("Next steps:")
            self.stdout.write("  1. Go to Systems page in the UI")
            self.stdout.write("  2. Configure Salesforce credentials")
            self.stdout.write("  3. Use Salesforce actions via MCP tools")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading Salesforce: {e}"))
