"""
Add BIM platforms and project banks for construction:
- Autodesk Construction Cloud (ACC/BIM 360)
- Trimble Connect
- Dalux
- SokoPro
"""
from django.db import migrations


def add_bim_and_projectbank_adapters(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')
    IndustryTemplate = apps.get_model('systems', 'IndustryTemplate')
    TermMapping = apps.get_model('systems', 'TermMapping')

    # Get construction industry template
    construction = IndustryTemplate.objects.filter(name='construction').first()
    if not construction:
        print("Construction template not found, skipping")
        return

    # ==========================================================================
    # AUTODESK CONSTRUCTION CLOUD (ACC / BIM 360)
    # ==========================================================================
    autodesk = System.objects.create(
        name='autodesk_acc',
        alias='autodesk',
        display_name='Autodesk Construction Cloud',
        description='Autodesk Construction Cloud (ACC) and BIM 360. Cloud-based BIM collaboration, model coordination, document management, and project insights.',
        system_type='bim',
        icon='box',
        website_url='https://construction.autodesk.com',
        industry=construction,
        variables={
            'api_url': 'https://developer.api.autodesk.com'
        },
        meta={
            'api_version': 'v2',
            'docs_url': 'https://aps.autodesk.com/developer/documentation'
        },
        is_active=True
    )

    # Autodesk Data Management API
    autodesk_dm = Interface.objects.create(
        system=autodesk,
        alias='data',
        name='data',
        type='API',
        base_url='https://developer.api.autodesk.com',
        auth={
            'type': 'oauth2',
            'authorization_url': 'https://developer.api.autodesk.com/authentication/v2/authorize',
            'token_url': 'https://developer.api.autodesk.com/authentication/v2/token',
            'scope': 'data:read data:write data:create bucket:read'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 300}
    )

    # Autodesk Hubs (ACC accounts)
    autodesk_hubs = Resource.objects.create(
        interface=autodesk_dm, alias='hubs', name='hubs',
        description='ACC/BIM 360 hubs (accounts)'
    )
    Action.objects.create(
        resource=autodesk_hubs, alias='list', name='list',
        description='List all hubs (ACC accounts)',
        method='GET', path='/project/v1/hubs',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=autodesk_hubs, alias='get', name='get',
        description='Get hub details',
        method='GET', path='/project/v1/hubs/{hub_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'hub_id': {'type': 'string', 'description': 'Hub ID'}},
            'required': ['hub_id']
        }
    )

    # Autodesk Projects
    autodesk_projects = Resource.objects.create(
        interface=autodesk_dm, alias='projects', name='projects',
        description='ACC/BIM 360 projects'
    )
    Action.objects.create(
        resource=autodesk_projects, alias='list', name='list',
        description='List projects in a hub',
        method='GET', path='/project/v1/hubs/{hub_id}/projects',
        parameters_schema={
            'type': 'object',
            'properties': {'hub_id': {'type': 'string', 'description': 'Hub ID'}},
            'required': ['hub_id']
        }
    )
    Action.objects.create(
        resource=autodesk_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/project/v1/hubs/{hub_id}/projects/{project_id}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'hub_id': {'type': 'string', 'description': 'Hub ID'},
                'project_id': {'type': 'string', 'description': 'Project ID'}
            },
            'required': ['hub_id', 'project_id']
        }
    )

    # Autodesk Folders
    autodesk_folders = Resource.objects.create(
        interface=autodesk_dm, alias='folders', name='folders',
        description='Project folders'
    )
    Action.objects.create(
        resource=autodesk_folders, alias='get_contents', name='get_contents',
        description='Get folder contents',
        method='GET', path='/data/v1/projects/{project_id}/folders/{folder_id}/contents',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'folder_id': {'type': 'string', 'description': 'Folder ID'}
            },
            'required': ['project_id', 'folder_id']
        }
    )
    Action.objects.create(
        resource=autodesk_folders, alias='get_top_folders', name='get_top_folders',
        description='Get project top-level folders',
        method='GET', path='/project/v1/hubs/{hub_id}/projects/{project_id}/topFolders',
        parameters_schema={
            'type': 'object',
            'properties': {
                'hub_id': {'type': 'string', 'description': 'Hub ID'},
                'project_id': {'type': 'string', 'description': 'Project ID'}
            },
            'required': ['hub_id', 'project_id']
        }
    )

    # Autodesk Items (Files)
    autodesk_items = Resource.objects.create(
        interface=autodesk_dm, alias='items', name='items',
        description='Files and documents'
    )
    Action.objects.create(
        resource=autodesk_items, alias='get', name='get',
        description='Get item details',
        method='GET', path='/data/v1/projects/{project_id}/items/{item_id}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'item_id': {'type': 'string', 'description': 'Item ID'}
            },
            'required': ['project_id', 'item_id']
        }
    )
    Action.objects.create(
        resource=autodesk_items, alias='get_versions', name='get_versions',
        description='Get item versions',
        method='GET', path='/data/v1/projects/{project_id}/items/{item_id}/versions',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'item_id': {'type': 'string', 'description': 'Item ID'}
            },
            'required': ['project_id', 'item_id']
        }
    )

    # Autodesk Model Derivative (for viewing/translating models)
    autodesk_models = Resource.objects.create(
        interface=autodesk_dm, alias='models', name='models',
        description='BIM model operations'
    )
    Action.objects.create(
        resource=autodesk_models, alias='get_manifest', name='get_manifest',
        description='Get model manifest (translation status)',
        method='GET', path='/modelderivative/v2/designdata/{urn}/manifest',
        parameters_schema={
            'type': 'object',
            'properties': {'urn': {'type': 'string', 'description': 'Base64-encoded URN'}},
            'required': ['urn']
        }
    )
    Action.objects.create(
        resource=autodesk_models, alias='get_metadata', name='get_metadata',
        description='Get model metadata',
        method='GET', path='/modelderivative/v2/designdata/{urn}/metadata',
        parameters_schema={
            'type': 'object',
            'properties': {'urn': {'type': 'string', 'description': 'Base64-encoded URN'}},
            'required': ['urn']
        }
    )
    Action.objects.create(
        resource=autodesk_models, alias='translate', name='translate',
        description='Start model translation job',
        method='POST', path='/modelderivative/v2/designdata/job',
        parameters_schema={
            'type': 'object',
            'properties': {
                'urn': {'type': 'string', 'description': 'Base64-encoded URN'},
                'output_format': {'type': 'string', 'enum': ['svf', 'svf2', 'ifc'], 'description': 'Output format'}
            },
            'required': ['urn']
        }
    )

    # Autodesk Issues
    autodesk_issues = Resource.objects.create(
        interface=autodesk_dm, alias='issues', name='issues',
        description='Project issues and RFIs'
    )
    Action.objects.create(
        resource=autodesk_issues, alias='list', name='list',
        description='List project issues',
        method='GET', path='/issues/v1/containers/{container_id}/quality-issues',
        parameters_schema={
            'type': 'object',
            'properties': {
                'container_id': {'type': 'string', 'description': 'Issues container ID'}
            },
            'required': ['container_id']
        }
    )
    Action.objects.create(
        resource=autodesk_issues, alias='create', name='create',
        description='Create an issue',
        method='POST', path='/issues/v1/containers/{container_id}/quality-issues',
        parameters_schema={
            'type': 'object',
            'properties': {
                'container_id': {'type': 'string', 'description': 'Issues container ID'},
                'title': {'type': 'string', 'description': 'Issue title'},
                'description': {'type': 'string', 'description': 'Issue description'},
                'status': {'type': 'string', 'enum': ['open', 'pending', 'closed']}
            },
            'required': ['container_id', 'title']
        }
    )

    # Autodesk term mappings
    autodesk_terms = [
        ('project', 'Project'),
        ('model', 'Model'),
        ('drawing', 'Sheet'),
        ('folder', 'Folder'),
        ('observation', 'Issue'),
        ('company', 'Company'),
    ]
    for canonical_term, system_term in autodesk_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=autodesk,
            defaults={'system_term': system_term}
        )

    # ==========================================================================
    # TRIMBLE CONNECT
    # ==========================================================================
    trimble = System.objects.create(
        name='trimble_connect',
        alias='trimble',
        display_name='Trimble Connect',
        description='Trimble Connect - Cloud collaboration platform for construction. BIM collaboration, model viewing, clash detection, and field data collection. Integrates with Tekla, SketchUp, and Trimble field solutions.',
        system_type='bim',
        icon='layers',
        website_url='https://connect.trimble.com',
        industry=construction,
        variables={
            'api_url': 'https://app.connect.trimble.com/tc/api/2.0'
        },
        meta={
            'api_version': '2.0',
            'docs_url': 'https://developer.trimble.com/docs/connect-api'
        },
        is_active=True
    )

    # Trimble Connect API
    trimble_api = Interface.objects.create(
        system=trimble,
        alias='api',
        name='api',
        type='API',
        base_url='https://app.connect.trimble.com/tc/api/2.0',
        auth={
            'type': 'oauth2',
            'authorization_url': 'https://id.trimble.com/oauth/authorize',
            'token_url': 'https://id.trimble.com/oauth/token',
            'scope': 'openid trimble-connect'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 120}
    )

    # Trimble Projects
    trimble_projects = Resource.objects.create(
        interface=trimble_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=trimble_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/projects',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=trimble_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/projects/{project_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=trimble_projects, alias='create', name='create',
        description='Create a new project',
        method='POST', path='/projects',
        parameters_schema={
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': 'Project name'},
                'description': {'type': 'string', 'description': 'Project description'},
                'location': {'type': 'string', 'description': 'Project location'}
            },
            'required': ['name']
        }
    )

    # Trimble Folders
    trimble_folders = Resource.objects.create(
        interface=trimble_api, alias='folders', name='folders',
        description='Project folder structure'
    )
    Action.objects.create(
        resource=trimble_folders, alias='list', name='list',
        description='List folders in project',
        method='GET', path='/projects/{project_id}/folders',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=trimble_folders, alias='get_contents', name='get_contents',
        description='Get folder contents',
        method='GET', path='/folders/{folder_id}/items',
        parameters_schema={
            'type': 'object',
            'properties': {'folder_id': {'type': 'string', 'description': 'Folder ID'}},
            'required': ['folder_id']
        }
    )

    # Trimble Files
    trimble_files = Resource.objects.create(
        interface=trimble_api, alias='files', name='files',
        description='File management'
    )
    Action.objects.create(
        resource=trimble_files, alias='get', name='get',
        description='Get file details',
        method='GET', path='/files/{file_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'file_id': {'type': 'string', 'description': 'File ID'}},
            'required': ['file_id']
        }
    )
    Action.objects.create(
        resource=trimble_files, alias='get_versions', name='get_versions',
        description='Get file version history',
        method='GET', path='/files/{file_id}/versions',
        parameters_schema={
            'type': 'object',
            'properties': {'file_id': {'type': 'string', 'description': 'File ID'}},
            'required': ['file_id']
        }
    )
    Action.objects.create(
        resource=trimble_files, alias='download', name='download',
        description='Get file download URL',
        method='GET', path='/files/{file_id}/downloadurl',
        parameters_schema={
            'type': 'object',
            'properties': {'file_id': {'type': 'string', 'description': 'File ID'}},
            'required': ['file_id']
        }
    )

    # Trimble Models (3D/BIM)
    trimble_models = Resource.objects.create(
        interface=trimble_api, alias='models', name='models',
        description='BIM models and 3D views'
    )
    Action.objects.create(
        resource=trimble_models, alias='list', name='list',
        description='List project models',
        method='GET', path='/projects/{project_id}/models',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=trimble_models, alias='get', name='get',
        description='Get model details',
        method='GET', path='/models/{model_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'model_id': {'type': 'string', 'description': 'Model ID'}},
            'required': ['model_id']
        }
    )

    # Trimble ToDos (Tasks)
    trimble_todos = Resource.objects.create(
        interface=trimble_api, alias='todos', name='todos',
        description='Tasks and to-dos'
    )
    Action.objects.create(
        resource=trimble_todos, alias='list', name='list',
        description='List project to-dos',
        method='GET', path='/projects/{project_id}/todos',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=trimble_todos, alias='create', name='create',
        description='Create a to-do',
        method='POST', path='/projects/{project_id}/todos',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'label': {'type': 'string', 'description': 'To-do label'},
                'description': {'type': 'string', 'description': 'Description'},
                'priority': {'type': 'string', 'enum': ['low', 'normal', 'high', 'critical']}
            },
            'required': ['project_id', 'label']
        }
    )

    # Trimble term mappings
    trimble_terms = [
        ('project', 'Project'),
        ('model', 'Model'),
        ('drawing', 'File'),
        ('folder', 'Folder'),
        ('observation', 'ToDo'),
        ('equipment', 'Asset'),
    ]
    for canonical_term, system_term in trimble_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=trimble,
            defaults={'system_term': system_term}
        )

    # ==========================================================================
    # DALUX - Project Bank / Field Management
    # ==========================================================================
    dalux = System.objects.create(
        name='dalux',
        alias='dalux',
        display_name='Dalux',
        description='Dalux - Digital construction platform. BIM viewer, quality assurance, handover, and facility management. Strong in Nordic markets.',
        system_type='project_management',
        icon='phone',
        website_url='https://dalux.com',
        industry=construction,
        variables={
            'api_url': 'https://api.dalux.com'
        },
        meta={
            'api_version': 'v1',
            'docs_url': 'https://developer.dalux.com'
        },
        is_active=True
    )

    # Dalux API
    dalux_api = Interface.objects.create(
        system=dalux,
        alias='api',
        name='api',
        type='API',
        base_url='https://api.dalux.com/v1',
        auth={
            'type': 'oauth2',
            'authorization_url': 'https://dalux.com/oauth/authorize',
            'token_url': 'https://dalux.com/oauth/token',
            'scope': 'read write'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 60}
    )

    # Dalux Projects
    dalux_projects = Resource.objects.create(
        interface=dalux_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=dalux_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/projects',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=dalux_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/projects/{project_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # Dalux Documents
    dalux_docs = Resource.objects.create(
        interface=dalux_api, alias='documents', name='documents',
        description='Document management'
    )
    Action.objects.create(
        resource=dalux_docs, alias='list', name='list',
        description='List project documents',
        method='GET', path='/projects/{project_id}/documents',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'folder_id': {'type': 'string', 'description': 'Filter by folder'}
            },
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=dalux_docs, alias='get', name='get',
        description='Get document details',
        method='GET', path='/documents/{document_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'document_id': {'type': 'string', 'description': 'Document ID'}},
            'required': ['document_id']
        }
    )
    Action.objects.create(
        resource=dalux_docs, alias='get_versions', name='get_versions',
        description='Get document versions',
        method='GET', path='/documents/{document_id}/versions',
        parameters_schema={
            'type': 'object',
            'properties': {'document_id': {'type': 'string', 'description': 'Document ID'}},
            'required': ['document_id']
        }
    )

    # Dalux Issues/QA
    dalux_issues = Resource.objects.create(
        interface=dalux_api, alias='issues', name='issues',
        description='Quality assurance issues'
    )
    Action.objects.create(
        resource=dalux_issues, alias='list', name='list',
        description='List project issues',
        method='GET', path='/projects/{project_id}/issues',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'status': {'type': 'string', 'description': 'Filter by status'}
            },
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=dalux_issues, alias='create', name='create',
        description='Create an issue',
        method='POST', path='/projects/{project_id}/issues',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'title': {'type': 'string', 'description': 'Issue title'},
                'description': {'type': 'string', 'description': 'Issue description'},
                'location': {'type': 'string', 'description': 'Location in building'},
                'assignee': {'type': 'string', 'description': 'Assignee ID'}
            },
            'required': ['project_id', 'title']
        }
    )

    # Dalux Checklists
    dalux_checklists = Resource.objects.create(
        interface=dalux_api, alias='checklists', name='checklists',
        description='QA checklists'
    )
    Action.objects.create(
        resource=dalux_checklists, alias='list', name='list',
        description='List project checklists',
        method='GET', path='/projects/{project_id}/checklists',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=dalux_checklists, alias='get', name='get',
        description='Get checklist with items',
        method='GET', path='/checklists/{checklist_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'checklist_id': {'type': 'string', 'description': 'Checklist ID'}},
            'required': ['checklist_id']
        }
    )

    # Dalux Models (BIM viewer)
    dalux_models = Resource.objects.create(
        interface=dalux_api, alias='models', name='models',
        description='BIM models'
    )
    Action.objects.create(
        resource=dalux_models, alias='list', name='list',
        description='List project models',
        method='GET', path='/projects/{project_id}/models',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # Dalux term mappings
    dalux_terms = [
        ('project', 'Project'),
        ('model', 'Model'),
        ('drawing', 'Document'),
        ('observation', 'Issue'),
        ('inspection', 'Checklist'),
    ]
    for canonical_term, system_term in dalux_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=dalux,
            defaults={'system_term': system_term}
        )

    # ==========================================================================
    # SOKOPRO - Finnish Project Bank
    # ==========================================================================
    sokopro = System.objects.create(
        name='sokopro',
        alias='sokopro',
        display_name='SokoPro',
        description='SokoPro - Finnish project bank and document management system. Widely used in Finnish construction for document distribution, version control, and project communication.',
        system_type='storage',
        icon='archive',
        website_url='https://sokopro.fi',
        industry=construction,
        variables={
            'api_url': 'https://api.sokopro.fi'
        },
        meta={
            'api_version': 'v1',
            'market': 'Finland'
        },
        is_active=True
    )

    # SokoPro API
    sokopro_api = Interface.objects.create(
        system=sokopro,
        alias='api',
        name='api',
        type='API',
        base_url='https://api.sokopro.fi/v1',
        auth={
            'type': 'bearer',
            'header': 'Authorization',
            'prefix': 'Bearer'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 60}
    )

    # SokoPro Projects
    sokopro_projects = Resource.objects.create(
        interface=sokopro_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=sokopro_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/projects',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=sokopro_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/projects/{project_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # SokoPro Folders
    sokopro_folders = Resource.objects.create(
        interface=sokopro_api, alias='folders', name='folders',
        description='Folder structure'
    )
    Action.objects.create(
        resource=sokopro_folders, alias='list', name='list',
        description='List project folders',
        method='GET', path='/projects/{project_id}/folders',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=sokopro_folders, alias='get_contents', name='get_contents',
        description='Get folder contents',
        method='GET', path='/folders/{folder_id}/contents',
        parameters_schema={
            'type': 'object',
            'properties': {'folder_id': {'type': 'string', 'description': 'Folder ID'}},
            'required': ['folder_id']
        }
    )

    # SokoPro Documents
    sokopro_docs = Resource.objects.create(
        interface=sokopro_api, alias='documents', name='documents',
        description='Document management'
    )
    Action.objects.create(
        resource=sokopro_docs, alias='list', name='list',
        description='List documents',
        method='GET', path='/projects/{project_id}/documents',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'folder_id': {'type': 'string', 'description': 'Filter by folder'},
                'modified_since': {'type': 'string', 'format': 'date-time', 'description': 'Filter by modification date'}
            },
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=sokopro_docs, alias='get', name='get',
        description='Get document details',
        method='GET', path='/documents/{document_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'document_id': {'type': 'string', 'description': 'Document ID'}},
            'required': ['document_id']
        }
    )
    Action.objects.create(
        resource=sokopro_docs, alias='get_versions', name='get_versions',
        description='Get document version history',
        method='GET', path='/documents/{document_id}/versions',
        parameters_schema={
            'type': 'object',
            'properties': {'document_id': {'type': 'string', 'description': 'Document ID'}},
            'required': ['document_id']
        }
    )
    Action.objects.create(
        resource=sokopro_docs, alias='download', name='download',
        description='Download document file',
        method='GET', path='/documents/{document_id}/download',
        parameters_schema={
            'type': 'object',
            'properties': {
                'document_id': {'type': 'string', 'description': 'Document ID'},
                'version': {'type': 'integer', 'description': 'Version number (latest if omitted)'}
            },
            'required': ['document_id']
        }
    )

    # SokoPro Distribution Lists
    sokopro_distribution = Resource.objects.create(
        interface=sokopro_api, alias='distributions', name='distributions',
        description='Document distribution'
    )
    Action.objects.create(
        resource=sokopro_distribution, alias='list', name='list',
        description='List distribution lists',
        method='GET', path='/projects/{project_id}/distributions',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=sokopro_distribution, alias='send', name='send',
        description='Send documents to distribution list',
        method='POST', path='/distributions/{distribution_id}/send',
        parameters_schema={
            'type': 'object',
            'properties': {
                'distribution_id': {'type': 'string', 'description': 'Distribution list ID'},
                'document_ids': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Document IDs to send'},
                'message': {'type': 'string', 'description': 'Optional message'}
            },
            'required': ['distribution_id', 'document_ids']
        }
    )

    # SokoPro Comments
    sokopro_comments = Resource.objects.create(
        interface=sokopro_api, alias='comments', name='comments',
        description='Document comments'
    )
    Action.objects.create(
        resource=sokopro_comments, alias='list', name='list',
        description='List document comments',
        method='GET', path='/documents/{document_id}/comments',
        parameters_schema={
            'type': 'object',
            'properties': {'document_id': {'type': 'string', 'description': 'Document ID'}},
            'required': ['document_id']
        }
    )
    Action.objects.create(
        resource=sokopro_comments, alias='create', name='create',
        description='Add comment to document',
        method='POST', path='/documents/{document_id}/comments',
        parameters_schema={
            'type': 'object',
            'properties': {
                'document_id': {'type': 'string', 'description': 'Document ID'},
                'text': {'type': 'string', 'description': 'Comment text'}
            },
            'required': ['document_id', 'text']
        }
    )

    # SokoPro term mappings
    sokopro_terms = [
        ('project', 'Projekti'),
        ('drawing', 'Dokumentti'),
        ('folder', 'Kansio'),
        ('company', 'Yritys'),
    ]
    for canonical_term, system_term in sokopro_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=sokopro,
            defaults={'system_term': system_term}
        )

    print("Created BIM and project bank adapters: Autodesk ACC, Trimble Connect, Dalux, SokoPro")


def remove_bim_and_projectbank_adapters(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    System.objects.filter(alias__in=['autodesk', 'trimble', 'dalux', 'sokopro']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0033_add_construction_adapters'),
    ]

    operations = [
        migrations.RunPython(add_bim_and_projectbank_adapters, remove_bim_and_projectbank_adapters),
    ]
