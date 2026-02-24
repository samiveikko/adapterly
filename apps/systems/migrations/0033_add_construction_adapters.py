"""
Add construction industry adapters: Congrid, Procore, Visma Severa.
Also link Infrakit to construction industry.
"""
from django.db import migrations


def add_construction_adapters(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')
    IndustryTemplate = apps.get_model('systems', 'IndustryTemplate')
    TermMapping = apps.get_model('systems', 'TermMapping')

    # Get construction industry template
    construction = IndustryTemplate.objects.filter(name='construction').first()
    if not construction:
        print("Construction template not found, skipping industry linking")
        return

    # ==========================================================================
    # Link Infrakit to construction industry
    # ==========================================================================
    infrakit = System.objects.filter(alias='infrakit').first()
    if infrakit:
        infrakit.industry = construction
        infrakit.save()
        print("Linked Infrakit to construction industry")

    # ==========================================================================
    # CONGRID - Quality Management for Construction
    # ==========================================================================
    congrid = System.objects.create(
        name='congrid',
        alias='congrid',
        display_name='Congrid',
        description='Quality management and site safety platform for construction. Provides inspections, observations, task management, and TR-measurements.',
        system_type='quality_management',
        icon='clipboard-check',
        website_url='https://congrid.com',
        industry=construction,
        variables={
            'api_url': 'https://api.congrid.com'
        },
        meta={
            'api_version': 'v1',
            'docs_url': 'https://developer.congrid.com'
        },
        is_active=True
    )

    # Congrid API Interface
    congrid_api = Interface.objects.create(
        system=congrid,
        alias='api',
        name='api',
        type='API',
        base_url='https://api.congrid.com/v1',
        auth={
            'type': 'bearer',
            'header': 'Authorization',
            'prefix': 'Bearer'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 100}
    )

    # Congrid Projects
    congrid_projects = Resource.objects.create(
        interface=congrid_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=congrid_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/projects',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=congrid_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/projects/{project_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # Congrid Observations (Havainnot)
    congrid_observations = Resource.objects.create(
        interface=congrid_api, alias='observations', name='observations',
        description='Site observations and quality issues'
    )
    Action.objects.create(
        resource=congrid_observations, alias='list', name='list',
        description='List observations for a project',
        method='GET', path='/projects/{project_id}/observations',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'status': {'type': 'string', 'description': 'Filter by status'},
                'category': {'type': 'string', 'description': 'Filter by category'}
            },
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=congrid_observations, alias='create', name='create',
        description='Create a new observation',
        method='POST', path='/projects/{project_id}/observations',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'title': {'type': 'string', 'description': 'Observation title'},
                'description': {'type': 'string', 'description': 'Observation description'},
                'category': {'type': 'string', 'description': 'Category'},
                'severity': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']}
            },
            'required': ['project_id', 'title']
        }
    )
    Action.objects.create(
        resource=congrid_observations, alias='get', name='get',
        description='Get observation details',
        method='GET', path='/observations/{observation_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'observation_id': {'type': 'string', 'description': 'Observation ID'}},
            'required': ['observation_id']
        }
    )
    Action.objects.create(
        resource=congrid_observations, alias='update', name='update',
        description='Update observation',
        method='PATCH', path='/observations/{observation_id}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'observation_id': {'type': 'string', 'description': 'Observation ID'},
                'status': {'type': 'string', 'description': 'New status'},
                'assignee': {'type': 'string', 'description': 'Assignee user ID'}
            },
            'required': ['observation_id']
        }
    )

    # Congrid Inspections (Tarkastukset)
    congrid_inspections = Resource.objects.create(
        interface=congrid_api, alias='inspections', name='inspections',
        description='Quality inspections and TR-measurements'
    )
    Action.objects.create(
        resource=congrid_inspections, alias='list', name='list',
        description='List inspections for a project',
        method='GET', path='/projects/{project_id}/inspections',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'type': {'type': 'string', 'description': 'Inspection type'}
            },
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=congrid_inspections, alias='get', name='get',
        description='Get inspection details',
        method='GET', path='/inspections/{inspection_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'inspection_id': {'type': 'string', 'description': 'Inspection ID'}},
            'required': ['inspection_id']
        }
    )
    Action.objects.create(
        resource=congrid_inspections, alias='get_results', name='get_results',
        description='Get inspection results/TR score',
        method='GET', path='/inspections/{inspection_id}/results',
        parameters_schema={
            'type': 'object',
            'properties': {'inspection_id': {'type': 'string', 'description': 'Inspection ID'}},
            'required': ['inspection_id']
        }
    )

    # Congrid Tasks
    congrid_tasks = Resource.objects.create(
        interface=congrid_api, alias='tasks', name='tasks',
        description='Task management'
    )
    Action.objects.create(
        resource=congrid_tasks, alias='list', name='list',
        description='List tasks for a project',
        method='GET', path='/projects/{project_id}/tasks',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'status': {'type': 'string', 'description': 'Filter by status'},
                'assignee': {'type': 'string', 'description': 'Filter by assignee'}
            },
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=congrid_tasks, alias='create', name='create',
        description='Create a new task',
        method='POST', path='/projects/{project_id}/tasks',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'title': {'type': 'string', 'description': 'Task title'},
                'description': {'type': 'string', 'description': 'Task description'},
                'due_date': {'type': 'string', 'format': 'date', 'description': 'Due date'},
                'assignee': {'type': 'string', 'description': 'Assignee user ID'}
            },
            'required': ['project_id', 'title']
        }
    )

    # Congrid Companies (Yritykset/Aliurakoitsijat)
    congrid_companies = Resource.objects.create(
        interface=congrid_api, alias='companies', name='companies',
        description='Companies and subcontractors'
    )
    Action.objects.create(
        resource=congrid_companies, alias='list', name='list',
        description='List companies in project',
        method='GET', path='/projects/{project_id}/companies',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # Add Congrid term mappings
    congrid_terms = [
        ('project', 'Project'),
        ('observation', 'Observation'),
        ('inspection', 'Inspection'),
        ('site', 'Worksite'),
        ('contractor', 'Company'),
        ('worker', 'User'),
        ('equipment', 'Equipment'),
    ]
    for canonical_term, system_term in congrid_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=congrid,
            defaults={'system_term': system_term}
        )

    # ==========================================================================
    # PROCORE - Global Construction Management Platform
    # ==========================================================================
    procore = System.objects.create(
        name='procore',
        alias='procore',
        display_name='Procore',
        description='Global construction management platform. Project management, drawings, RFIs, submittals, daily logs, and financials.',
        system_type='project_management',
        icon='building',
        website_url='https://procore.com',
        industry=construction,
        variables={
            'api_url': 'https://api.procore.com'
        },
        meta={
            'api_version': 'v1.0',
            'docs_url': 'https://developers.procore.com'
        },
        is_active=True
    )

    # Procore API Interface
    procore_api = Interface.objects.create(
        system=procore,
        alias='rest',
        name='rest',
        type='API',
        base_url='https://api.procore.com/rest/v1.0',
        auth={
            'type': 'oauth2',
            'authorization_url': 'https://login.procore.com/oauth/authorize',
            'token_url': 'https://login.procore.com/oauth/token',
            'scope': 'read write'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 3600}
    )

    # Procore Projects
    procore_projects = Resource.objects.create(
        interface=procore_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=procore_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/projects',
        parameters_schema={
            'type': 'object',
            'properties': {
                'company_id': {'type': 'integer', 'description': 'Company ID'}
            },
            'required': ['company_id']
        }
    )
    Action.objects.create(
        resource=procore_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/projects/{project_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'integer', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # Procore Daily Logs
    procore_dailylogs = Resource.objects.create(
        interface=procore_api, alias='daily_logs', name='daily_logs',
        description='Daily construction logs'
    )
    Action.objects.create(
        resource=procore_dailylogs, alias='list', name='list',
        description='List daily logs',
        method='GET', path='/projects/{project_id}/daily_logs',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'integer', 'description': 'Project ID'},
                'start_date': {'type': 'string', 'format': 'date'},
                'end_date': {'type': 'string', 'format': 'date'}
            },
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=procore_dailylogs, alias='create', name='create',
        description='Create daily log entry',
        method='POST', path='/projects/{project_id}/daily_logs',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'integer', 'description': 'Project ID'},
                'log_date': {'type': 'string', 'format': 'date'},
                'notes': {'type': 'string'}
            },
            'required': ['project_id', 'log_date']
        }
    )

    # Procore RFIs
    procore_rfis = Resource.objects.create(
        interface=procore_api, alias='rfis', name='rfis',
        description='Requests for Information'
    )
    Action.objects.create(
        resource=procore_rfis, alias='list', name='list',
        description='List RFIs',
        method='GET', path='/projects/{project_id}/rfis',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'integer', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=procore_rfis, alias='create', name='create',
        description='Create RFI',
        method='POST', path='/projects/{project_id}/rfis',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'integer', 'description': 'Project ID'},
                'subject': {'type': 'string', 'description': 'RFI subject'},
                'question': {'type': 'string', 'description': 'RFI question'},
                'assignee_id': {'type': 'integer', 'description': 'Assignee ID'}
            },
            'required': ['project_id', 'subject', 'question']
        }
    )

    # Procore Drawings
    procore_drawings = Resource.objects.create(
        interface=procore_api, alias='drawings', name='drawings',
        description='Construction drawings and plans'
    )
    Action.objects.create(
        resource=procore_drawings, alias='list', name='list',
        description='List drawings',
        method='GET', path='/projects/{project_id}/drawings',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'integer', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # Procore Submittals
    procore_submittals = Resource.objects.create(
        interface=procore_api, alias='submittals', name='submittals',
        description='Submittals workflow'
    )
    Action.objects.create(
        resource=procore_submittals, alias='list', name='list',
        description='List submittals',
        method='GET', path='/projects/{project_id}/submittals',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'integer', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # Add Procore term mappings
    procore_terms = [
        ('project', 'Project'),
        ('site', 'Jobsite'),
        ('drawing', 'Drawing'),
        ('contractor', 'Vendor'),
        ('worker', 'Employee'),
        ('equipment', 'Equipment'),
        ('inspection', 'Inspection'),
        ('material', 'Material'),
        ('schedule', 'Schedule'),
    ]
    for canonical_term, system_term in procore_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=procore,
            defaults={'system_term': system_term}
        )

    # ==========================================================================
    # VISMA SEVERA - ERP/Finance for Construction
    # ==========================================================================
    visma = System.objects.create(
        name='visma_severa',
        alias='visma',
        display_name='Visma Severa',
        description='Project-based ERP and financial management. Project accounting, invoicing, resource planning, and time tracking.',
        system_type='erp',
        icon='cash-stack',
        website_url='https://severa.visma.com',
        industry=construction,
        variables={
            'api_url': 'https://api.severa.visma.com'
        },
        meta={
            'api_version': 'v1',
            'docs_url': 'https://developer.visma.com/severa'
        },
        is_active=True
    )

    # Visma API Interface
    visma_api = Interface.objects.create(
        system=visma,
        alias='api',
        name='api',
        type='API',
        base_url='https://api.severa.visma.com/v1',
        auth={
            'type': 'oauth2',
            'authorization_url': 'https://connect.visma.com/authorize',
            'token_url': 'https://connect.visma.com/token',
            'scope': 'severa'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 60}
    )

    # Visma Projects
    visma_projects = Resource.objects.create(
        interface=visma_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=visma_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/projects',
        parameters_schema={
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'enum': ['active', 'closed', 'all']},
                'modified_since': {'type': 'string', 'format': 'date-time'}
            }
        }
    )
    Action.objects.create(
        resource=visma_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/projects/{project_code}',
        parameters_schema={
            'type': 'object',
            'properties': {'project_code': {'type': 'string', 'description': 'Project code'}},
            'required': ['project_code']
        }
    )
    Action.objects.create(
        resource=visma_projects, alias='get_financials', name='get_financials',
        description='Get project financial summary',
        method='GET', path='/projects/{project_code}/financials',
        parameters_schema={
            'type': 'object',
            'properties': {'project_code': {'type': 'string', 'description': 'Project code'}},
            'required': ['project_code']
        }
    )

    # Visma Invoices
    visma_invoices = Resource.objects.create(
        interface=visma_api, alias='invoices', name='invoices',
        description='Invoice management'
    )
    Action.objects.create(
        resource=visma_invoices, alias='list', name='list',
        description='List invoices',
        method='GET', path='/invoices',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_code': {'type': 'string', 'description': 'Filter by project'},
                'status': {'type': 'string', 'enum': ['draft', 'sent', 'paid', 'overdue']},
                'from_date': {'type': 'string', 'format': 'date'},
                'to_date': {'type': 'string', 'format': 'date'}
            }
        }
    )
    Action.objects.create(
        resource=visma_invoices, alias='get', name='get',
        description='Get invoice details',
        method='GET', path='/invoices/{invoice_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'invoice_id': {'type': 'string', 'description': 'Invoice ID'}},
            'required': ['invoice_id']
        }
    )

    # Visma Time Entries
    visma_time = Resource.objects.create(
        interface=visma_api, alias='time_entries', name='time_entries',
        description='Time tracking'
    )
    Action.objects.create(
        resource=visma_time, alias='list', name='list',
        description='List time entries',
        method='GET', path='/time-entries',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_code': {'type': 'string', 'description': 'Filter by project'},
                'user_id': {'type': 'string', 'description': 'Filter by user'},
                'from_date': {'type': 'string', 'format': 'date'},
                'to_date': {'type': 'string', 'format': 'date'}
            }
        }
    )
    Action.objects.create(
        resource=visma_time, alias='create', name='create',
        description='Create time entry',
        method='POST', path='/time-entries',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_code': {'type': 'string', 'description': 'Project code'},
                'date': {'type': 'string', 'format': 'date'},
                'hours': {'type': 'number', 'description': 'Hours worked'},
                'description': {'type': 'string', 'description': 'Work description'}
            },
            'required': ['project_code', 'date', 'hours']
        }
    )

    # Visma Expenses
    visma_expenses = Resource.objects.create(
        interface=visma_api, alias='expenses', name='expenses',
        description='Expense management'
    )
    Action.objects.create(
        resource=visma_expenses, alias='list', name='list',
        description='List expenses',
        method='GET', path='/expenses',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_code': {'type': 'string', 'description': 'Filter by project'},
                'from_date': {'type': 'string', 'format': 'date'},
                'to_date': {'type': 'string', 'format': 'date'}
            }
        }
    )

    # Visma Customers
    visma_customers = Resource.objects.create(
        interface=visma_api, alias='customers', name='customers',
        description='Customer management'
    )
    Action.objects.create(
        resource=visma_customers, alias='list', name='list',
        description='List customers',
        method='GET', path='/customers',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=visma_customers, alias='get', name='get',
        description='Get customer details',
        method='GET', path='/customers/{customer_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'customer_id': {'type': 'string', 'description': 'Customer ID'}},
            'required': ['customer_id']
        }
    )

    # Add Visma term mappings
    visma_terms = [
        ('project', 'Projekti'),
        ('contractor', 'Toimittaja'),
        ('worker', 'Henkilö'),
        ('company', 'Asiakas'),
        ('material', 'Tuote'),
    ]
    for canonical_term, system_term in visma_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=visma,
            defaults={'system_term': system_term}
        )

    print("Created construction adapters: Congrid, Procore, Visma Severa")


def remove_construction_adapters(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    System.objects.filter(alias__in=['congrid', 'procore', 'visma']).delete()

    # Unlink Infrakit from industry
    infrakit = System.objects.filter(alias='infrakit').first()
    if infrakit:
        infrakit.industry = None
        infrakit.save()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0032_add_system_industry_field'),
    ]

    operations = [
        migrations.RunPython(add_construction_adapters, remove_construction_adapters),
    ]
