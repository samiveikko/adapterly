# Generated migration for SharePoint adapter

from django.db import migrations


def add_sharepoint_adapter(apps, schema_editor):
    """Add Microsoft SharePoint system with Graph API interface."""
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')
    AuthenticationStep = apps.get_model('systems', 'AuthenticationStep')

    # Create or get SharePoint System
    sharepoint, created = System.objects.get_or_create(
        alias='sharepoint',
        defaults={
            'name': 'sharepoint',
            'display_name': 'Microsoft SharePoint',
            'description': 'Document management and collaboration platform with sites, lists, and document libraries',
            'system_type': 'storage',
            'icon': 'share-2',
            'website_url': 'https://www.microsoft.com/sharepoint',
            'is_active': True,
            'variables': {},
            'meta': {
                'vendor': 'Microsoft',
                'category': 'Document Management'
            }
        }
    )

    # Clean up existing interfaces for this system to avoid duplicates
    Interface.objects.filter(system=sharepoint).delete()
    AuthenticationStep.objects.filter(system=sharepoint).delete()

    # Create Azure AD OAuth2 Authentication Step
    AuthenticationStep.objects.create(
        system=sharepoint,
        step_order=1,
        step_type='oauth',
        step_name='Azure AD OAuth2',
        description='Authenticate using Azure Active Directory',
        base_url='https://login.microsoftonline.com',
        is_required=True,
        input_fields={
            'client_id': {
                'type': 'text',
                'label': 'Application (client) ID',
                'required': True,
                'description': 'The Application ID from Azure AD App Registration'
            },
            'client_secret': {
                'type': 'password',
                'label': 'Client Secret',
                'required': True,
                'description': 'The client secret from Azure AD App Registration'
            },
            'tenant_id': {
                'type': 'text',
                'label': 'Directory (tenant) ID',
                'required': True,
                'description': 'The Azure AD tenant ID'
            }
        },
        validation_rules={
            'client_id': {'type': 'string', 'required': True},
            'client_secret': {'type': 'string', 'required': True},
            'tenant_id': {'type': 'string', 'required': True}
        },
        success_message='Successfully authenticated with Azure AD',
        failure_message='Azure AD authentication failed'
    )

    # Create Microsoft Graph API Interface (recommended for SharePoint)
    graph = Interface.objects.create(
        system=sharepoint,
        alias='graph',
        name='graph',
        type='API',
        base_url='https://graph.microsoft.com/v1.0',
        auth={
            'type': 'oauth2_client_credentials',
            'token_url': 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        },
        requires_browser=False,
        rate_limits={
            'requests_per_minute': 120
        }
    )

    # ========== SITES RESOURCE ==========
    sites = Resource.objects.create(
        interface=graph,
        alias='sites',
        name='sites',
        description='SharePoint sites management'
    )

    Action.objects.create(
        resource=sites,
        alias='search',
        name='search',
        description='Search for sites across SharePoint',
        method='GET',
        path='/sites',
        parameters_schema={
            'type': 'object',
            'properties': {
                'search': {
                    'type': 'string',
                    'description': 'Search query to find sites'
                }
            },
            'required': ['search']
        }
    )

    Action.objects.create(
        resource=sites,
        alias='get',
        name='get',
        description='Get a specific site by ID',
        method='GET',
        path='/sites/{siteId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID or site path (e.g., contoso.sharepoint.com:/sites/marketing)'
                }
            },
            'required': ['siteId']
        }
    )

    Action.objects.create(
        resource=sites,
        alias='get_by_path',
        name='get_by_path',
        description='Get a site by server-relative path',
        method='GET',
        path='/sites/{hostname}:/{serverRelativePath}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'hostname': {
                    'type': 'string',
                    'description': 'The SharePoint hostname (e.g., contoso.sharepoint.com)'
                },
                'serverRelativePath': {
                    'type': 'string',
                    'description': 'Server-relative path (e.g., sites/marketing)'
                }
            },
            'required': ['hostname', 'serverRelativePath']
        }
    )

    Action.objects.create(
        resource=sites,
        alias='get_root',
        name='get_root',
        description='Get the root site for the tenant',
        method='GET',
        path='/sites/root',
        parameters_schema={
            'type': 'object',
            'properties': {}
        }
    )

    # ========== LISTS RESOURCE ==========
    lists = Resource.objects.create(
        interface=graph,
        alias='lists',
        name='lists',
        description='SharePoint lists management'
    )

    Action.objects.create(
        resource=lists,
        alias='list',
        name='list',
        description='Get all lists in a site',
        method='GET',
        path='/sites/{siteId}/lists',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                }
            },
            'required': ['siteId']
        }
    )

    Action.objects.create(
        resource=lists,
        alias='get',
        name='get',
        description='Get a specific list by ID',
        method='GET',
        path='/sites/{siteId}/lists/{listId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                },
                'listId': {
                    'type': 'string',
                    'description': 'The list ID or list name'
                }
            },
            'required': ['siteId', 'listId']
        }
    )

    Action.objects.create(
        resource=lists,
        alias='create',
        name='create',
        description='Create a new list in a site',
        method='POST',
        path='/sites/{siteId}/lists',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                },
                'displayName': {
                    'type': 'string',
                    'description': 'Display name of the list'
                },
                'list': {
                    'type': 'object',
                    'description': 'List template configuration',
                    'properties': {
                        'template': {
                            'type': 'string',
                            'description': 'List template (e.g., genericList, documentLibrary)'
                        }
                    }
                }
            },
            'required': ['siteId', 'displayName']
        }
    )

    Action.objects.create(
        resource=lists,
        alias='delete',
        name='delete',
        description='Delete a list from a site',
        method='DELETE',
        path='/sites/{siteId}/lists/{listId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                },
                'listId': {
                    'type': 'string',
                    'description': 'The list ID'
                }
            },
            'required': ['siteId', 'listId']
        }
    )

    # ========== LIST ITEMS RESOURCE ==========
    items = Resource.objects.create(
        interface=graph,
        alias='items',
        name='items',
        description='SharePoint list items management'
    )

    Action.objects.create(
        resource=items,
        alias='list',
        name='list',
        description='Get all items in a list',
        method='GET',
        path='/sites/{siteId}/lists/{listId}/items',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                },
                'listId': {
                    'type': 'string',
                    'description': 'The list ID'
                },
                '$expand': {
                    'type': 'string',
                    'description': 'Expand related entities (e.g., fields)'
                },
                '$filter': {
                    'type': 'string',
                    'description': 'OData filter expression'
                },
                '$top': {
                    'type': 'integer',
                    'description': 'Number of items to return'
                },
                '$orderby': {
                    'type': 'string',
                    'description': 'Order results by field'
                }
            },
            'required': ['siteId', 'listId']
        }
    )

    Action.objects.create(
        resource=items,
        alias='get',
        name='get',
        description='Get a specific list item',
        method='GET',
        path='/sites/{siteId}/lists/{listId}/items/{itemId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                },
                'listId': {
                    'type': 'string',
                    'description': 'The list ID'
                },
                'itemId': {
                    'type': 'string',
                    'description': 'The item ID'
                },
                '$expand': {
                    'type': 'string',
                    'description': 'Expand related entities (e.g., fields)'
                }
            },
            'required': ['siteId', 'listId', 'itemId']
        }
    )

    Action.objects.create(
        resource=items,
        alias='create',
        name='create',
        description='Create a new list item',
        method='POST',
        path='/sites/{siteId}/lists/{listId}/items',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                },
                'listId': {
                    'type': 'string',
                    'description': 'The list ID'
                },
                'fields': {
                    'type': 'object',
                    'description': 'Field values for the new item'
                }
            },
            'required': ['siteId', 'listId', 'fields']
        }
    )

    Action.objects.create(
        resource=items,
        alias='update',
        name='update',
        description='Update a list item',
        method='PATCH',
        path='/sites/{siteId}/lists/{listId}/items/{itemId}/fields',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                },
                'listId': {
                    'type': 'string',
                    'description': 'The list ID'
                },
                'itemId': {
                    'type': 'string',
                    'description': 'The item ID'
                },
                'fields': {
                    'type': 'object',
                    'description': 'Field values to update'
                }
            },
            'required': ['siteId', 'listId', 'itemId', 'fields']
        }
    )

    Action.objects.create(
        resource=items,
        alias='delete',
        name='delete',
        description='Delete a list item',
        method='DELETE',
        path='/sites/{siteId}/lists/{listId}/items/{itemId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                },
                'listId': {
                    'type': 'string',
                    'description': 'The list ID'
                },
                'itemId': {
                    'type': 'string',
                    'description': 'The item ID'
                }
            },
            'required': ['siteId', 'listId', 'itemId']
        }
    )

    # ========== DRIVES (DOCUMENT LIBRARIES) RESOURCE ==========
    drives = Resource.objects.create(
        interface=graph,
        alias='drives',
        name='drives',
        description='SharePoint document libraries (drives) management'
    )

    Action.objects.create(
        resource=drives,
        alias='list',
        name='list',
        description='Get all drives (document libraries) in a site',
        method='GET',
        path='/sites/{siteId}/drives',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                }
            },
            'required': ['siteId']
        }
    )

    Action.objects.create(
        resource=drives,
        alias='get',
        name='get',
        description='Get a specific drive by ID',
        method='GET',
        path='/drives/{driveId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                }
            },
            'required': ['driveId']
        }
    )

    Action.objects.create(
        resource=drives,
        alias='get_default',
        name='get_default',
        description='Get the default document library for a site',
        method='GET',
        path='/sites/{siteId}/drive',
        parameters_schema={
            'type': 'object',
            'properties': {
                'siteId': {
                    'type': 'string',
                    'description': 'The site ID'
                }
            },
            'required': ['siteId']
        }
    )

    # ========== DRIVE ITEMS (FILES/FOLDERS) RESOURCE ==========
    drive_items = Resource.objects.create(
        interface=graph,
        alias='drive_items',
        name='drive_items',
        description='SharePoint files and folders management'
    )

    Action.objects.create(
        resource=drive_items,
        alias='list_root',
        name='list_root',
        description='Get items in the root of a drive',
        method='GET',
        path='/drives/{driveId}/root/children',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                },
                '$top': {
                    'type': 'integer',
                    'description': 'Number of items to return'
                },
                '$orderby': {
                    'type': 'string',
                    'description': 'Order results by field'
                }
            },
            'required': ['driveId']
        }
    )

    Action.objects.create(
        resource=drive_items,
        alias='list_folder',
        name='list_folder',
        description='Get items in a folder',
        method='GET',
        path='/drives/{driveId}/items/{itemId}/children',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                },
                'itemId': {
                    'type': 'string',
                    'description': 'The folder item ID'
                },
                '$top': {
                    'type': 'integer',
                    'description': 'Number of items to return'
                }
            },
            'required': ['driveId', 'itemId']
        }
    )

    Action.objects.create(
        resource=drive_items,
        alias='get',
        name='get',
        description='Get a drive item (file or folder) metadata',
        method='GET',
        path='/drives/{driveId}/items/{itemId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                },
                'itemId': {
                    'type': 'string',
                    'description': 'The item ID'
                }
            },
            'required': ['driveId', 'itemId']
        }
    )

    Action.objects.create(
        resource=drive_items,
        alias='get_by_path',
        name='get_by_path',
        description='Get a drive item by path',
        method='GET',
        path='/drives/{driveId}/root:/{itemPath}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                },
                'itemPath': {
                    'type': 'string',
                    'description': 'Path to the item (e.g., Documents/report.docx)'
                }
            },
            'required': ['driveId', 'itemPath']
        }
    )

    Action.objects.create(
        resource=drive_items,
        alias='download',
        name='download',
        description='Get download URL for a file',
        method='GET',
        path='/drives/{driveId}/items/{itemId}/content',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                },
                'itemId': {
                    'type': 'string',
                    'description': 'The file item ID'
                }
            },
            'required': ['driveId', 'itemId']
        }
    )

    Action.objects.create(
        resource=drive_items,
        alias='upload_small',
        name='upload_small',
        description='Upload a small file (up to 4MB)',
        method='PUT',
        path='/drives/{driveId}/items/{parentId}:/{filename}:/content',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                },
                'parentId': {
                    'type': 'string',
                    'description': 'The parent folder ID (use "root" for root folder)'
                },
                'filename': {
                    'type': 'string',
                    'description': 'Name of the file to create'
                },
                'content': {
                    'type': 'string',
                    'description': 'File content (base64 encoded for binary files)'
                }
            },
            'required': ['driveId', 'parentId', 'filename', 'content']
        }
    )

    Action.objects.create(
        resource=drive_items,
        alias='create_folder',
        name='create_folder',
        description='Create a new folder',
        method='POST',
        path='/drives/{driveId}/items/{parentId}/children',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                },
                'parentId': {
                    'type': 'string',
                    'description': 'The parent folder ID (use "root" for root folder)'
                },
                'name': {
                    'type': 'string',
                    'description': 'Folder name'
                },
                'folder': {
                    'type': 'object',
                    'description': 'Empty object to indicate folder creation',
                    'default': {}
                }
            },
            'required': ['driveId', 'parentId', 'name']
        }
    )

    Action.objects.create(
        resource=drive_items,
        alias='delete',
        name='delete',
        description='Delete a file or folder',
        method='DELETE',
        path='/drives/{driveId}/items/{itemId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                },
                'itemId': {
                    'type': 'string',
                    'description': 'The item ID to delete'
                }
            },
            'required': ['driveId', 'itemId']
        }
    )

    Action.objects.create(
        resource=drive_items,
        alias='copy',
        name='copy',
        description='Copy a file or folder to a new location',
        method='POST',
        path='/drives/{driveId}/items/{itemId}/copy',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The source drive ID'
                },
                'itemId': {
                    'type': 'string',
                    'description': 'The item ID to copy'
                },
                'parentReference': {
                    'type': 'object',
                    'description': 'Destination parent reference',
                    'properties': {
                        'driveId': {'type': 'string'},
                        'id': {'type': 'string'}
                    }
                },
                'name': {
                    'type': 'string',
                    'description': 'New name for the copied item (optional)'
                }
            },
            'required': ['driveId', 'itemId', 'parentReference']
        }
    )

    Action.objects.create(
        resource=drive_items,
        alias='search',
        name='search',
        description='Search for files and folders',
        method='GET',
        path='/drives/{driveId}/root/search(q=\'{query}\')',
        parameters_schema={
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The drive ID'
                },
                'query': {
                    'type': 'string',
                    'description': 'Search query'
                }
            },
            'required': ['driveId', 'query']
        }
    )

    print("SharePoint adapter created successfully")


def remove_sharepoint_adapter(apps, schema_editor):
    """Remove SharePoint system and all related objects."""
    System = apps.get_model('systems', 'System')

    System.objects.filter(alias='sharepoint').delete()
    print("SharePoint adapter removed")


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0025_add_powerbi_adapter'),
    ]

    operations = [
        migrations.RunPython(add_sharepoint_adapter, remove_sharepoint_adapter),
    ]
