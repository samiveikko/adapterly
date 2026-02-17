"""
Add Sitedrive and Takting - Construction scheduling and takt planning tools.
"""
from django.db import migrations


def add_sitedrive_and_takting(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')
    IndustryTemplate = apps.get_model('systems', 'IndustryTemplate')
    TermMapping = apps.get_model('systems', 'TermMapping')

    # Get construction industry template
    construction = IndustryTemplate.objects.filter(name='construction').first()

    # Helper to create actions
    def create_actions(resource, actions):
        for action_def in actions:
            Action.objects.get_or_create(
                resource=resource, alias=action_def[0],
                defaults={
                    'name': action_def[0],
                    'method': action_def[1],
                    'path': action_def[2],
                    'description': action_def[3],
                    'parameters_schema': {'type': 'object', 'properties': {}},
                }
            )

    # ==========================================================================
    # SITEDRIVE - Construction Production Planning
    # ==========================================================================
    sitedrive, _ = System.objects.get_or_create(
        alias='sitedrive',
        defaults={
            'name': 'sitedrive',
            'display_name': 'Sitedrive',
            'description': 'Construction production planning with factory-like precision. Takt planning, Gantt charts, real-time progress tracking. Used by Skanska, Hartela, Saint-Gobain. 300+ jobsites.',
            'system_type': 'project_management',
            'icon': 'speedometer2',
            'website_url': 'https://www.sitedrive.com',
            'industry': construction,
            'variables': {'api_url': 'https://api.sitedrive.com'},
            'meta': {'api_version': 'v1', 'countries': ['FI', 'NO', 'SE', 'DK', 'CZ', 'ES', 'FR']},
            'is_active': True,
        }
    )

    sitedrive_api, _ = Interface.objects.get_or_create(
        system=sitedrive, alias='api',
        defaults={
            'name': 'api', 'type': 'API',
            'base_url': 'https://api.sitedrive.com/v1',
            'auth': {'type': 'oauth2', 'token_url': 'https://api.sitedrive.com/oauth/token'},
            'rate_limits': {'requests_per_minute': 100},
        }
    )

    # Projects
    sd_projects, _ = Resource.objects.get_or_create(
        interface=sitedrive_api, alias='projects',
        defaults={'name': 'projects', 'description': 'Construction projects'}
    )
    create_actions(sd_projects, [
        ('list', 'GET', '/projects', 'List all projects'),
        ('get', 'GET', '/projects/{project_id}', 'Get project details'),
        ('create', 'POST', '/projects', 'Create new project'),
        ('update', 'PATCH', '/projects/{project_id}', 'Update project'),
        ('get_dashboard', 'GET', '/projects/{project_id}/dashboard', 'Get project dashboard summary'),
        ('get_progress', 'GET', '/projects/{project_id}/progress', 'Get overall project progress'),
    ])

    # Schedules (Takt, Gantt, Task list)
    sd_schedules, _ = Resource.objects.get_or_create(
        interface=sitedrive_api, alias='schedules',
        defaults={'name': 'schedules', 'description': 'Production schedules - Takt, Gantt, task views'}
    )
    create_actions(sd_schedules, [
        ('list', 'GET', '/projects/{project_id}/schedules', 'List schedules'),
        ('get', 'GET', '/schedules/{schedule_id}', 'Get schedule details'),
        ('create', 'POST', '/projects/{project_id}/schedules', 'Create schedule'),
        ('update', 'PATCH', '/schedules/{schedule_id}', 'Update schedule'),
        ('delete', 'DELETE', '/schedules/{schedule_id}', 'Delete schedule'),
        ('get_takt_view', 'GET', '/schedules/{schedule_id}/takt', 'Get takt/flowline view'),
        ('get_gantt_view', 'GET', '/schedules/{schedule_id}/gantt', 'Get Gantt view'),
        ('import_ms_project', 'POST', '/schedules/import/msproject', 'Import from MS Project'),
        ('export_ms_project', 'GET', '/schedules/{schedule_id}/export/msproject', 'Export to MS Project'),
    ])

    # Tasks
    sd_tasks, _ = Resource.objects.get_or_create(
        interface=sitedrive_api, alias='tasks',
        defaults={'name': 'tasks', 'description': 'Production tasks and activities'}
    )
    create_actions(sd_tasks, [
        ('list', 'GET', '/schedules/{schedule_id}/tasks', 'List tasks'),
        ('get', 'GET', '/tasks/{task_id}', 'Get task details'),
        ('create', 'POST', '/schedules/{schedule_id}/tasks', 'Create task'),
        ('update', 'PATCH', '/tasks/{task_id}', 'Update task'),
        ('delete', 'DELETE', '/tasks/{task_id}', 'Delete task'),
        ('update_progress', 'POST', '/tasks/{task_id}/progress', 'Update task progress'),
        ('add_obstacle', 'POST', '/tasks/{task_id}/obstacles', 'Report obstacle/blocker'),
        ('resolve_obstacle', 'POST', '/obstacles/{obstacle_id}/resolve', 'Resolve obstacle'),
    ])

    # Locations (zones, floors, areas)
    sd_locations, _ = Resource.objects.get_or_create(
        interface=sitedrive_api, alias='locations',
        defaults={'name': 'locations', 'description': 'Project locations - zones, floors, areas for takt planning'}
    )
    create_actions(sd_locations, [
        ('list', 'GET', '/projects/{project_id}/locations', 'List locations'),
        ('get', 'GET', '/locations/{location_id}', 'Get location details'),
        ('create', 'POST', '/projects/{project_id}/locations', 'Create location'),
        ('update', 'PATCH', '/locations/{location_id}', 'Update location'),
        ('get_progress', 'GET', '/locations/{location_id}/progress', 'Get location progress'),
        ('get_tasks', 'GET', '/locations/{location_id}/tasks', 'Get tasks at location'),
    ])

    # Trades / Work crews
    sd_trades, _ = Resource.objects.get_or_create(
        interface=sitedrive_api, alias='trades',
        defaults={'name': 'trades', 'description': 'Trades and work crews'}
    )
    create_actions(sd_trades, [
        ('list', 'GET', '/projects/{project_id}/trades', 'List trades'),
        ('get', 'GET', '/trades/{trade_id}', 'Get trade details'),
        ('create', 'POST', '/projects/{project_id}/trades', 'Create trade'),
        ('update', 'PATCH', '/trades/{trade_id}', 'Update trade'),
        ('get_workload', 'GET', '/trades/{trade_id}/workload', 'Get trade workload'),
    ])

    # Obstacles / Issues
    sd_obstacles, _ = Resource.objects.get_or_create(
        interface=sitedrive_api, alias='obstacles',
        defaults={'name': 'obstacles', 'description': 'Production obstacles and blockers'}
    )
    create_actions(sd_obstacles, [
        ('list', 'GET', '/projects/{project_id}/obstacles', 'List all obstacles'),
        ('get', 'GET', '/obstacles/{obstacle_id}', 'Get obstacle details'),
        ('create', 'POST', '/tasks/{task_id}/obstacles', 'Create obstacle'),
        ('update', 'PATCH', '/obstacles/{obstacle_id}', 'Update obstacle'),
        ('resolve', 'POST', '/obstacles/{obstacle_id}/resolve', 'Resolve obstacle'),
        ('list_open', 'GET', '/projects/{project_id}/obstacles/open', 'List open obstacles'),
    ])

    # Reports
    sd_reports, _ = Resource.objects.get_or_create(
        interface=sitedrive_api, alias='reports',
        defaults={'name': 'reports', 'description': 'Production reports and analytics'}
    )
    create_actions(sd_reports, [
        ('get_progress_report', 'GET', '/projects/{project_id}/reports/progress', 'Get progress report'),
        ('get_takt_performance', 'GET', '/projects/{project_id}/reports/takt', 'Get takt performance metrics'),
        ('get_obstacle_summary', 'GET', '/projects/{project_id}/reports/obstacles', 'Get obstacle summary'),
        ('export_powerbi', 'GET', '/projects/{project_id}/reports/powerbi', 'Export data for Power BI'),
    ])

    # ==========================================================================
    # TAKTING - Takt Planning for Construction
    # ==========================================================================
    takting, _ = System.objects.get_or_create(
        alias='takting',
        defaults={
            'name': 'takting',
            'display_name': 'TAKT.ing',
            'description': 'Industrializing construction through takt planning. Flowline scheduling, production leveling, continuous flow optimization for construction projects.',
            'system_type': 'project_management',
            'icon': 'graph-up-arrow',
            'website_url': 'https://takting.com',
            'industry': construction,
            'variables': {'api_url': 'https://api.takting.com'},
            'meta': {'api_version': 'v1', 'focus': 'takt_planning'},
            'is_active': True,
        }
    )

    takting_api, _ = Interface.objects.get_or_create(
        system=takting, alias='api',
        defaults={
            'name': 'api', 'type': 'API',
            'base_url': 'https://api.takting.com/v1',
            'auth': {'type': 'bearer'},
            'rate_limits': {'requests_per_minute': 100},
        }
    )

    # Projects
    takt_projects, _ = Resource.objects.get_or_create(
        interface=takting_api, alias='projects',
        defaults={'name': 'projects', 'description': 'Takt-planned construction projects'}
    )
    create_actions(takt_projects, [
        ('list', 'GET', '/projects', 'List all projects'),
        ('get', 'GET', '/projects/{project_id}', 'Get project details'),
        ('create', 'POST', '/projects', 'Create new project'),
        ('update', 'PATCH', '/projects/{project_id}', 'Update project'),
        ('get_metrics', 'GET', '/projects/{project_id}/metrics', 'Get project takt metrics'),
    ])

    # Takt Plans
    takt_plans, _ = Resource.objects.get_or_create(
        interface=takting_api, alias='takt_plans',
        defaults={'name': 'takt_plans', 'description': 'Takt production plans'}
    )
    create_actions(takt_plans, [
        ('list', 'GET', '/projects/{project_id}/takt-plans', 'List takt plans'),
        ('get', 'GET', '/takt-plans/{plan_id}', 'Get takt plan'),
        ('create', 'POST', '/projects/{project_id}/takt-plans', 'Create takt plan'),
        ('update', 'PATCH', '/takt-plans/{plan_id}', 'Update takt plan'),
        ('delete', 'DELETE', '/takt-plans/{plan_id}', 'Delete takt plan'),
        ('calculate_takt_time', 'POST', '/takt-plans/{plan_id}/calculate', 'Calculate optimal takt time'),
        ('get_flowline', 'GET', '/takt-plans/{plan_id}/flowline', 'Get flowline visualization data'),
        ('balance_workload', 'POST', '/takt-plans/{plan_id}/balance', 'Balance workload across takt areas'),
    ])

    # Takt Areas (zones/wagons)
    takt_areas, _ = Resource.objects.get_or_create(
        interface=takting_api, alias='takt_areas',
        defaults={'name': 'takt_areas', 'description': 'Takt areas / production zones / wagons'}
    )
    create_actions(takt_areas, [
        ('list', 'GET', '/takt-plans/{plan_id}/areas', 'List takt areas'),
        ('get', 'GET', '/takt-areas/{area_id}', 'Get takt area'),
        ('create', 'POST', '/takt-plans/{plan_id}/areas', 'Create takt area'),
        ('update', 'PATCH', '/takt-areas/{area_id}', 'Update takt area'),
        ('delete', 'DELETE', '/takt-areas/{area_id}', 'Delete takt area'),
        ('get_status', 'GET', '/takt-areas/{area_id}/status', 'Get current takt area status'),
        ('handover', 'POST', '/takt-areas/{area_id}/handover', 'Complete handover to next trade'),
    ])

    # Work Packages (activities within takt)
    takt_packages, _ = Resource.objects.get_or_create(
        interface=takting_api, alias='work_packages',
        defaults={'name': 'work_packages', 'description': 'Work packages / activities'}
    )
    create_actions(takt_packages, [
        ('list', 'GET', '/takt-areas/{area_id}/work-packages', 'List work packages'),
        ('get', 'GET', '/work-packages/{package_id}', 'Get work package'),
        ('create', 'POST', '/takt-areas/{area_id}/work-packages', 'Create work package'),
        ('update', 'PATCH', '/work-packages/{package_id}', 'Update work package'),
        ('update_progress', 'POST', '/work-packages/{package_id}/progress', 'Update progress'),
        ('complete', 'POST', '/work-packages/{package_id}/complete', 'Mark as complete'),
    ])

    # Trades / Crews
    takt_trades, _ = Resource.objects.get_or_create(
        interface=takting_api, alias='trades',
        defaults={'name': 'trades', 'description': 'Trades and work crews'}
    )
    create_actions(takt_trades, [
        ('list', 'GET', '/projects/{project_id}/trades', 'List trades'),
        ('get', 'GET', '/trades/{trade_id}', 'Get trade'),
        ('create', 'POST', '/projects/{project_id}/trades', 'Create trade'),
        ('update', 'PATCH', '/trades/{trade_id}', 'Update trade'),
        ('get_capacity', 'GET', '/trades/{trade_id}/capacity', 'Get trade capacity'),
        ('get_schedule', 'GET', '/trades/{trade_id}/schedule', 'Get trade schedule'),
    ])

    # Takt Control (daily management)
    takt_control, _ = Resource.objects.get_or_create(
        interface=takting_api, alias='takt_control',
        defaults={'name': 'takt_control', 'description': 'Daily takt control and production meetings'}
    )
    create_actions(takt_control, [
        ('get_daily_status', 'GET', '/projects/{project_id}/daily-status', 'Get daily takt status'),
        ('report_variance', 'POST', '/takt-areas/{area_id}/variance', 'Report takt variance'),
        ('get_variances', 'GET', '/projects/{project_id}/variances', 'Get all variances'),
        ('create_countermeasure', 'POST', '/variances/{variance_id}/countermeasure', 'Create countermeasure'),
        ('get_ppc', 'GET', '/projects/{project_id}/ppc', 'Get Percent Plan Complete'),
    ])

    # Analytics
    takt_analytics, _ = Resource.objects.get_or_create(
        interface=takting_api, alias='analytics',
        defaults={'name': 'analytics', 'description': 'Takt analytics and performance metrics'}
    )
    create_actions(takt_analytics, [
        ('get_takt_time_analysis', 'GET', '/projects/{project_id}/analytics/takt-time', 'Analyze takt time performance'),
        ('get_flow_efficiency', 'GET', '/projects/{project_id}/analytics/flow', 'Get flow efficiency metrics'),
        ('get_waste_analysis', 'GET', '/projects/{project_id}/analytics/waste', 'Get waste/muda analysis'),
        ('get_throughput', 'GET', '/projects/{project_id}/analytics/throughput', 'Get throughput metrics'),
        ('compare_plans', 'GET', '/projects/{project_id}/analytics/compare', 'Compare planned vs actual'),
    ])

    # ==========================================================================
    # TERM MAPPINGS
    # ==========================================================================
    if construction:
        # Sitedrive term mappings
        for canonical, system_term in [
            ('schedule', 'Schedule'),
            ('task', 'Task'),
            ('takt', 'Takt'),
            ('location', 'Location'),
            ('trade', 'Trade'),
            ('obstacle', 'Obstacle'),
            ('progress', 'Progress'),
            ('gantt', 'Gantt'),
        ]:
            TermMapping.objects.get_or_create(
                template=construction,
                canonical_term=canonical,
                system=sitedrive,
                defaults={'system_term': system_term}
            )

        # Takting term mappings
        for canonical, system_term in [
            ('schedule', 'Takt Plan'),
            ('task', 'Work Package'),
            ('takt', 'Takt'),
            ('location', 'Takt Area'),
            ('trade', 'Trade'),
            ('takt_time', 'Takt Time'),
            ('flowline', 'Flowline'),
            ('wagon', 'Wagon'),
            ('handover', 'Handover'),
            ('ppc', 'PPC'),
        ]:
            TermMapping.objects.get_or_create(
                template=construction,
                canonical_term=canonical,
                system=takting,
                defaults={'system_term': system_term}
            )


def remove_sitedrive_and_takting(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    System.objects.filter(alias__in=['sitedrive', 'takting']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0040_add_logistics_industry'),
    ]

    operations = [
        migrations.RunPython(add_sitedrive_and_takting, remove_sitedrive_and_takting),
    ]
