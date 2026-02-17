# Generated manually

from django.db import migrations


def update_system_aliases(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    
    # Update existing systems to use correct aliases
    alias_mapping = {
        'jira': 'jira',
        'slack': 'slack', 
        'github': 'github',
        'jenkins': 'jenkins',
        'infrakit': 'infrakit',
    }
    
    for system in System.objects.all():
        if system.name in alias_mapping:
            system.alias = alias_mapping[system.name]
            system.save()


def reverse_update_system_aliases(apps, schema_editor):
    # Ei tarvitse reverse-toimintoa
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0007_add_system_alias_nullable'),
    ]

    operations = [
        migrations.RunPython(update_system_aliases, reverse_update_system_aliases),
    ]
