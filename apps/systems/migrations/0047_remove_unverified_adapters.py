"""
Remove 9 system adapters that have no verifiable public REST API.

Audit found these systems lack publicly documented REST/Web APIs:
- builderhead: No API — confirmed by multiple sources
- visilean: No API — confirmed by GetApp
- fondion: No public API documentation, only "open interfaces" mention
- sigma: Desktop-only plugin API (Appscript), no REST/cloud API
- admicom_planner: No own API (Admicom Ultima/Estima have one, Planner does not)
- logiapps: No public web presence or API documentation
- takting: API mentioned in marketing but no public documentation
- powerproject: OLE/COM desktop automation only, no REST API
- buildots: No public API, only pre-built partner integrations
"""
from django.db import migrations


ALIASES_TO_REMOVE = [
    'builderhead',
    'visilean',
    'fondion',
    'sigma',
    'admicom_planner',
    'logiapps',
    'takting',
    'powerproject',
    'buildots',
]


def remove_unverified_systems(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    Resource = apps.get_model('systems', 'Resource')

    systems = System.objects.filter(alias__in=ALIASES_TO_REMOVE)
    # Resource → Interface FK is PROTECT, so delete Resources first
    # (Action → Resource is CASCADE, so Actions are deleted automatically)
    Resource.objects.filter(interface__system__in=systems).delete()
    deleted_count, _ = systems.delete()
    print(f"Removed {deleted_count} objects (systems + related interfaces/auth steps)")


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0046_remove_data_mappings'),
    ]

    operations = [
        migrations.RunPython(remove_unverified_systems, migrations.RunPython.noop),
    ]
