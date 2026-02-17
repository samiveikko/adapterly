"""
Add Admicom Planner - Finland's most popular construction scheduling software.
"""
from django.db import migrations


def add_admicom_planner(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')
    IndustryTemplate = apps.get_model('systems', 'IndustryTemplate')
    TermMapping = apps.get_model('systems', 'TermMapping')

    # Get construction industry template
    construction = IndustryTemplate.objects.filter(name='construction').first()

    # ==========================================================================
    # ADMICOM PLANNER - Finnish Construction Scheduling Software
    # ==========================================================================
    planner = System.objects.create(
        name='admicom_planner',
        alias='admicom_planner',
        display_name='Admicom Planner',
        description='Finland\'s most popular construction scheduling software. Gantt charts, location-based schedules, takt planning, resource allocation, progress monitoring, multi-project management.',
        system_type='project_management',
        icon='calendar-range',
        website_url='https://www.admicom.com/solutions/admicom-planner',
        industry=construction,
        variables={'api_url': 'https://api.admicom.fi/planner'},
        meta={'api_version': 'v1', 'country': 'FI', 'product': 'planner'},
        is_active=True
    )

    planner_api = Interface.objects.create(
        system=planner, alias='api', name='api', type='API',
        base_url='https://api.admicom.fi/planner/v1',
        auth={'type': 'oauth2', 'token_url': 'https://api.admicom.fi/oauth/token'},
        rate_limits={'requests_per_minute': 60}
    )

    # Projects
    planner_projects = Resource.objects.create(
        interface=planner_api, alias='projects', name='projects',
        description='Construction projects and schedules'
    )
    for action_def in [
        ('list', 'GET', '/projects', 'List all projects'),
        ('get', 'GET', '/projects/{project_id}', 'Get project details'),
        ('create', 'POST', '/projects', 'Create new project'),
        ('update', 'PATCH', '/projects/{project_id}', 'Update project'),
        ('get_summary', 'GET', '/projects/{project_id}/summary', 'Get project summary with progress'),
    ]:
        Action.objects.create(
            resource=planner_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Schedules (Gantt, Location-based, Takt)
    planner_schedules = Resource.objects.create(
        interface=planner_api, alias='schedules', name='schedules',
        description='Project schedules - Gantt, location-based, and takt schedules'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_id}/schedules', 'List all schedules for a project'),
        ('get', 'GET', '/schedules/{schedule_id}', 'Get schedule details'),
        ('create', 'POST', '/projects/{project_id}/schedules', 'Create new schedule'),
        ('update', 'PATCH', '/schedules/{schedule_id}', 'Update schedule'),
        ('delete', 'DELETE', '/schedules/{schedule_id}', 'Delete schedule'),
        ('export', 'GET', '/schedules/{schedule_id}/export', 'Export schedule (XML, PDF, Excel)'),
        ('import', 'POST', '/projects/{project_id}/schedules/import', 'Import schedule from file'),
    ]:
        Action.objects.create(
            resource=planner_schedules, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Tasks
    planner_tasks = Resource.objects.create(
        interface=planner_api, alias='tasks', name='tasks',
        description='Schedule tasks and activities'
    )
    for action_def in [
        ('list', 'GET', '/schedules/{schedule_id}/tasks', 'List tasks in schedule'),
        ('get', 'GET', '/tasks/{task_id}', 'Get task details'),
        ('create', 'POST', '/schedules/{schedule_id}/tasks', 'Create task'),
        ('update', 'PATCH', '/tasks/{task_id}', 'Update task'),
        ('delete', 'DELETE', '/tasks/{task_id}', 'Delete task'),
        ('link', 'POST', '/tasks/{task_id}/links', 'Create task dependency link'),
        ('unlink', 'DELETE', '/tasks/{task_id}/links/{link_id}', 'Remove task dependency'),
        ('move', 'POST', '/tasks/{task_id}/move', 'Move task in schedule'),
        ('update_progress', 'PATCH', '/tasks/{task_id}/progress', 'Update task progress'),
    ]:
        Action.objects.create(
            resource=planner_tasks, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Resources (workers, equipment, materials)
    planner_resources = Resource.objects.create(
        interface=planner_api, alias='resources', name='resources',
        description='Resources - workers, equipment, materials for scheduling'
    )
    for action_def in [
        ('list', 'GET', '/resources', 'List all resources'),
        ('get', 'GET', '/resources/{resource_id}', 'Get resource details'),
        ('create', 'POST', '/resources', 'Create resource'),
        ('update', 'PATCH', '/resources/{resource_id}', 'Update resource'),
        ('get_availability', 'GET', '/resources/{resource_id}/availability', 'Get resource availability'),
        ('assign_to_task', 'POST', '/tasks/{task_id}/resources', 'Assign resource to task'),
        ('get_utilization', 'GET', '/resources/{resource_id}/utilization', 'Get resource utilization report'),
    ]:
        Action.objects.create(
            resource=planner_resources, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Locations (for location-based scheduling)
    planner_locations = Resource.objects.create(
        interface=planner_api, alias='locations', name='locations',
        description='Locations/sections for location-based scheduling'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_id}/locations', 'List project locations/sections'),
        ('get', 'GET', '/locations/{location_id}', 'Get location details'),
        ('create', 'POST', '/projects/{project_id}/locations', 'Create location/section'),
        ('update', 'PATCH', '/locations/{location_id}', 'Update location'),
        ('get_progress', 'GET', '/locations/{location_id}/progress', 'Get location progress'),
    ]:
        Action.objects.create(
            resource=planner_locations, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Progress tracking
    planner_progress = Resource.objects.create(
        interface=planner_api, alias='progress', name='progress',
        description='Progress monitoring and tracking'
    )
    for action_def in [
        ('get_project_progress', 'GET', '/projects/{project_id}/progress', 'Get overall project progress'),
        ('get_schedule_progress', 'GET', '/schedules/{schedule_id}/progress', 'Get schedule progress'),
        ('create_update', 'POST', '/projects/{project_id}/progress-updates', 'Create progress update'),
        ('list_updates', 'GET', '/projects/{project_id}/progress-updates', 'List progress updates'),
        ('get_baseline_comparison', 'GET', '/schedules/{schedule_id}/baseline-comparison', 'Compare to baseline'),
    ]:
        Action.objects.create(
            resource=planner_progress, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Baselines
    planner_baselines = Resource.objects.create(
        interface=planner_api, alias='baselines', name='baselines',
        description='Schedule baselines for comparison'
    )
    for action_def in [
        ('list', 'GET', '/schedules/{schedule_id}/baselines', 'List baselines'),
        ('create', 'POST', '/schedules/{schedule_id}/baselines', 'Save current as baseline'),
        ('get', 'GET', '/baselines/{baseline_id}', 'Get baseline details'),
        ('delete', 'DELETE', '/baselines/{baseline_id}', 'Delete baseline'),
    ]:
        Action.objects.create(
            resource=planner_baselines, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Term mappings for construction industry
    if construction:
        term_mappings = [
            ('schedule', 'Aikataulu'),
            ('task', 'Tehtävä'),
            ('milestone', 'Välitavoite'),
            ('baseline', 'Vertailupohja'),
            ('location', 'Lohko'),
            ('progress', 'Edistymä'),
            ('resource', 'Resurssi'),
            ('gantt', 'Jana-aikataulu'),
            ('takt', 'Tahtiaikataulu'),
        ]
        for canonical, system_term in term_mappings:
            TermMapping.objects.create(
                template=construction,
                canonical_term=canonical,
                system=planner,
                system_term=system_term
            )


def remove_admicom_planner(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    System.objects.filter(alias='admicom_planner').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0038_add_nordic_construction_systems'),
    ]

    operations = [
        migrations.RunPython(add_admicom_planner, remove_admicom_planner),
    ]
