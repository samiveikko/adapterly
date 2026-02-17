"""
Data migration:
1. Create a default project for each account that has no projects
2. Set default_project on each account
3. Create ProjectIntegration records from existing AccountSystem records
"""

from django.db import migrations
from django.utils.text import slugify


def create_default_projects_and_integrations(apps, schema_editor):
    """
    For each account:
    - If no projects exist, create a "Default" project
    - Set account.default_project to the first project
    - Create ProjectIntegration from existing AccountSystem records
    """
    Account = apps.get_model('accounts', 'Account')
    Project = apps.get_model('mcp', 'Project')
    ProjectIntegration = apps.get_model('mcp', 'ProjectIntegration')
    AccountSystem = apps.get_model('systems', 'AccountSystem')

    for account in Account.objects.all():
        # Ensure at least one project exists
        project = Project.objects.filter(account=account).first()
        if not project:
            project = Project.objects.create(
                account=account,
                name='Default',
                slug='default',
                description='Default project (auto-created)',
                is_active=True,
            )

        # Set default_project
        if not account.default_project_id:
            account.default_project_id = project.id
            account.save(update_fields=['default_project_id'])

        # Create ProjectIntegration from existing AccountSystem records
        account_systems = AccountSystem.objects.filter(
            account=account,
            is_enabled=True,
        )
        for accsys in account_systems:
            target_project = project
            if accsys.project_id:
                # Project-specific credential → use that project
                target_project_obj = Project.objects.filter(id=accsys.project_id).first()
                if target_project_obj:
                    target_project = target_project_obj

            # Determine credential source
            credential_source = 'project' if accsys.project_id else 'account'

            # Get external_id from project's external_mappings if available
            external_id = ''
            if target_project.external_mappings and isinstance(target_project.external_mappings, dict):
                # Try to find system alias
                from django.apps import apps as django_apps
                try:
                    System = django_apps.get_model('systems', 'System')
                    system = System.objects.filter(id=accsys.system_id).first()
                    if system and system.alias in target_project.external_mappings:
                        external_id = target_project.external_mappings[system.alias]
                except Exception:
                    pass

            # Create integration (skip duplicates)
            ProjectIntegration.objects.get_or_create(
                project=target_project,
                system_id=accsys.system_id,
                defaults={
                    'credential_source': credential_source,
                    'external_id': external_id or '',
                    'is_enabled': True,
                }
            )


def reverse_migration(apps, schema_editor):
    """Reverse: delete auto-created integrations and default projects."""
    ProjectIntegration = apps.get_model('mcp', 'ProjectIntegration')
    ProjectIntegration.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('mcp', '0009_add_projectintegration'),
        ('accounts', '0006_add_default_project'),
        ('systems', '0045_accountsystem_project_scoping'),
    ]

    operations = [
        migrations.RunPython(
            create_default_projects_and_integrations,
            reverse_migration,
        ),
    ]
