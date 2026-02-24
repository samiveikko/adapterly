"""
Add pagination configuration to Infrakit Kuura API actions.

Infrakit Kuura API uses:
- page param: 'page' (0-indexed)
- size param: 'size' (not 'pageSize')
- data field: varies by endpoint (e.g. 'logpoints', 'machines') — auto-detected
- last page indicator: 'last' boolean field
- No totalPages/totalElements fields
"""
from django.db import migrations


# Infrakit pagination config
INFRAKIT_PAGINATION = {
    'page_param': 'page',
    'size_param': 'size',
    'default_size': 100,
    'max_size': 100,
    'start_page': 0,  # Infrakit uses 0-indexed pages
    'data_field': None,  # Auto-detect (varies: 'logpoints', 'machines', etc.)
    'total_pages_field': 'totalPages',
    'total_elements_field': 'totalElements',
    'last_page_field': 'last',
    'max_pages': 100
}

# Actions that return paginated lists
PAGINATED_ACTIONS = [
    ('projects', 'list'),
    ('organization', 'get_projects'),
    ('folders', 'get_documents'),
    ('folders', 'get_models'),
    ('folders', 'get_images'),
    ('models', 'get_changed'),
    ('logpoints', 'list'),
    ('masshaul', 'get_trips'),
    ('masshaul', 'get_truck_tasks'),
    ('equipment', 'list'),
]


def add_pagination_config(apps, schema_editor):
    Action = apps.get_model('systems', 'Action')

    for resource_alias, action_alias in PAGINATED_ACTIONS:
        actions = Action.objects.filter(
            resource__interface__alias='kuura',
            resource__alias=resource_alias,
            alias=action_alias
        )
        updated = actions.update(pagination=INFRAKIT_PAGINATION)
        if updated:
            print(f"  Added pagination to {resource_alias}.{action_alias}")


def remove_pagination_config(apps, schema_editor):
    Action = apps.get_model('systems', 'Action')

    for resource_alias, action_alias in PAGINATED_ACTIONS:
        Action.objects.filter(
            resource__interface__alias='kuura',
            resource__alias=resource_alias,
            alias=action_alias
        ).update(pagination={})


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0021_infrakit_full_api'),
    ]

    operations = [
        migrations.RunPython(add_pagination_config, remove_pagination_config),
    ]
