# Generated manually - Add Infrakit system

from django.db import migrations


def create_infrakit_system(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    SystemEndpoint = apps.get_model('systems', 'SystemEndpoint')
    
    # Infrakit
    infrakit = System.objects.create(
        name='infrakit',
        display_name='Infrakit',
        description='Infrastructure project management and deployment system',
        system_type='project_management',
        icon='building-gear',
        website_url='https://infrakit.io',
        is_active=True
    )
    
    SystemEndpoint.objects.create(
        system=infrakit,
        name='REST API',
        description='Infrakit REST API for project management',
        base_url='https://api.infrakit.io',
        api_version='v1',
        auth_type='bearer',
        auth_config={'token_type': 'Bearer'},
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
        timeout=30,
        input_schema={
            'project': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'required': True},
                    'description': {'type': 'string'},
                    'environment': {'type': 'string', 'enum': ['development', 'staging', 'production']},
                    'infrastructure_type': {'type': 'string', 'enum': ['kubernetes', 'docker', 'vm', 'cloud']}
                }
            }
        },
        pagination_schema={
            'page': {'type': 'integer', 'default': 1},
            'per_page': {'type': 'integer', 'default': 20, 'maximum': 100},
            'sort': {'type': 'string', 'enum': ['name', 'created_at', 'updated_at']},
            'order': {'type': 'string', 'enum': ['asc', 'desc'], 'default': 'desc'}
        },
        output_schema={
            'project': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'status': {'type': 'string', 'enum': ['active', 'inactive', 'archived']},
                    'created_at': {'type': 'string', 'format': 'date-time'},
                    'updated_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        },
        parameter_schema={
            'project_id': {'type': 'string', 'required': True, 'description': 'Unique project identifier'},
            'environment': {'type': 'string', 'enum': ['development', 'staging', 'production']},
            'include_deployments': {'type': 'boolean', 'default': False}
        },
        is_active=True
    )


def remove_infrakit_system(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    System.objects.filter(name='infrakit').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0003_add_schema_fields'),
    ]

    operations = [
        migrations.RunPython(create_infrakit_system, remove_infrakit_system),
    ]
