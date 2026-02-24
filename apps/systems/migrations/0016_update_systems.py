# Generated manually

from django.db import migrations


def update_systems(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    
    # Remove GitHub, Jenkins, Jira
    systems_to_remove = ['github', 'jenkins', 'jira']
    removed_count = System.objects.filter(alias__in=systems_to_remove).delete()[0]
    
    # Add Google Sheets
    google_sheets, created = System.objects.get_or_create(
        alias='google_sheets',
        defaults={
            'name': 'Google Sheets',
            'display_name': 'Google Sheets',
            'description': 'Google Sheets spreadsheet platform for data management and collaboration',
            'system_type': 'storage',
            'icon': 'table',
            'website_url': 'https://sheets.google.com',
            'is_active': True,
            'variables': {},
            'meta': {}
        }
    )
    # Add Power BI
    powerbi, created = System.objects.get_or_create(
        alias='powerbi',
        defaults={
            'name': 'Power BI',
            'display_name': 'Microsoft Power BI',
            'description': 'Business intelligence and data visualization platform',
            'system_type': 'other',
            'icon': 'bar-chart',
            'website_url': 'https://powerbi.microsoft.com',
            'is_active': True,
            'variables': {},
            'meta': {}
        }
    )


def reverse_update_systems(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    
    # Remove Google Sheets and Power BI
    System.objects.filter(alias__in=['google_sheets', 'powerbi']).delete()
    
    # Recreate GitHub, Jenkins, Jira (basic versions)
    System.objects.get_or_create(
        alias='github',
        defaults={
            'name': 'GitHub',
            'display_name': 'GitHub',
            'description': 'Version control and collaboration platform',
            'system_type': 'version_control',
            'icon': 'github',
            'website_url': 'https://github.com',
            'is_active': True
        }
    )
    
    System.objects.get_or_create(
        alias='jenkins',
        defaults={
            'name': 'Jenkins',
            'display_name': 'Jenkins',
            'description': 'Continuous integration and delivery platform',
            'system_type': 'ci_cd',
            'icon': 'gear',
            'website_url': 'https://jenkins.io',
            'is_active': True
        }
    )
    
    System.objects.get_or_create(
        alias='jira',
        defaults={
            'name': 'Jira',
            'display_name': 'Jira',
            'description': 'Project management and issue tracking',
            'system_type': 'project_management',
            'icon': 'kanban',
            'website_url': 'https://atlassian.com/jira',
            'is_active': True
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0015_alter_resource_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(update_systems, reverse_update_systems),
    ]

