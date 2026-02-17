"""
Add scheduling and site monitoring adapters for construction:
- Aiforsite (AI-based site monitoring)
- Oracle Primavera P6 (enterprise scheduling)
- Vico Office / Schedule Planner (location-based scheduling)
- Microsoft Project (scheduling)
- Fira Site (site management)
"""
from django.db import migrations


def add_scheduling_and_monitoring_adapters(apps, schema_editor):
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
    # AIFORSITE - AI-Based Site Monitoring
    # ==========================================================================
    aiforsite = System.objects.create(
        name='aiforsite',
        alias='aiforsite',
        display_name='Aiforsite',
        description='Aiforsite - AI-powered construction site monitoring. Real-time situational awareness, progress tracking, safety monitoring, and resource utilization through cameras and sensors.',
        system_type='monitoring',
        icon='camera-video',
        website_url='https://aiforsite.com',
        industry=construction,
        variables={
            'api_url': 'https://api.aiforsite.com'
        },
        meta={
            'api_version': 'v1',
            'market': 'Finland, Nordics'
        },
        is_active=True
    )

    # Aiforsite API
    aiforsite_api = Interface.objects.create(
        system=aiforsite,
        alias='api',
        name='api',
        type='API',
        base_url='https://api.aiforsite.com/v1',
        auth={
            'type': 'bearer',
            'header': 'Authorization',
            'prefix': 'Bearer'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 60}
    )

    # Aiforsite Sites
    aiforsite_sites = Resource.objects.create(
        interface=aiforsite_api, alias='sites', name='sites',
        description='Construction sites'
    )
    Action.objects.create(
        resource=aiforsite_sites, alias='list', name='list',
        description='List all monitored sites',
        method='GET', path='/sites',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=aiforsite_sites, alias='get', name='get',
        description='Get site details and current status',
        method='GET', path='/sites/{site_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'site_id': {'type': 'string', 'description': 'Site ID'}},
            'required': ['site_id']
        }
    )
    Action.objects.create(
        resource=aiforsite_sites, alias='get_dashboard', name='get_dashboard',
        description='Get site dashboard with KPIs',
        method='GET', path='/sites/{site_id}/dashboard',
        parameters_schema={
            'type': 'object',
            'properties': {'site_id': {'type': 'string', 'description': 'Site ID'}},
            'required': ['site_id']
        }
    )

    # Aiforsite Cameras
    aiforsite_cameras = Resource.objects.create(
        interface=aiforsite_api, alias='cameras', name='cameras',
        description='Site cameras and feeds'
    )
    Action.objects.create(
        resource=aiforsite_cameras, alias='list', name='list',
        description='List cameras at site',
        method='GET', path='/sites/{site_id}/cameras',
        parameters_schema={
            'type': 'object',
            'properties': {'site_id': {'type': 'string', 'description': 'Site ID'}},
            'required': ['site_id']
        }
    )
    Action.objects.create(
        resource=aiforsite_cameras, alias='get_snapshot', name='get_snapshot',
        description='Get latest camera snapshot',
        method='GET', path='/cameras/{camera_id}/snapshot',
        parameters_schema={
            'type': 'object',
            'properties': {'camera_id': {'type': 'string', 'description': 'Camera ID'}},
            'required': ['camera_id']
        }
    )
    Action.objects.create(
        resource=aiforsite_cameras, alias='get_timelapse', name='get_timelapse',
        description='Get camera timelapse for date range',
        method='GET', path='/cameras/{camera_id}/timelapse',
        parameters_schema={
            'type': 'object',
            'properties': {
                'camera_id': {'type': 'string', 'description': 'Camera ID'},
                'from_date': {'type': 'string', 'format': 'date'},
                'to_date': {'type': 'string', 'format': 'date'}
            },
            'required': ['camera_id']
        }
    )

    # Aiforsite Progress
    aiforsite_progress = Resource.objects.create(
        interface=aiforsite_api, alias='progress', name='progress',
        description='Construction progress tracking'
    )
    Action.objects.create(
        resource=aiforsite_progress, alias='get_current', name='get_current',
        description='Get current progress status',
        method='GET', path='/sites/{site_id}/progress',
        parameters_schema={
            'type': 'object',
            'properties': {'site_id': {'type': 'string', 'description': 'Site ID'}},
            'required': ['site_id']
        }
    )
    Action.objects.create(
        resource=aiforsite_progress, alias='get_history', name='get_history',
        description='Get progress history',
        method='GET', path='/sites/{site_id}/progress/history',
        parameters_schema={
            'type': 'object',
            'properties': {
                'site_id': {'type': 'string', 'description': 'Site ID'},
                'from_date': {'type': 'string', 'format': 'date'},
                'to_date': {'type': 'string', 'format': 'date'}
            },
            'required': ['site_id']
        }
    )
    Action.objects.create(
        resource=aiforsite_progress, alias='compare_to_schedule', name='compare_to_schedule',
        description='Compare actual progress to planned schedule',
        method='GET', path='/sites/{site_id}/progress/vs-schedule',
        parameters_schema={
            'type': 'object',
            'properties': {'site_id': {'type': 'string', 'description': 'Site ID'}},
            'required': ['site_id']
        }
    )

    # Aiforsite Resources (workers, equipment)
    aiforsite_resources = Resource.objects.create(
        interface=aiforsite_api, alias='resources', name='resources',
        description='Resource utilization tracking'
    )
    Action.objects.create(
        resource=aiforsite_resources, alias='get_workers', name='get_workers',
        description='Get worker count and trends',
        method='GET', path='/sites/{site_id}/resources/workers',
        parameters_schema={
            'type': 'object',
            'properties': {
                'site_id': {'type': 'string', 'description': 'Site ID'},
                'date': {'type': 'string', 'format': 'date', 'description': 'Specific date'}
            },
            'required': ['site_id']
        }
    )
    Action.objects.create(
        resource=aiforsite_resources, alias='get_equipment', name='get_equipment',
        description='Get equipment utilization',
        method='GET', path='/sites/{site_id}/resources/equipment',
        parameters_schema={
            'type': 'object',
            'properties': {'site_id': {'type': 'string', 'description': 'Site ID'}},
            'required': ['site_id']
        }
    )

    # Aiforsite Safety
    aiforsite_safety = Resource.objects.create(
        interface=aiforsite_api, alias='safety', name='safety',
        description='Safety monitoring'
    )
    Action.objects.create(
        resource=aiforsite_safety, alias='get_alerts', name='get_alerts',
        description='Get safety alerts',
        method='GET', path='/sites/{site_id}/safety/alerts',
        parameters_schema={
            'type': 'object',
            'properties': {
                'site_id': {'type': 'string', 'description': 'Site ID'},
                'severity': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']}
            },
            'required': ['site_id']
        }
    )
    Action.objects.create(
        resource=aiforsite_safety, alias='get_ppe_compliance', name='get_ppe_compliance',
        description='Get PPE compliance statistics',
        method='GET', path='/sites/{site_id}/safety/ppe',
        parameters_schema={
            'type': 'object',
            'properties': {'site_id': {'type': 'string', 'description': 'Site ID'}},
            'required': ['site_id']
        }
    )

    # Aiforsite Weather
    aiforsite_weather = Resource.objects.create(
        interface=aiforsite_api, alias='weather', name='weather',
        description='Site weather data'
    )
    Action.objects.create(
        resource=aiforsite_weather, alias='get_current', name='get_current',
        description='Get current weather at site',
        method='GET', path='/sites/{site_id}/weather',
        parameters_schema={
            'type': 'object',
            'properties': {'site_id': {'type': 'string', 'description': 'Site ID'}},
            'required': ['site_id']
        }
    )
    Action.objects.create(
        resource=aiforsite_weather, alias='get_forecast', name='get_forecast',
        description='Get weather forecast',
        method='GET', path='/sites/{site_id}/weather/forecast',
        parameters_schema={
            'type': 'object',
            'properties': {
                'site_id': {'type': 'string', 'description': 'Site ID'},
                'days': {'type': 'integer', 'description': 'Number of forecast days'}
            },
            'required': ['site_id']
        }
    )

    # Aiforsite term mappings
    aiforsite_terms = [
        ('site', 'Site'),
        ('equipment', 'Equipment'),
        ('worker', 'Worker'),
        ('observation', 'Alert'),
        ('inspection', 'Safety Check'),
    ]
    for canonical_term, system_term in aiforsite_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=aiforsite,
            defaults={'system_term': system_term}
        )

    # ==========================================================================
    # ORACLE PRIMAVERA P6 - Enterprise Project Scheduling
    # ==========================================================================
    primavera = System.objects.create(
        name='primavera_p6',
        alias='primavera',
        display_name='Oracle Primavera P6',
        description='Oracle Primavera P6 - Enterprise project portfolio management and scheduling. Industry standard for large construction and infrastructure projects. CPM scheduling, resource management, and earned value.',
        system_type='project_management',
        icon='calendar3',
        website_url='https://oracle.com/primavera',
        industry=construction,
        variables={
            'api_url': 'https://your-server/p6ws/restapi'
        },
        meta={
            'api_version': 'v1',
            'docs_url': 'https://docs.oracle.com/en/industries/construction-engineering/primavera-p6-eppm/'
        },
        is_active=True
    )

    # Primavera REST API
    primavera_api = Interface.objects.create(
        system=primavera,
        alias='rest',
        name='rest',
        type='API',
        base_url='{base_url}/restapi',
        auth={
            'type': 'basic',
            'header': 'Authorization'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 120}
    )

    # Primavera Projects
    primavera_projects = Resource.objects.create(
        interface=primavera_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=primavera_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/project',
        parameters_schema={
            'type': 'object',
            'properties': {
                'Fields': {'type': 'string', 'description': 'Comma-separated field names to return'}
            }
        }
    )
    Action.objects.create(
        resource=primavera_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/project/{project_id}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'integer', 'description': 'Project ObjectId'},
                'Fields': {'type': 'string', 'description': 'Fields to return'}
            },
            'required': ['project_id']
        }
    )

    # Primavera Activities
    primavera_activities = Resource.objects.create(
        interface=primavera_api, alias='activities', name='activities',
        description='Schedule activities'
    )
    Action.objects.create(
        resource=primavera_activities, alias='list', name='list',
        description='List project activities',
        method='GET', path='/activity',
        parameters_schema={
            'type': 'object',
            'properties': {
                'ProjectObjectId': {'type': 'integer', 'description': 'Project ID'},
                'Fields': {'type': 'string', 'description': 'Fields to return'},
                'Filter': {'type': 'string', 'description': 'Filter expression'}
            },
            'required': ['ProjectObjectId']
        }
    )
    Action.objects.create(
        resource=primavera_activities, alias='get', name='get',
        description='Get activity details',
        method='GET', path='/activity/{activity_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'activity_id': {'type': 'integer', 'description': 'Activity ObjectId'}},
            'required': ['activity_id']
        }
    )
    Action.objects.create(
        resource=primavera_activities, alias='update_progress', name='update_progress',
        description='Update activity progress',
        method='PUT', path='/activity/{activity_id}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'activity_id': {'type': 'integer', 'description': 'Activity ObjectId'},
                'PercentComplete': {'type': 'number', 'description': 'Percent complete'},
                'ActualStartDate': {'type': 'string', 'format': 'date'},
                'ActualFinishDate': {'type': 'string', 'format': 'date'}
            },
            'required': ['activity_id']
        }
    )

    # Primavera Resources
    primavera_resources = Resource.objects.create(
        interface=primavera_api, alias='resources', name='resources',
        description='Resource management'
    )
    Action.objects.create(
        resource=primavera_resources, alias='list', name='list',
        description='List resources',
        method='GET', path='/resource',
        parameters_schema={
            'type': 'object',
            'properties': {
                'Fields': {'type': 'string', 'description': 'Fields to return'}
            }
        }
    )
    Action.objects.create(
        resource=primavera_resources, alias='get_assignments', name='get_assignments',
        description='Get resource assignments',
        method='GET', path='/resourceassignment',
        parameters_schema={
            'type': 'object',
            'properties': {
                'ProjectObjectId': {'type': 'integer', 'description': 'Project ID'},
                'ResourceObjectId': {'type': 'integer', 'description': 'Resource ID'}
            }
        }
    )

    # Primavera WBS
    primavera_wbs = Resource.objects.create(
        interface=primavera_api, alias='wbs', name='wbs',
        description='Work Breakdown Structure'
    )
    Action.objects.create(
        resource=primavera_wbs, alias='list', name='list',
        description='List WBS elements',
        method='GET', path='/wbs',
        parameters_schema={
            'type': 'object',
            'properties': {
                'ProjectObjectId': {'type': 'integer', 'description': 'Project ID'},
                'Fields': {'type': 'string', 'description': 'Fields to return'}
            },
            'required': ['ProjectObjectId']
        }
    )

    # Primavera term mappings
    primavera_terms = [
        ('project', 'Project'),
        ('schedule', 'Activity'),
        ('worker', 'Resource'),
    ]
    for canonical_term, system_term in primavera_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=primavera,
            defaults={'system_term': system_term}
        )

    # ==========================================================================
    # VICO OFFICE / SCHEDULE PLANNER - Location-Based Scheduling
    # ==========================================================================
    vico = System.objects.create(
        name='vico_office',
        alias='vico',
        display_name='Trimble Vico Office',
        description='Trimble Vico Office - Location-based scheduling and 5D BIM. Flowline visualization, production planning, and cost management for construction.',
        system_type='project_management',
        icon='graph-up',
        website_url='https://www.trimble.com/en/products/software/trimble-vico-office',
        industry=construction,
        variables={
            'api_url': 'https://api.vico.trimble.com'
        },
        meta={
            'api_version': 'v1',
            'features': ['5D BIM', 'Location-Based Scheduling', 'Flowline']
        },
        is_active=True
    )

    # Vico API
    vico_api = Interface.objects.create(
        system=vico,
        alias='api',
        name='api',
        type='API',
        base_url='https://api.vico.trimble.com/v1',
        auth={
            'type': 'oauth2',
            'authorization_url': 'https://id.trimble.com/oauth/authorize',
            'token_url': 'https://id.trimble.com/oauth/token',
            'scope': 'vico'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 60}
    )

    # Vico Projects
    vico_projects = Resource.objects.create(
        interface=vico_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=vico_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/projects',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=vico_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/projects/{project_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # Vico Schedules (Flowline)
    vico_schedules = Resource.objects.create(
        interface=vico_api, alias='schedules', name='schedules',
        description='Location-based schedules'
    )
    Action.objects.create(
        resource=vico_schedules, alias='list', name='list',
        description='List project schedules',
        method='GET', path='/projects/{project_id}/schedules',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=vico_schedules, alias='get', name='get',
        description='Get schedule details',
        method='GET', path='/schedules/{schedule_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'schedule_id': {'type': 'string', 'description': 'Schedule ID'}},
            'required': ['schedule_id']
        }
    )
    Action.objects.create(
        resource=vico_schedules, alias='get_flowline', name='get_flowline',
        description='Get flowline data for visualization',
        method='GET', path='/schedules/{schedule_id}/flowline',
        parameters_schema={
            'type': 'object',
            'properties': {'schedule_id': {'type': 'string', 'description': 'Schedule ID'}},
            'required': ['schedule_id']
        }
    )

    # Vico Tasks
    vico_tasks = Resource.objects.create(
        interface=vico_api, alias='tasks', name='tasks',
        description='Schedule tasks'
    )
    Action.objects.create(
        resource=vico_tasks, alias='list', name='list',
        description='List tasks in schedule',
        method='GET', path='/schedules/{schedule_id}/tasks',
        parameters_schema={
            'type': 'object',
            'properties': {
                'schedule_id': {'type': 'string', 'description': 'Schedule ID'},
                'location': {'type': 'string', 'description': 'Filter by location'}
            },
            'required': ['schedule_id']
        }
    )
    Action.objects.create(
        resource=vico_tasks, alias='update_progress', name='update_progress',
        description='Update task progress',
        method='PATCH', path='/tasks/{task_id}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'task_id': {'type': 'string', 'description': 'Task ID'},
                'percent_complete': {'type': 'number'},
                'actual_start': {'type': 'string', 'format': 'date'},
                'actual_finish': {'type': 'string', 'format': 'date'}
            },
            'required': ['task_id']
        }
    )

    # Vico Locations
    vico_locations = Resource.objects.create(
        interface=vico_api, alias='locations', name='locations',
        description='Location breakdown structure'
    )
    Action.objects.create(
        resource=vico_locations, alias='list', name='list',
        description='List project locations',
        method='GET', path='/projects/{project_id}/locations',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # Vico Quantities
    vico_quantities = Resource.objects.create(
        interface=vico_api, alias='quantities', name='quantities',
        description='BIM quantities and costs'
    )
    Action.objects.create(
        resource=vico_quantities, alias='list', name='list',
        description='List quantities by location',
        method='GET', path='/projects/{project_id}/quantities',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'location': {'type': 'string', 'description': 'Filter by location'}
            },
            'required': ['project_id']
        }
    )

    # Vico term mappings
    vico_terms = [
        ('project', 'Project'),
        ('schedule', 'Schedule'),
        ('site', 'Location'),
    ]
    for canonical_term, system_term in vico_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=vico,
            defaults={'system_term': system_term}
        )

    # ==========================================================================
    # MICROSOFT PROJECT - Project Scheduling
    # ==========================================================================
    msproject = System.objects.create(
        name='microsoft_project',
        alias='msproject',
        display_name='Microsoft Project',
        description='Microsoft Project Online and Project for the Web. Project scheduling, resource management, and portfolio management integrated with Microsoft 365.',
        system_type='project_management',
        icon='microsoft',
        website_url='https://www.microsoft.com/en-us/microsoft-365/project/project-management-software',
        industry=construction,
        variables={
            'api_url': 'https://graph.microsoft.com'
        },
        meta={
            'api_version': 'v1.0',
            'docs_url': 'https://docs.microsoft.com/en-us/graph/api/resources/project-rome-overview'
        },
        is_active=True
    )

    # MS Project Graph API
    msproject_api = Interface.objects.create(
        system=msproject,
        alias='graph',
        name='graph',
        type='API',
        base_url='https://graph.microsoft.com/v1.0',
        auth={
            'type': 'oauth2',
            'authorization_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            'scope': 'https://graph.microsoft.com/.default'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 120}
    )

    # MS Project Projects
    msproject_projects = Resource.objects.create(
        interface=msproject_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=msproject_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/sites/{site_id}/lists',
        parameters_schema={
            'type': 'object',
            'properties': {'site_id': {'type': 'string', 'description': 'SharePoint site ID'}},
            'required': ['site_id']
        }
    )

    # MS Project Tasks (Planner)
    msproject_tasks = Resource.objects.create(
        interface=msproject_api, alias='tasks', name='tasks',
        description='Project tasks'
    )
    Action.objects.create(
        resource=msproject_tasks, alias='list', name='list',
        description='List tasks in a plan',
        method='GET', path='/planner/plans/{plan_id}/tasks',
        parameters_schema={
            'type': 'object',
            'properties': {'plan_id': {'type': 'string', 'description': 'Plan ID'}},
            'required': ['plan_id']
        }
    )
    Action.objects.create(
        resource=msproject_tasks, alias='create', name='create',
        description='Create a task',
        method='POST', path='/planner/tasks',
        parameters_schema={
            'type': 'object',
            'properties': {
                'planId': {'type': 'string', 'description': 'Plan ID'},
                'title': {'type': 'string', 'description': 'Task title'},
                'dueDateTime': {'type': 'string', 'format': 'date-time'},
                'assignments': {'type': 'object', 'description': 'User assignments'}
            },
            'required': ['planId', 'title']
        }
    )
    Action.objects.create(
        resource=msproject_tasks, alias='update', name='update',
        description='Update a task',
        method='PATCH', path='/planner/tasks/{task_id}',
        parameters_schema={
            'type': 'object',
            'properties': {
                'task_id': {'type': 'string', 'description': 'Task ID'},
                'percentComplete': {'type': 'integer', 'description': 'Percent complete (0-100)'},
                'title': {'type': 'string'},
                'dueDateTime': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['task_id']
        }
    )

    # MS Project Buckets
    msproject_buckets = Resource.objects.create(
        interface=msproject_api, alias='buckets', name='buckets',
        description='Task buckets/categories'
    )
    Action.objects.create(
        resource=msproject_buckets, alias='list', name='list',
        description='List buckets in a plan',
        method='GET', path='/planner/plans/{plan_id}/buckets',
        parameters_schema={
            'type': 'object',
            'properties': {'plan_id': {'type': 'string', 'description': 'Plan ID'}},
            'required': ['plan_id']
        }
    )

    # MS Project term mappings
    msproject_terms = [
        ('project', 'Plan'),
        ('schedule', 'Task'),
    ]
    for canonical_term, system_term in msproject_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=msproject,
            defaults={'system_term': system_term}
        )

    # ==========================================================================
    # SITEDRIVE (Fira) - Finnish Site Management
    # ==========================================================================
    sitedrive = System.objects.create(
        name='sitedrive',
        alias='sitedrive',
        display_name='SiteDrive',
        description='SiteDrive (by Fira) - Visual site management and scheduling. Takt-time planning, visual control boards, and Last Planner System support.',
        system_type='project_management',
        icon='kanban',
        website_url='https://sitedrive.com',
        industry=construction,
        variables={
            'api_url': 'https://api.sitedrive.com'
        },
        meta={
            'api_version': 'v1',
            'market': 'Finland, Nordics',
            'methodology': 'Lean Construction, Takt Planning'
        },
        is_active=True
    )

    # SiteDrive API
    sitedrive_api = Interface.objects.create(
        system=sitedrive,
        alias='api',
        name='api',
        type='API',
        base_url='https://api.sitedrive.com/v1',
        auth={
            'type': 'bearer',
            'header': 'Authorization',
            'prefix': 'Bearer'
        },
        requires_browser=False,
        rate_limits={'requests_per_minute': 60}
    )

    # SiteDrive Projects
    sitedrive_projects = Resource.objects.create(
        interface=sitedrive_api, alias='projects', name='projects',
        description='Project management'
    )
    Action.objects.create(
        resource=sitedrive_projects, alias='list', name='list',
        description='List all projects',
        method='GET', path='/projects',
        parameters_schema={'type': 'object', 'properties': {}}
    )
    Action.objects.create(
        resource=sitedrive_projects, alias='get', name='get',
        description='Get project details',
        method='GET', path='/projects/{project_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # SiteDrive Schedules (Takt)
    sitedrive_schedules = Resource.objects.create(
        interface=sitedrive_api, alias='schedules', name='schedules',
        description='Takt schedules'
    )
    Action.objects.create(
        resource=sitedrive_schedules, alias='list', name='list',
        description='List project schedules',
        method='GET', path='/projects/{project_id}/schedules',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=sitedrive_schedules, alias='get', name='get',
        description='Get schedule with takt times',
        method='GET', path='/schedules/{schedule_id}',
        parameters_schema={
            'type': 'object',
            'properties': {'schedule_id': {'type': 'string', 'description': 'Schedule ID'}},
            'required': ['schedule_id']
        }
    )
    Action.objects.create(
        resource=sitedrive_schedules, alias='get_takt_board', name='get_takt_board',
        description='Get visual takt board data',
        method='GET', path='/schedules/{schedule_id}/takt-board',
        parameters_schema={
            'type': 'object',
            'properties': {'schedule_id': {'type': 'string', 'description': 'Schedule ID'}},
            'required': ['schedule_id']
        }
    )

    # SiteDrive Tasks
    sitedrive_tasks = Resource.objects.create(
        interface=sitedrive_api, alias='tasks', name='tasks',
        description='Tasks and work packages'
    )
    Action.objects.create(
        resource=sitedrive_tasks, alias='list', name='list',
        description='List tasks in schedule',
        method='GET', path='/schedules/{schedule_id}/tasks',
        parameters_schema={
            'type': 'object',
            'properties': {
                'schedule_id': {'type': 'string', 'description': 'Schedule ID'},
                'zone': {'type': 'string', 'description': 'Filter by zone/location'},
                'trade': {'type': 'string', 'description': 'Filter by trade'}
            },
            'required': ['schedule_id']
        }
    )
    Action.objects.create(
        resource=sitedrive_tasks, alias='update_status', name='update_status',
        description='Update task status',
        method='PATCH', path='/tasks/{task_id}/status',
        parameters_schema={
            'type': 'object',
            'properties': {
                'task_id': {'type': 'string', 'description': 'Task ID'},
                'status': {'type': 'string', 'enum': ['not_started', 'in_progress', 'completed', 'blocked']},
                'percent_complete': {'type': 'integer'},
                'notes': {'type': 'string'}
            },
            'required': ['task_id', 'status']
        }
    )

    # SiteDrive Lookahead
    sitedrive_lookahead = Resource.objects.create(
        interface=sitedrive_api, alias='lookahead', name='lookahead',
        description='Weekly lookahead planning'
    )
    Action.objects.create(
        resource=sitedrive_lookahead, alias='get', name='get',
        description='Get lookahead plan',
        method='GET', path='/projects/{project_id}/lookahead',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'weeks': {'type': 'integer', 'description': 'Number of weeks (default: 4)'}
            },
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=sitedrive_lookahead, alias='get_commitments', name='get_commitments',
        description='Get weekly commitments',
        method='GET', path='/projects/{project_id}/lookahead/commitments',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'week': {'type': 'string', 'format': 'date', 'description': 'Week start date'}
            },
            'required': ['project_id']
        }
    )

    # SiteDrive PPC (Percent Plan Complete)
    sitedrive_ppc = Resource.objects.create(
        interface=sitedrive_api, alias='ppc', name='ppc',
        description='PPC metrics and reasons for variance'
    )
    Action.objects.create(
        resource=sitedrive_ppc, alias='get_metrics', name='get_metrics',
        description='Get PPC metrics',
        method='GET', path='/projects/{project_id}/ppc',
        parameters_schema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'from_date': {'type': 'string', 'format': 'date'},
                'to_date': {'type': 'string', 'format': 'date'}
            },
            'required': ['project_id']
        }
    )
    Action.objects.create(
        resource=sitedrive_ppc, alias='get_variance_reasons', name='get_variance_reasons',
        description='Get reasons for variance',
        method='GET', path='/projects/{project_id}/ppc/variances',
        parameters_schema={
            'type': 'object',
            'properties': {'project_id': {'type': 'string', 'description': 'Project ID'}},
            'required': ['project_id']
        }
    )

    # SiteDrive term mappings
    sitedrive_terms = [
        ('project', 'Project'),
        ('schedule', 'Schedule'),
        ('site', 'Zone'),
        ('contractor', 'Trade'),
    ]
    for canonical_term, system_term in sitedrive_terms:
        TermMapping.objects.get_or_create(
            template=construction,
            canonical_term=canonical_term,
            system=sitedrive,
            defaults={'system_term': system_term}
        )

    print("Created scheduling and monitoring adapters: Aiforsite, Primavera P6, Vico Office, MS Project, SiteDrive")


def remove_scheduling_and_monitoring_adapters(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    System.objects.filter(alias__in=['aiforsite', 'primavera', 'vico', 'msproject', 'sitedrive']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0034_add_bim_and_projectbank_adapters'),
    ]

    operations = [
        migrations.RunPython(add_scheduling_and_monitoring_adapters, remove_scheduling_and_monitoring_adapters),
    ]
