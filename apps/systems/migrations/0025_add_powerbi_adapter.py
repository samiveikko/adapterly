# Generated migration for Power BI adapter

from django.db import migrations


def add_powerbi_adapter(apps, schema_editor):
    """Add Microsoft Power BI system with REST API interface."""
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')
    AuthenticationStep = apps.get_model('systems', 'AuthenticationStep')

    # Create or get Power BI System
    powerbi, created = System.objects.get_or_create(
        alias='powerbi',
        defaults={
            'name': 'powerbi',
            'display_name': 'Microsoft Power BI',
            'description': 'Business analytics service for interactive visualizations and business intelligence',
            'system_type': 'storage',
            'icon': 'bar-chart',
            'website_url': 'https://powerbi.microsoft.com',
            'is_active': True,
            'variables': {},
            'meta': {
                'vendor': 'Microsoft',
                'category': 'Business Intelligence'
            }
        }
    )

    # Clean up existing interfaces for this system to avoid duplicates
    Interface.objects.filter(system=powerbi).delete()
    AuthenticationStep.objects.filter(system=powerbi).delete()

    # Create Azure AD OAuth2 Authentication Step
    AuthenticationStep.objects.create(
        system=powerbi,
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

    # Create Power BI REST API Interface
    api = Interface.objects.create(
        system=powerbi,
        alias='api',
        name='api',
        type='API',
        base_url='https://api.powerbi.com/v1.0/myorg',
        auth={
            'type': 'oauth2_client_credentials',
            'token_url': 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            'scope': 'https://analysis.windows.net/powerbi/api/.default',
            'grant_type': 'client_credentials'
        },
        requires_browser=False,
        rate_limits={
            'requests_per_minute': 200
        }
    )

    # ========== DATASETS RESOURCE ==========
    datasets = Resource.objects.create(
        interface=api,
        alias='datasets',
        name='datasets',
        description='Power BI datasets management'
    )

    Action.objects.create(
        resource=datasets,
        alias='list',
        name='list',
        description='Returns a list of datasets from My workspace',
        method='GET',
        path='/datasets',
        parameters_schema={
            'type': 'object',
            'properties': {}
        }
    )

    Action.objects.create(
        resource=datasets,
        alias='get',
        name='get',
        description='Returns the specified dataset from My workspace',
        method='GET',
        path='/datasets/{datasetId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'datasetId': {
                    'type': 'string',
                    'description': 'The dataset ID'
                }
            },
            'required': ['datasetId']
        }
    )

    Action.objects.create(
        resource=datasets,
        alias='refresh',
        name='refresh',
        description='Triggers a refresh for the specified dataset',
        method='POST',
        path='/datasets/{datasetId}/refreshes',
        parameters_schema={
            'type': 'object',
            'properties': {
                'datasetId': {
                    'type': 'string',
                    'description': 'The dataset ID'
                },
                'notifyOption': {
                    'type': 'string',
                    'description': 'Mail notification options',
                    'enum': ['NoNotification', 'MailOnFailure', 'MailOnCompletion']
                }
            },
            'required': ['datasetId']
        }
    )

    Action.objects.create(
        resource=datasets,
        alias='get_refresh_history',
        name='get_refresh_history',
        description='Returns the refresh history for the specified dataset',
        method='GET',
        path='/datasets/{datasetId}/refreshes',
        parameters_schema={
            'type': 'object',
            'properties': {
                'datasetId': {
                    'type': 'string',
                    'description': 'The dataset ID'
                },
                '$top': {
                    'type': 'integer',
                    'description': 'The requested number of entries'
                }
            },
            'required': ['datasetId']
        }
    )

    Action.objects.create(
        resource=datasets,
        alias='delete',
        name='delete',
        description='Deletes the specified dataset',
        method='DELETE',
        path='/datasets/{datasetId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'datasetId': {
                    'type': 'string',
                    'description': 'The dataset ID'
                }
            },
            'required': ['datasetId']
        }
    )

    # ========== REPORTS RESOURCE ==========
    reports = Resource.objects.create(
        interface=api,
        alias='reports',
        name='reports',
        description='Power BI reports management'
    )

    Action.objects.create(
        resource=reports,
        alias='list',
        name='list',
        description='Returns a list of reports from My workspace',
        method='GET',
        path='/reports',
        parameters_schema={
            'type': 'object',
            'properties': {}
        }
    )

    Action.objects.create(
        resource=reports,
        alias='get',
        name='get',
        description='Returns the specified report from My workspace',
        method='GET',
        path='/reports/{reportId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'reportId': {
                    'type': 'string',
                    'description': 'The report ID'
                }
            },
            'required': ['reportId']
        }
    )

    Action.objects.create(
        resource=reports,
        alias='delete',
        name='delete',
        description='Deletes the specified report',
        method='DELETE',
        path='/reports/{reportId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'reportId': {
                    'type': 'string',
                    'description': 'The report ID'
                }
            },
            'required': ['reportId']
        }
    )

    Action.objects.create(
        resource=reports,
        alias='clone',
        name='clone',
        description='Clones the specified report',
        method='POST',
        path='/reports/{reportId}/Clone',
        parameters_schema={
            'type': 'object',
            'properties': {
                'reportId': {
                    'type': 'string',
                    'description': 'The report ID'
                },
                'name': {
                    'type': 'string',
                    'description': 'The new report name'
                },
                'targetModelId': {
                    'type': 'string',
                    'description': 'Target dataset ID (optional)'
                },
                'targetWorkspaceId': {
                    'type': 'string',
                    'description': 'Target workspace ID (optional)'
                }
            },
            'required': ['reportId', 'name']
        }
    )

    Action.objects.create(
        resource=reports,
        alias='export_to_file',
        name='export_to_file',
        description='Exports the specified report to file format',
        method='POST',
        path='/reports/{reportId}/ExportTo',
        parameters_schema={
            'type': 'object',
            'properties': {
                'reportId': {
                    'type': 'string',
                    'description': 'The report ID'
                },
                'format': {
                    'type': 'string',
                    'description': 'Export format',
                    'enum': ['PDF', 'PNG', 'PPTX']
                }
            },
            'required': ['reportId', 'format']
        }
    )

    # ========== DASHBOARDS RESOURCE ==========
    dashboards = Resource.objects.create(
        interface=api,
        alias='dashboards',
        name='dashboards',
        description='Power BI dashboards management'
    )

    Action.objects.create(
        resource=dashboards,
        alias='list',
        name='list',
        description='Returns a list of dashboards from My workspace',
        method='GET',
        path='/dashboards',
        parameters_schema={
            'type': 'object',
            'properties': {}
        }
    )

    Action.objects.create(
        resource=dashboards,
        alias='get',
        name='get',
        description='Returns the specified dashboard from My workspace',
        method='GET',
        path='/dashboards/{dashboardId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'dashboardId': {
                    'type': 'string',
                    'description': 'The dashboard ID'
                }
            },
            'required': ['dashboardId']
        }
    )

    Action.objects.create(
        resource=dashboards,
        alias='get_tiles',
        name='get_tiles',
        description='Returns a list of tiles within the specified dashboard',
        method='GET',
        path='/dashboards/{dashboardId}/tiles',
        parameters_schema={
            'type': 'object',
            'properties': {
                'dashboardId': {
                    'type': 'string',
                    'description': 'The dashboard ID'
                }
            },
            'required': ['dashboardId']
        }
    )

    # ========== GROUPS (WORKSPACES) RESOURCE ==========
    groups = Resource.objects.create(
        interface=api,
        alias='groups',
        name='groups',
        description='Power BI workspaces (groups) management'
    )

    Action.objects.create(
        resource=groups,
        alias='list',
        name='list',
        description='Returns a list of workspaces the user has access to',
        method='GET',
        path='/groups',
        parameters_schema={
            'type': 'object',
            'properties': {
                '$top': {
                    'type': 'integer',
                    'description': 'Returns only the first n results'
                },
                '$skip': {
                    'type': 'integer',
                    'description': 'Skips the first n results'
                },
                '$filter': {
                    'type': 'string',
                    'description': 'OData filter expression'
                }
            }
        }
    )

    Action.objects.create(
        resource=groups,
        alias='get',
        name='get',
        description='Returns the specified workspace',
        method='GET',
        path='/groups/{groupId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'groupId': {
                    'type': 'string',
                    'description': 'The workspace ID'
                }
            },
            'required': ['groupId']
        }
    )

    Action.objects.create(
        resource=groups,
        alias='create',
        name='create',
        description='Creates a new workspace',
        method='POST',
        path='/groups',
        parameters_schema={
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The workspace name'
                }
            },
            'required': ['name']
        }
    )

    Action.objects.create(
        resource=groups,
        alias='delete',
        name='delete',
        description='Deletes the specified workspace',
        method='DELETE',
        path='/groups/{groupId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'groupId': {
                    'type': 'string',
                    'description': 'The workspace ID'
                }
            },
            'required': ['groupId']
        }
    )

    # ========== IMPORTS RESOURCE ==========
    imports = Resource.objects.create(
        interface=api,
        alias='imports',
        name='imports',
        description='Power BI import operations'
    )

    Action.objects.create(
        resource=imports,
        alias='list',
        name='list',
        description='Returns a list of imports from My workspace',
        method='GET',
        path='/imports',
        parameters_schema={
            'type': 'object',
            'properties': {}
        }
    )

    Action.objects.create(
        resource=imports,
        alias='get',
        name='get',
        description='Returns the specified import from My workspace',
        method='GET',
        path='/imports/{importId}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'importId': {
                    'type': 'string',
                    'description': 'The import ID'
                }
            },
            'required': ['importId']
        }
    )

    print("Power BI adapter created successfully")


def remove_powerbi_adapter(apps, schema_editor):
    """Remove Power BI system and all related objects."""
    System = apps.get_model('systems', 'System')

    System.objects.filter(alias='powerbi').delete()
    print("Power BI adapter removed")


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0024_seed_entity_types'),
    ]

    operations = [
        migrations.RunPython(add_powerbi_adapter, remove_powerbi_adapter),
    ]
