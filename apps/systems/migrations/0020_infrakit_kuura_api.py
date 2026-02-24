"""
Add Infrakit Kuura API interface with all resources and actions.
Based on: https://docs.infrakit.com/specifications/kuura-api.yaml
"""
from django.db import migrations


def add_kuura_api(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')

    # Get Infrakit system
    infrakit = System.objects.filter(alias='infrakit').first()
    if not infrakit:
        print("Infrakit system not found, skipping")
        return

    # Update system details
    infrakit.description = 'Infrakit construction project management platform. Provides access to projects, models, logpoints, mass haul, and more via Kuura API.'
    infrakit.variables = {
        'iam_url': 'https://iam.infrakit.com'
    }
    infrakit.meta = {
        'api_version': 'Kuura v1',
        'docs_url': 'https://docs.infrakit.com/specifications/kuura-api.yaml'
    }
    infrakit.save()

    # Create Kuura API interface
    kuura = Interface.objects.create(
        system=infrakit,
        alias='kuura',
        name='kuura',
        type='API',
        base_url='https://app.infrakit.com/kuura',
        auth={
            'type': 'oauth2_password',
            'token_url': 'https://iam.infrakit.com/auth/token',
            'grant_type': 'password',
            'token_field': 'accessToken',
            'expires_field': 'expiresIn',
            'test_endpoint': '/v1/time'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 60}
    )

    # ==========================================================================
    # Resource: Time
    # ==========================================================================
    time_resource = Resource.objects.create(
        interface=kuura, alias='time', name='time',
        description='Server time information'
    )
    Action.objects.create(
        resource=time_resource, alias='get', name='get',
        description='Get server and user timestamps',
        method='GET', path='/v1/time',
        parameters_schema={'type': 'object', 'properties': {}}
    )

    # ==========================================================================
    # Resource: Projects
    # ==========================================================================
    projects = Resource.objects.create(
        interface=kuura, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=projects, alias='list', name='list',
        description='List all projects for the user',
        method='GET', path='/v1/projects',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=projects, alias='get', name='get',
        description='Get project details by UUID',
        method='GET', path='/v1/project/{uuid}',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Project UUID'}},
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=projects, alias='create', name='create',
        description='Create a new project',
        method='POST', path='/v1/project',
        parameters_schema={
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': 'Project name'},
                'organizationUuid': {'type': 'string', 'description': 'Organization UUID'}
            },
            'required': ['name', 'organizationUuid']
        }
    )
    Action.objects.create(
        resource=projects, alias='get_folders', name='get_folders',
        description='Get project folder structure',
        method='GET', path='/v1/project/{uuid}/folders',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Project UUID'}},
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=projects, alias='get_main_alignment', name='get_main_alignment',
        description='Get main alignment details',
        method='GET', path='/v1/project/{uuid}/main-alignment',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Project UUID'}},
            'required': ['uuid']
        }
    )

    # ==========================================================================
    # Resource: Organization
    # ==========================================================================
    org = Resource.objects.create(
        interface=kuura, alias='organization', name='organization',
        description='Organization management'
    )
    Action.objects.create(
        resource=org, alias='get', name='get',
        description='Get organization details',
        method='GET', path='/v1/organization/{uuid}',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Organization UUID'}},
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=org, alias='get_projects', name='get_projects',
        description='List organization projects',
        method='GET', path='/v1/organization/{uuid}/projects',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Organization UUID'}},
            'required': ['uuid']
        }
    )

    # ==========================================================================
    # Resource: Folders
    # ==========================================================================
    folders = Resource.objects.create(
        interface=kuura, alias='folders', name='folders',
        description='Folder management'
    )
    Action.objects.create(
        resource=folders, alias='get', name='get',
        description='View folder with contents',
        method='GET', path='/v1/folder/{uuid}',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Folder UUID'}},
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=folders, alias='create', name='create',
        description='Create a new folder',
        method='POST', path='/v1/folder',
        parameters_schema={
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': 'Folder name'},
                'parentUuid': {'type': 'string', 'description': 'Parent folder UUID'}
            },
            'required': ['name', 'parentUuid']
        }
    )
    Action.objects.create(
        resource=folders, alias='get_documents', name='get_documents',
        description='List folder documents',
        method='GET', path='/v1/folder/{uuid}/documents',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Folder UUID'}},
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=folders, alias='get_models', name='get_models',
        description='List folder models',
        method='GET', path='/v1/folder/{uuid}/models',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Folder UUID'}},
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=folders, alias='get_images', name='get_images',
        description='List folder images',
        method='GET', path='/v1/folder/{uuid}/images',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Folder UUID'}},
            'required': ['uuid']
        }
    )

    # ==========================================================================
    # Resource: Models
    # ==========================================================================
    models = Resource.objects.create(
        interface=kuura, alias='models', name='models',
        description='3D models and design files'
    )
    Action.objects.create(
        resource=models, alias='get_changed', name='get_changed',
        description='Retrieve modified models since timestamp',
        method='GET', path='/v1/models/changed-files',
        parameters_schema={
            'type': 'object',
            'properties': {
                'projectUuid': {'type': 'string', 'description': 'Project UUID'},
                'since': {'type': 'string', 'description': 'ISO timestamp'}
            },
            'required': ['projectUuid']
        }
    )
    Action.objects.create(
        resource=models, alias='download', name='download',
        description='Download model file',
        method='GET', path='/v1/models/{modelId}/file-download',
        parameters_schema={
            'type': 'object',
            'properties': {'modelId': {'type': 'string', 'description': 'Model ID'}},
            'required': ['modelId']
        }
    )
    Action.objects.create(
        resource=models, alias='upload_async', name='upload_async',
        description='Get pre-signed URL for model upload',
        method='POST', path='/v1/model/async-upload',
        parameters_schema={
            'type': 'object',
            'properties': {
                'folderUuid': {'type': 'string', 'description': 'Target folder UUID'},
                'filename': {'type': 'string', 'description': 'File name'}
            },
            'required': ['folderUuid', 'filename']
        }
    )

    # ==========================================================================
    # Resource: Images
    # ==========================================================================
    images = Resource.objects.create(
        interface=kuura, alias='images', name='images',
        description='Project images and photos'
    )
    Action.objects.create(
        resource=images, alias='download', name='download',
        description='Download image file',
        method='GET', path='/v1/image/{imageId}',
        parameters_schema={
            'type': 'object',
            'properties': {'imageId': {'type': 'string', 'description': 'Image ID'}},
            'required': ['imageId']
        }
    )
    Action.objects.create(
        resource=images, alias='upload_async', name='upload_async',
        description='Get pre-signed URL for image upload',
        method='POST', path='/v1/image/async-upload',
        parameters_schema={
            'type': 'object',
            'properties': {
                'folderUuid': {'type': 'string', 'description': 'Target folder UUID'},
                'filename': {'type': 'string', 'description': 'File name'}
            },
            'required': ['folderUuid', 'filename']
        }
    )

    # ==========================================================================
    # Resource: Logpoints (As-Built)
    # ==========================================================================
    logpoints = Resource.objects.create(
        interface=kuura, alias='logpoints', name='logpoints',
        description='As-built logpoints and survey data'
    )
    Action.objects.create(
        resource=logpoints, alias='list', name='list',
        description='Retrieve project logpoints',
        method='GET', path='/v1/project/{uuid}/logpoints',
        parameters_schema={
            'type': 'object',
            'properties': {
                'uuid': {'type': 'string', 'description': 'Project UUID'},
                'from': {'type': 'string', 'description': 'Start timestamp'},
                'to': {'type': 'string', 'description': 'End timestamp'}
            },
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=logpoints, alias='create', name='create',
        description='Add logpoints to project',
        method='POST', path='/v1/project/{uuid}/logpoints',
        parameters_schema={
            'type': 'object',
            'properties': {
                'uuid': {'type': 'string', 'description': 'Project UUID'},
                'logpoints': {'type': 'array', 'description': 'Array of logpoint data'}
            },
            'required': ['uuid', 'logpoints']
        }
    )
    Action.objects.create(
        resource=logpoints, alias='update', name='update',
        description='Modify existing logpoints',
        method='PATCH', path='/v1/project/{uuid}/logpoints',
        parameters_schema={
            'type': 'object',
            'properties': {
                'uuid': {'type': 'string', 'description': 'Project UUID'},
                'logpoints': {'type': 'array', 'description': 'Array of logpoint updates'}
            },
            'required': ['uuid', 'logpoints']
        }
    )
    Action.objects.create(
        resource=logpoints, alias='delete', name='delete',
        description='Delete logpoints',
        method='POST', path='/v1/project/{uuid}/logpoints/delete',
        parameters_schema={
            'type': 'object',
            'properties': {
                'uuid': {'type': 'string', 'description': 'Project UUID'},
                'logpointIds': {'type': 'array', 'description': 'Array of logpoint IDs to delete'}
            },
            'required': ['uuid', 'logpointIds']
        }
    )
    Action.objects.create(
        resource=logpoints, alias='upload_file', name='upload_file',
        description='Upload logpoints from file',
        method='POST', path='/v1/project/{uuid}/logpoints/file',
        parameters_schema={
            'type': 'object',
            'properties': {
                'uuid': {'type': 'string', 'description': 'Project UUID'}
            },
            'required': ['uuid']
        }
    )

    # ==========================================================================
    # Resource: Mass Haul
    # ==========================================================================
    masshaul = Resource.objects.create(
        interface=kuura, alias='masshaul', name='masshaul',
        description='Mass haul areas and materials'
    )
    Action.objects.create(
        resource=masshaul, alias='get_areas', name='get_areas',
        description='Get mass haul areas',
        method='GET', path='/v1/project/{uuid}/masshaul-areas',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Project UUID'}},
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=masshaul, alias='create_area', name='create_area',
        description='Create mass haul area',
        method='POST', path='/v1/project/{uuid}/masshaul-area',
        parameters_schema={
            'type': 'object',
            'properties': {
                'uuid': {'type': 'string', 'description': 'Project UUID'},
                'name': {'type': 'string', 'description': 'Area name'}
            },
            'required': ['uuid', 'name']
        }
    )
    Action.objects.create(
        resource=masshaul, alias='get_materials', name='get_materials',
        description='List project materials',
        method='GET', path='/v1/project/{uuid}/materials',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Project UUID'}},
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=masshaul, alias='get_trips', name='get_trips',
        description='Retrieve vehicle trips',
        method='GET', path='/v1/project/{uuid}/trips',
        parameters_schema={
            'type': 'object',
            'properties': {
                'uuid': {'type': 'string', 'description': 'Project UUID'},
                'from': {'type': 'string', 'description': 'Start timestamp'},
                'to': {'type': 'string', 'description': 'End timestamp'}
            },
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=masshaul, alias='create_trip', name='create_trip',
        description='Create vehicle trip',
        method='POST', path='/v1/project/{uuid}/trips',
        parameters_schema={
            'type': 'object',
            'properties': {
                'uuid': {'type': 'string', 'description': 'Project UUID'}
            },
            'required': ['uuid']
        }
    )
    Action.objects.create(
        resource=masshaul, alias='get_truck_tasks', name='get_truck_tasks',
        description='Get truck tasks',
        method='GET', path='/v1/project/{uuid}/truck-tasks',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'Project UUID'}},
            'required': ['uuid']
        }
    )

    # ==========================================================================
    # Resource: Equipment
    # ==========================================================================
    equipment = Resource.objects.create(
        interface=kuura, alias='equipment', name='equipment',
        description='Construction equipment and machines'
    )
    Action.objects.create(
        resource=equipment, alias='list', name='list',
        description='List project machines',
        method='GET', path='/v1/machines',
        parameters_schema={
            'type': 'object',
            'properties': {
                'projectUuid': {'type': 'string', 'description': 'Project UUID'}
            },
            'required': ['projectUuid']
        }
    )
    Action.objects.create(
        resource=equipment, alias='get', name='get',
        description='Get machine details',
        method='GET', path='/v1/machine/{vehicleId}',
        parameters_schema={
            'type': 'object',
            'properties': {'vehicleId': {'type': 'string', 'description': 'Vehicle ID'}},
            'required': ['vehicleId']
        }
    )
    Action.objects.create(
        resource=equipment, alias='get_vendors', name='get_vendors',
        description='List equipment vendors',
        method='GET', path='/v1/machines/vendors',
        parameters_schema={'type': 'object', 'properties': {}}
    )

    # ==========================================================================
    # Resource: Documents
    # ==========================================================================
    documents = Resource.objects.create(
        interface=kuura, alias='documents', name='documents',
        description='Project documents'
    )
    Action.objects.create(
        resource=documents, alias='upload_async', name='upload_async',
        description='Get pre-signed URL for document upload',
        method='POST', path='/v1/document/async-upload',
        parameters_schema={
            'type': 'object',
            'properties': {
                'folderUuid': {'type': 'string', 'description': 'Target folder UUID'},
                'filename': {'type': 'string', 'description': 'File name'}
            },
            'required': ['folderUuid', 'filename']
        }
    )

    # ==========================================================================
    # IAM Interface for user info
    # ==========================================================================
    iam = Interface.objects.create(
        system=infrakit,
        alias='iam',
        name='iam',
        type='API',
        base_url='https://iam.infrakit.com',
        auth={
            'type': 'oauth2_password',
            'token_url': 'https://iam.infrakit.com/auth/token',
            'grant_type': 'password',
            'token_field': 'accessToken',
            'expires_field': 'expiresIn',
            'test_endpoint': '/user'
        },
        requires_browser=False
    )

    user = Resource.objects.create(
        interface=iam, alias='user', name='user',
        description='User management'
    )
    Action.objects.create(
        resource=user, alias='get_current', name='get_current',
        description='Get current user info including organizationUuid',
        method='GET', path='/user',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=user, alias='get', name='get',
        description='Get user by UUID',
        method='GET', path='/v1/user/{uuid}',
        parameters_schema={
            'type': 'object',
            'properties': {'uuid': {'type': 'string', 'description': 'User UUID'}},
            'required': ['uuid']
        }
    )


def remove_kuura_api(apps, schema_editor):
    Interface = apps.get_model('systems', 'Interface')
    Interface.objects.filter(system__alias='infrakit', alias__in=['kuura', 'iam']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0019_encrypt_existing_credentials'),
    ]

    operations = [
        migrations.RunPython(add_kuura_api, remove_kuura_api),
    ]
