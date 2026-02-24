"""
Add global construction and enterprise systems.
Project management, BIM, scheduling, ERP, documentation, logistics, and collaboration tools.
"""
from django.db import migrations


def add_global_construction_systems(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')
    IndustryTemplate = apps.get_model('systems', 'IndustryTemplate')
    TermMapping = apps.get_model('systems', 'TermMapping')

    # Get industry templates
    construction = IndustryTemplate.objects.filter(name='construction').first()
    logistics = IndustryTemplate.objects.filter(name='logistics').first()

    # Helper to create system with API interface
    def create_system_with_api(
        name, alias, display_name, description, system_type,
        icon, website_url, industry, api_base_url, auth_type='bearer',
        country='US', resources_config=None
    ):
        # Check if already exists by alias or name
        if System.objects.filter(alias=alias).exists():
            print(f"System {alias} already exists (by alias), skipping")
            return None, None
        if System.objects.filter(name=name).exists():
            print(f"System {name} already exists (by name), skipping")
            return None, None

        system = System.objects.create(
            name=name,
            alias=alias,
            display_name=display_name,
            description=description,
            system_type=system_type,
            icon=icon,
            website_url=website_url,
            industry=industry,
            variables={'api_url': api_base_url},
            meta={'api_version': 'v1', 'country': country},
            is_active=True
        )

        auth_config = {'type': auth_type}
        if auth_type == 'oauth2':
            auth_config['token_url'] = f"{api_base_url}/oauth/token"

        interface = Interface.objects.create(
            system=system,
            alias='api',
            name='api',
            type='API',
            base_url=api_base_url,
            auth=auth_config,
            rate_limits={'requests_per_minute': 60}
        )

        # Create resources and actions
        if resources_config:
            for res_config in resources_config:
                resource = Resource.objects.create(
                    interface=interface,
                    alias=res_config['alias'],
                    name=res_config['name'],
                    description=res_config.get('description', '')
                )
                for action_def in res_config.get('actions', []):
                    Action.objects.create(
                        resource=resource,
                        alias=action_def[0],
                        name=action_def[0],
                        method=action_def[1],
                        path=action_def[2],
                        description=action_def[3],
                        parameters_schema={'type': 'object', 'properties': {}}
                    )

        return system, interface

    # ==========================================================================
    # CONSTRUCTION PROJECT MANAGEMENT
    # ==========================================================================

    # Autodesk Construction Cloud (ACC/BIM 360)
    create_system_with_api(
        name='autodesk_construction_cloud',
        alias='acc',
        display_name='Autodesk Construction Cloud',
        description='Unified platform for construction project delivery. Combines BIM 360, PlanGrid, and BuildingConnected. Document management, model coordination, field management.',
        system_type='project_management',
        icon='building',
        website_url='https://construction.autodesk.com',
        industry=construction,
        api_base_url='https://developer.api.autodesk.com',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'ACC Projects',
                'actions': [
                    ('list', 'GET', '/construction/admin/v1/projects', 'List projects'),
                    ('get', 'GET', '/construction/admin/v1/projects/{id}', 'Get project'),
                    ('create', 'POST', '/construction/admin/v1/projects', 'Create project'),
                ]
            },
            {
                'alias': 'documents', 'name': 'documents', 'description': 'Document management',
                'actions': [
                    ('list_folders', 'GET', '/data/v1/projects/{project_id}/folders', 'List folders'),
                    ('list_items', 'GET', '/data/v1/projects/{project_id}/folders/{folder_id}/contents', 'List items'),
                    ('upload', 'POST', '/data/v1/projects/{project_id}/items', 'Upload document'),
                ]
            },
            {
                'alias': 'issues', 'name': 'issues', 'description': 'Issues and RFIs',
                'actions': [
                    ('list', 'GET', '/construction/issues/v1/projects/{project_id}/issues', 'List issues'),
                    ('create', 'POST', '/construction/issues/v1/projects/{project_id}/issues', 'Create issue'),
                    ('update', 'PATCH', '/construction/issues/v1/projects/{project_id}/issues/{id}', 'Update issue'),
                ]
            },
            {
                'alias': 'models', 'name': 'models', 'description': 'Model coordination',
                'actions': [
                    ('list_model_sets', 'GET', '/construction/modelset/v3/projects/{project_id}/model-sets', 'List model sets'),
                    ('get_clashes', 'GET', '/construction/clash/v3/projects/{project_id}/model-sets/{model_set_id}/clashes', 'Get clashes'),
                ]
            },
        ]
    )

    # Procore
    create_system_with_api(
        name='procore',
        alias='procore',
        display_name='Procore',
        description='Construction management platform. Project management, financials, quality & safety, resource management. Used by contractors worldwide.',
        system_type='project_management',
        icon='building-gear',
        website_url='https://www.procore.com',
        industry=construction,
        api_base_url='https://api.procore.com/rest/v1.0',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                    ('create', 'POST', '/projects', 'Create project'),
                ]
            },
            {
                'alias': 'rfis', 'name': 'rfis', 'description': 'Requests for Information',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/rfis', 'List RFIs'),
                    ('create', 'POST', '/projects/{project_id}/rfis', 'Create RFI'),
                    ('get', 'GET', '/projects/{project_id}/rfis/{id}', 'Get RFI'),
                ]
            },
            {
                'alias': 'submittals', 'name': 'submittals', 'description': 'Submittals',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/submittals', 'List submittals'),
                    ('create', 'POST', '/projects/{project_id}/submittals', 'Create submittal'),
                ]
            },
            {
                'alias': 'observations', 'name': 'observations', 'description': 'Safety observations',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/observations', 'List observations'),
                    ('create', 'POST', '/projects/{project_id}/observations', 'Create observation'),
                ]
            },
            {
                'alias': 'budget', 'name': 'budget', 'description': 'Budget and costs',
                'actions': [
                    ('get_budget', 'GET', '/projects/{project_id}/budget', 'Get budget'),
                    ('list_cost_codes', 'GET', '/projects/{project_id}/cost_codes', 'List cost codes'),
                ]
            },
        ]
    )

    # Dalux
    create_system_with_api(
        name='dalux',
        alias='dalux',
        display_name='Dalux',
        description='Construction quality management and BIM viewer. Digital handover, inspection checklists, 360 photo documentation. Danish company, strong in Europe.',
        system_type='quality_management',
        icon='check-circle',
        website_url='https://www.dalux.com',
        industry=construction,
        api_base_url='https://api.dalux.com/v1',
        auth_type='bearer',
        country='DK',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'checklists', 'name': 'checklists', 'description': 'Inspection checklists',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/checklists', 'List checklists'),
                    ('get', 'GET', '/checklists/{id}', 'Get checklist'),
                    ('submit', 'POST', '/checklists/{id}/submit', 'Submit checklist'),
                ]
            },
            {
                'alias': 'issues', 'name': 'issues', 'description': 'Quality issues',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/issues', 'List issues'),
                    ('create', 'POST', '/projects/{project_id}/issues', 'Create issue'),
                    ('update', 'PATCH', '/issues/{id}', 'Update issue'),
                ]
            },
            {
                'alias': 'photos', 'name': 'photos', 'description': '360 photos',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/photos', 'List photos'),
                    ('upload', 'POST', '/projects/{project_id}/photos', 'Upload photo'),
                ]
            },
        ]
    )

    # Oracle Aconex
    create_system_with_api(
        name='oracle_aconex',
        alias='aconex',
        display_name='Oracle Aconex',
        description='Project controls and document management for large capital projects. Mail, document control, workflows. Used in mega-projects worldwide.',
        system_type='project_management',
        icon='building-fill',
        website_url='https://www.oracle.com/construction-engineering/aconex-project-controls',
        industry=construction,
        api_base_url='https://api.aconex.com/api',
        auth_type='oauth2',
        country='AU',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'documents', 'name': 'documents', 'description': 'Documents',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/documents', 'List documents'),
                    ('get', 'GET', '/documents/{id}', 'Get document'),
                    ('upload', 'POST', '/projects/{project_id}/documents', 'Upload document'),
                    ('register', 'POST', '/projects/{project_id}/documents/register', 'Register document'),
                ]
            },
            {
                'alias': 'mail', 'name': 'mail', 'description': 'Project mail',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/mail', 'List mail'),
                    ('send', 'POST', '/projects/{project_id}/mail', 'Send mail'),
                ]
            },
            {
                'alias': 'workflows', 'name': 'workflows', 'description': 'Workflows',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/workflows', 'List workflows'),
                    ('get', 'GET', '/workflows/{id}', 'Get workflow'),
                ]
            },
        ]
    )

    # RIB Software iTWO
    create_system_with_api(
        name='rib_itwo',
        alias='itwo',
        display_name='RIB iTWO',
        description='5D BIM enterprise solution. Cost estimation, scheduling, procurement. Integrates model, cost and time. German company.',
        system_type='erp',
        icon='calculator-fill',
        website_url='https://www.rib-software.com',
        industry=construction,
        api_base_url='https://api.rib-software.com/itwo/v1',
        auth_type='oauth2',
        country='DE',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'estimates', 'name': 'estimates', 'description': 'Cost estimates',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/estimates', 'List estimates'),
                    ('get', 'GET', '/estimates/{id}', 'Get estimate'),
                    ('get_boq', 'GET', '/estimates/{id}/boq', 'Get bill of quantities'),
                ]
            },
            {
                'alias': 'schedules', 'name': 'schedules', 'description': 'Schedules',
                'actions': [
                    ('get', 'GET', '/projects/{project_id}/schedule', 'Get schedule'),
                    ('get_tasks', 'GET', '/projects/{project_id}/schedule/tasks', 'Get tasks'),
                ]
            },
        ]
    )

    # Thinkproject
    create_system_with_api(
        name='thinkproject',
        alias='thinkproject',
        display_name='Thinkproject',
        description='Construction project management platform. Document management, BIM, quality management, CAFM. European market leader.',
        system_type='project_management',
        icon='lightbulb',
        website_url='https://www.thinkproject.com',
        industry=construction,
        api_base_url='https://api.thinkproject.com/v1',
        auth_type='oauth2',
        country='DE',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'documents', 'name': 'documents', 'description': 'Documents',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/documents', 'List documents'),
                    ('upload', 'POST', '/projects/{project_id}/documents', 'Upload document'),
                    ('download', 'GET', '/documents/{id}/download', 'Download document'),
                ]
            },
            {
                'alias': 'defects', 'name': 'defects', 'description': 'Defects and issues',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/defects', 'List defects'),
                    ('create', 'POST', '/projects/{project_id}/defects', 'Create defect'),
                ]
            },
        ]
    )

    # Trimble ProjectSight
    create_system_with_api(
        name='trimble_projectsight',
        alias='projectsight',
        display_name='Trimble ProjectSight',
        description='Construction project management for owners and contractors. Quality management, document control, reporting.',
        system_type='project_management',
        icon='eye',
        website_url='https://www.trimble.com/projectsight',
        industry=construction,
        api_base_url='https://api.projectsight.trimble.com/v1',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'submittals', 'name': 'submittals', 'description': 'Submittals',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/submittals', 'List submittals'),
                    ('create', 'POST', '/projects/{project_id}/submittals', 'Create submittal'),
                ]
            },
            {
                'alias': 'documents', 'name': 'documents', 'description': 'Documents',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/documents', 'List documents'),
                    ('upload', 'POST', '/projects/{project_id}/documents', 'Upload document'),
                ]
            },
        ]
    )

    # Asite
    create_system_with_api(
        name='asite',
        alias='asite',
        display_name='Asite',
        description='Common Data Environment for construction. Document management, BIM, project controls. Used in major infrastructure projects.',
        system_type='project_management',
        icon='folder-symlink',
        website_url='https://www.asite.com',
        industry=construction,
        api_base_url='https://api.asite.com/v1',
        auth_type='bearer',
        country='UK',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'documents', 'name': 'documents', 'description': 'Documents',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/documents', 'List documents'),
                    ('upload', 'POST', '/projects/{project_id}/documents', 'Upload document'),
                    ('get_revisions', 'GET', '/documents/{id}/revisions', 'Get revisions'),
                ]
            },
            {
                'alias': 'forms', 'name': 'forms', 'description': 'Forms and workflows',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/forms', 'List forms'),
                    ('submit', 'POST', '/forms/{id}/submit', 'Submit form'),
                ]
            },
        ]
    )

    # PlanRadar
    create_system_with_api(
        name='planradar',
        alias='planradar',
        display_name='PlanRadar',
        description='Construction and real estate management. Defect management, documentation, progress tracking. Austrian company, strong in Europe.',
        system_type='quality_management',
        icon='clipboard-check',
        website_url='https://www.planradar.com',
        industry=construction,
        api_base_url='https://api.planradar.com/v1',
        auth_type='bearer',
        country='AT',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'tickets', 'name': 'tickets', 'description': 'Defect tickets',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/tickets', 'List tickets'),
                    ('create', 'POST', '/projects/{project_id}/tickets', 'Create ticket'),
                    ('update', 'PATCH', '/tickets/{id}', 'Update ticket'),
                ]
            },
            {
                'alias': 'plans', 'name': 'plans', 'description': 'Floor plans',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/plans', 'List plans'),
                    ('upload', 'POST', '/projects/{project_id}/plans', 'Upload plan'),
                ]
            },
        ]
    )

    # ==========================================================================
    # BIM AND MODEL-BASED TOOLS
    # ==========================================================================

    # Autodesk Revit (Cloud/API)
    create_system_with_api(
        name='autodesk_revit',
        alias='revit',
        display_name='Autodesk Revit',
        description='BIM software for architects, engineers, and contractors. 3D modeling, documentation, collaboration via Autodesk Platform Services.',
        system_type='bim',
        icon='bricks',
        website_url='https://www.autodesk.com/products/revit',
        industry=construction,
        api_base_url='https://developer.api.autodesk.com',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'models', 'name': 'models', 'description': 'Revit models',
                'actions': [
                    ('list', 'GET', '/modelderivative/v2/designdata', 'List models'),
                    ('get_metadata', 'GET', '/modelderivative/v2/designdata/{urn}/metadata', 'Get model metadata'),
                    ('get_properties', 'GET', '/modelderivative/v2/designdata/{urn}/metadata/{guid}/properties', 'Get properties'),
                ]
            },
            {
                'alias': 'viewer', 'name': 'viewer', 'description': 'Viewer service',
                'actions': [
                    ('translate', 'POST', '/modelderivative/v2/designdata/job', 'Translate model'),
                    ('get_manifest', 'GET', '/modelderivative/v2/designdata/{urn}/manifest', 'Get manifest'),
                ]
            },
        ]
    )

    # Archicad
    create_system_with_api(
        name='graphisoft_archicad',
        alias='archicad',
        display_name='Graphisoft Archicad',
        description='BIM software for architects. Architectural design, documentation, collaboration via BIMcloud.',
        system_type='bim',
        icon='building',
        website_url='https://graphisoft.com/archicad',
        industry=construction,
        api_base_url='https://api.bimcloud.com/v1',
        auth_type='oauth2',
        country='HU',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'BIMcloud projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'models', 'name': 'models', 'description': 'Archicad models',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/models', 'List models'),
                    ('get', 'GET', '/models/{id}', 'Get model'),
                    ('get_elements', 'GET', '/models/{id}/elements', 'Get elements'),
                ]
            },
        ]
    )

    # Trimble Connect
    create_system_with_api(
        name='trimble_connect',
        alias='trimble_connect',
        display_name='Trimble Connect',
        description='Open BIM collaboration platform. Model viewing, clash detection, task management. Works with Tekla, SketchUp, etc.',
        system_type='bim',
        icon='cloud-arrow-up',
        website_url='https://connect.trimble.com',
        industry=construction,
        api_base_url='https://app.connect.trimble.com/tc/api/2.0',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'models', 'name': 'models', 'description': 'Models',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/models', 'List models'),
                    ('upload', 'POST', '/projects/{project_id}/models', 'Upload model'),
                    ('get_versions', 'GET', '/models/{id}/versions', 'Get versions'),
                ]
            },
            {
                'alias': 'todos', 'name': 'todos', 'description': 'Tasks/ToDos',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/todos', 'List todos'),
                    ('create', 'POST', '/projects/{project_id}/todos', 'Create todo'),
                ]
            },
        ]
    )

    # BIMcollab
    create_system_with_api(
        name='bimcollab',
        alias='bimcollab',
        display_name='BIMcollab',
        description='BIM issue management and model checking. BCF-based collaboration, integrates with major BIM tools.',
        system_type='bim',
        icon='chat-square-dots',
        website_url='https://www.bimcollab.com',
        industry=construction,
        api_base_url='https://api.bimcollab.com/v1',
        auth_type='bearer',
        country='NL',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'issues', 'name': 'issues', 'description': 'BCF Issues',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/issues', 'List issues'),
                    ('create', 'POST', '/projects/{project_id}/issues', 'Create issue'),
                    ('update', 'PATCH', '/issues/{id}', 'Update issue'),
                ]
            },
            {
                'alias': 'models', 'name': 'models', 'description': 'Models',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/models', 'List models'),
                    ('check', 'POST', '/models/{id}/check', 'Run model check'),
                ]
            },
        ]
    )

    # Allplan
    create_system_with_api(
        name='allplan',
        alias='allplan',
        display_name='Allplan',
        description='BIM software for architecture and engineering. 3D modeling, reinforcement detailing, precast design. German company.',
        system_type='bim',
        icon='rulers',
        website_url='https://www.allplan.com',
        industry=construction,
        api_base_url='https://api.allplan.com/v1',
        auth_type='oauth2',
        country='DE',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'models', 'name': 'models', 'description': 'BIM models',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/models', 'List models'),
                    ('export_ifc', 'POST', '/models/{id}/export/ifc', 'Export IFC'),
                ]
            },
        ]
    )

    # ==========================================================================
    # SCHEDULING AND 4D
    # ==========================================================================

    # Microsoft Project
    create_system_with_api(
        name='microsoft_project',
        alias='msproject',
        display_name='Microsoft Project',
        description='Project management software. Scheduling, resource management, portfolio management. Via Project Online/Project for the Web API.',
        system_type='project_management',
        icon='calendar-range',
        website_url='https://www.microsoft.com/project',
        industry=construction,
        api_base_url='https://graph.microsoft.com/v1.0',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/planner/plans', 'List plans'),
                    ('get', 'GET', '/planner/plans/{id}', 'Get plan'),
                ]
            },
            {
                'alias': 'tasks', 'name': 'tasks', 'description': 'Tasks',
                'actions': [
                    ('list', 'GET', '/planner/plans/{plan_id}/tasks', 'List tasks'),
                    ('create', 'POST', '/planner/plans/{plan_id}/tasks', 'Create task'),
                    ('update', 'PATCH', '/planner/tasks/{id}', 'Update task'),
                ]
            },
        ]
    )

    # Oracle Primavera P6
    create_system_with_api(
        name='oracle_primavera_p6',
        alias='primavera',
        display_name='Oracle Primavera P6',
        description='Enterprise project portfolio management. Scheduling, resource management, risk analysis. Industry standard for large projects.',
        system_type='project_management',
        icon='diagram-3',
        website_url='https://www.oracle.com/primavera',
        industry=construction,
        api_base_url='https://api.oracle.com/primavera/v1',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'activities', 'name': 'activities', 'description': 'Activities',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/activities', 'List activities'),
                    ('get', 'GET', '/activities/{id}', 'Get activity'),
                    ('update_progress', 'PATCH', '/activities/{id}', 'Update progress'),
                ]
            },
            {
                'alias': 'resources', 'name': 'resources', 'description': 'Resources',
                'actions': [
                    ('list', 'GET', '/resources', 'List resources'),
                    ('get_assignments', 'GET', '/projects/{project_id}/assignments', 'Get assignments'),
                ]
            },
        ]
    )

    # Synchro (Bentley)
    create_system_with_api(
        name='bentley_synchro',
        alias='synchro',
        display_name='Bentley Synchro',
        description='4D construction scheduling and simulation. Links schedule to BIM for visual planning. Part of Bentley iTwin.',
        system_type='project_management',
        icon='play-circle',
        website_url='https://www.bentley.com/synchro',
        industry=construction,
        api_base_url='https://api.bentley.com/synchro/v1',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'schedules', 'name': 'schedules', 'description': 'Schedules',
                'actions': [
                    ('get', 'GET', '/projects/{project_id}/schedule', 'Get schedule'),
                    ('get_tasks', 'GET', '/projects/{project_id}/schedule/tasks', 'Get tasks'),
                    ('update_task', 'PATCH', '/tasks/{id}', 'Update task'),
                ]
            },
            {
                'alias': 'simulations', 'name': 'simulations', 'description': '4D simulations',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/simulations', 'List simulations'),
                    ('create', 'POST', '/projects/{project_id}/simulations', 'Create simulation'),
                ]
            },
        ]
    )

    # Asta Powerproject
    create_system_with_api(
        name='asta_powerproject',
        alias='powerproject',
        display_name='Asta Powerproject',
        description='Project planning software for construction. Scheduling, resource management, progress tracking. Popular in UK/Europe.',
        system_type='project_management',
        icon='bar-chart-steps',
        website_url='https://www.elecosoft.com/powerproject',
        industry=construction,
        api_base_url='https://api.astapowerproject.com/v1',
        auth_type='bearer',
        country='UK',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'tasks', 'name': 'tasks', 'description': 'Tasks',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/tasks', 'List tasks'),
                    ('update', 'PATCH', '/tasks/{id}', 'Update task'),
                ]
            },
        ]
    )

    # ==========================================================================
    # ERP AND FINANCE
    # ==========================================================================

    # SAP
    create_system_with_api(
        name='sap',
        alias='sap',
        display_name='SAP',
        description='Enterprise resource planning. Financial management, project accounting, procurement, HR. Global market leader.',
        system_type='erp',
        icon='stack',
        website_url='https://www.sap.com',
        industry=construction,
        api_base_url='https://api.sap.com',
        auth_type='oauth2',
        country='DE',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/sap/opu/odata/sap/API_PROJECT/A_Project', 'List projects'),
                    ('get', 'GET', '/sap/opu/odata/sap/API_PROJECT/A_Project(\'{id}\')', 'Get project'),
                ]
            },
            {
                'alias': 'cost_elements', 'name': 'cost_elements', 'description': 'Cost elements',
                'actions': [
                    ('list', 'GET', '/sap/opu/odata/sap/API_COSTCENTER/A_CostCenter', 'List cost centers'),
                ]
            },
            {
                'alias': 'purchase_orders', 'name': 'purchase_orders', 'description': 'Purchase orders',
                'actions': [
                    ('list', 'GET', '/sap/opu/odata/sap/API_PURCHASEORDER/A_PurchaseOrder', 'List POs'),
                    ('create', 'POST', '/sap/opu/odata/sap/API_PURCHASEORDER/A_PurchaseOrder', 'Create PO'),
                ]
            },
        ]
    )

    # IFS
    create_system_with_api(
        name='ifs',
        alias='ifs',
        display_name='IFS',
        description='Enterprise software for service-centric companies. Project-based ERP, asset management, field service.',
        system_type='erp',
        icon='gear-wide-connected',
        website_url='https://www.ifs.com',
        industry=construction,
        api_base_url='https://api.ifs.com/v1',
        auth_type='oauth2',
        country='SE',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'work_orders', 'name': 'work_orders', 'description': 'Work orders',
                'actions': [
                    ('list', 'GET', '/work-orders', 'List work orders'),
                    ('create', 'POST', '/work-orders', 'Create work order'),
                ]
            },
        ]
    )

    # Visma (Business/Netvisor)
    create_system_with_api(
        name='visma',
        alias='visma',
        display_name='Visma',
        description='Nordic ERP and accounting software. Multiple products: Netvisor (FI), Visma Business (NO/SE), accounting, payroll.',
        system_type='erp',
        icon='calculator',
        website_url='https://www.visma.com',
        industry=construction,
        api_base_url='https://api.visma.com/v1',
        auth_type='oauth2',
        country='NO',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'invoices', 'name': 'invoices', 'description': 'Invoices',
                'actions': [
                    ('list', 'GET', '/invoices', 'List invoices'),
                    ('create', 'POST', '/invoices', 'Create invoice'),
                ]
            },
            {
                'alias': 'employees', 'name': 'employees', 'description': 'Employees',
                'actions': [
                    ('list', 'GET', '/employees', 'List employees'),
                ]
            },
        ]
    )

    # Unit4
    create_system_with_api(
        name='unit4',
        alias='unit4',
        display_name='Unit4',
        description='ERP for people-centric organizations. Project accounting, HR, financial management.',
        system_type='erp',
        icon='briefcase',
        website_url='https://www.unit4.com',
        industry=construction,
        api_base_url='https://api.unit4.com/v1',
        auth_type='oauth2',
        country='NL',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'timesheets', 'name': 'timesheets', 'description': 'Timesheets',
                'actions': [
                    ('list', 'GET', '/timesheets', 'List timesheets'),
                    ('submit', 'POST', '/timesheets', 'Submit timesheet'),
                ]
            },
        ]
    )

    # Microsoft Dynamics 365
    create_system_with_api(
        name='microsoft_dynamics_365',
        alias='dynamics365',
        display_name='Microsoft Dynamics 365',
        description='Business applications platform. Project Operations, Finance, Supply Chain, Field Service.',
        system_type='erp',
        icon='microsoft',
        website_url='https://dynamics.microsoft.com',
        industry=construction,
        api_base_url='https://api.businesscentral.dynamics.com/v2.0',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/companies({company_id})/projects', 'List projects'),
                    ('get', 'GET', '/companies({company_id})/projects({id})', 'Get project'),
                ]
            },
            {
                'alias': 'purchase_invoices', 'name': 'purchase_invoices', 'description': 'Purchase invoices',
                'actions': [
                    ('list', 'GET', '/companies({company_id})/purchaseInvoices', 'List invoices'),
                    ('create', 'POST', '/companies({company_id})/purchaseInvoices', 'Create invoice'),
                ]
            },
        ]
    )

    # Monitor ERP
    create_system_with_api(
        name='monitor_erp',
        alias='monitor',
        display_name='Monitor ERP',
        description='Swedish ERP for manufacturing and project-based companies. Production planning, project management.',
        system_type='erp',
        icon='display',
        website_url='https://www.monitor.se',
        industry=construction,
        api_base_url='https://api.monitor.se/v1',
        auth_type='bearer',
        country='SE',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'orders', 'name': 'orders', 'description': 'Orders',
                'actions': [
                    ('list', 'GET', '/orders', 'List orders'),
                    ('create', 'POST', '/orders', 'Create order'),
                ]
            },
        ]
    )

    # Lemonsoft
    create_system_with_api(
        name='lemonsoft',
        alias='lemonsoft',
        display_name='Lemonsoft',
        description='Finnish ERP for SMEs. Accounting, project management, CRM, warehouse. Popular in Finland.',
        system_type='erp',
        icon='tree',
        website_url='https://www.lemonsoft.fi',
        industry=construction,
        api_base_url='https://api.lemonsoft.fi/v1',
        auth_type='bearer',
        country='FI',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'invoices', 'name': 'invoices', 'description': 'Invoices',
                'actions': [
                    ('list', 'GET', '/invoices', 'List invoices'),
                    ('create', 'POST', '/invoices', 'Create invoice'),
                ]
            },
        ]
    )

    # ==========================================================================
    # SITE DOCUMENTATION AND 360
    # ==========================================================================

    # OpenSpace
    create_system_with_api(
        name='openspace',
        alias='openspace',
        display_name='OpenSpace',
        description='360 photo documentation for construction. AI-powered progress tracking, BIM comparison, visual documentation.',
        system_type='documentation',
        icon='camera-video',
        website_url='https://www.openspace.ai',
        industry=construction,
        api_base_url='https://api.openspace.ai/v1',
        auth_type='bearer',
        country='US',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'captures', 'name': 'captures', 'description': '360 captures',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/captures', 'List captures'),
                    ('get', 'GET', '/captures/{id}', 'Get capture'),
                    ('get_progress', 'GET', '/projects/{project_id}/progress', 'Get progress analysis'),
                ]
            },
            {
                'alias': 'fields', 'name': 'fields', 'description': 'Custom fields',
                'actions': [
                    ('list_notes', 'GET', '/projects/{project_id}/notes', 'List field notes'),
                    ('create_note', 'POST', '/projects/{project_id}/notes', 'Create note'),
                ]
            },
        ]
    )

    # HoloBuilder
    create_system_with_api(
        name='holobuilder',
        alias='holobuilder',
        display_name='HoloBuilder',
        description='360 reality capture and virtual tours for construction. Progress documentation, as-built capture. Now part of Faro.',
        system_type='documentation',
        icon='badge-vr',
        website_url='https://www.holobuilder.com',
        industry=construction,
        api_base_url='https://api.holobuilder.com/v1',
        auth_type='bearer',
        country='DE',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'sheets', 'name': 'sheets', 'description': 'Floor sheets',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/sheets', 'List sheets'),
                    ('get', 'GET', '/sheets/{id}', 'Get sheet'),
                ]
            },
            {
                'alias': 'captures', 'name': 'captures', 'description': '360 captures',
                'actions': [
                    ('list', 'GET', '/sheets/{sheet_id}/captures', 'List captures'),
                    ('upload', 'POST', '/sheets/{sheet_id}/captures', 'Upload capture'),
                ]
            },
        ]
    )

    # NavVis
    create_system_with_api(
        name='navvis',
        alias='navvis',
        display_name='NavVis',
        description='Indoor spatial intelligence. Mobile laser scanning, digital twins, indoor navigation. German company.',
        system_type='documentation',
        icon='geo-alt',
        website_url='https://www.navvis.com',
        industry=construction,
        api_base_url='https://api.navvis.com/v1',
        auth_type='bearer',
        country='DE',
        resources_config=[
            {
                'alias': 'sites', 'name': 'sites', 'description': 'Sites',
                'actions': [
                    ('list', 'GET', '/sites', 'List sites'),
                    ('get', 'GET', '/sites/{id}', 'Get site'),
                ]
            },
            {
                'alias': 'scans', 'name': 'scans', 'description': 'Scans',
                'actions': [
                    ('list', 'GET', '/sites/{site_id}/scans', 'List scans'),
                    ('get', 'GET', '/scans/{id}', 'Get scan'),
                ]
            },
            {
                'alias': 'pois', 'name': 'pois', 'description': 'Points of interest',
                'actions': [
                    ('list', 'GET', '/sites/{site_id}/pois', 'List POIs'),
                    ('create', 'POST', '/sites/{site_id}/pois', 'Create POI'),
                ]
            },
        ]
    )

    # Matterport
    create_system_with_api(
        name='matterport',
        alias='matterport',
        display_name='Matterport',
        description='3D capture and digital twin platform. Immersive virtual tours, measurements, property documentation.',
        system_type='documentation',
        icon='box',
        website_url='https://www.matterport.com',
        industry=construction,
        api_base_url='https://api.matterport.com/api/models/v1',
        auth_type='bearer',
        country='US',
        resources_config=[
            {
                'alias': 'models', 'name': 'models', 'description': '3D models',
                'actions': [
                    ('list', 'GET', '/models', 'List models'),
                    ('get', 'GET', '/models/{id}', 'Get model'),
                    ('get_sweeps', 'GET', '/models/{id}/sweeps', 'Get sweep positions'),
                ]
            },
            {
                'alias': 'measurements', 'name': 'measurements', 'description': 'Measurements',
                'actions': [
                    ('list', 'GET', '/models/{model_id}/measurements', 'List measurements'),
                    ('create', 'POST', '/models/{model_id}/measurements', 'Create measurement'),
                ]
            },
        ]
    )

    # Buildots
    create_system_with_api(
        name='buildots',
        alias='buildots',
        display_name='Buildots',
        description='AI-powered construction monitoring. 360 cameras + AI for automatic progress tracking against schedule.',
        system_type='documentation',
        icon='robot',
        website_url='https://www.buildots.com',
        industry=construction,
        api_base_url='https://api.buildots.com/v1',
        auth_type='bearer',
        country='IL',
        resources_config=[
            {
                'alias': 'projects', 'name': 'projects', 'description': 'Projects',
                'actions': [
                    ('list', 'GET', '/projects', 'List projects'),
                    ('get', 'GET', '/projects/{id}', 'Get project'),
                ]
            },
            {
                'alias': 'captures', 'name': 'captures', 'description': 'Captures',
                'actions': [
                    ('list', 'GET', '/projects/{project_id}/captures', 'List captures'),
                    ('get_analysis', 'GET', '/captures/{id}/analysis', 'Get AI analysis'),
                ]
            },
            {
                'alias': 'progress', 'name': 'progress', 'description': 'Progress tracking',
                'actions': [
                    ('get_dashboard', 'GET', '/projects/{project_id}/progress', 'Get progress dashboard'),
                    ('get_delays', 'GET', '/projects/{project_id}/delays', 'Get delay analysis'),
                ]
            },
        ]
    )

    # ==========================================================================
    # LOGISTICS AND TRANSPORT
    # ==========================================================================

    # DHL
    create_system_with_api(
        name='dhl',
        alias='dhl',
        display_name='DHL',
        description='Global logistics and shipping. Express, freight, supply chain solutions. Track & trace, shipping APIs.',
        system_type='logistics',
        icon='truck',
        website_url='https://www.dhl.com',
        industry=logistics,
        api_base_url='https://api-eu.dhl.com',
        auth_type='bearer',
        country='DE',
        resources_config=[
            {
                'alias': 'shipments', 'name': 'shipments', 'description': 'Shipments',
                'actions': [
                    ('track', 'GET', '/track/shipments', 'Track shipment'),
                    ('create', 'POST', '/express/shipments', 'Create shipment'),
                ]
            },
            {
                'alias': 'rates', 'name': 'rates', 'description': 'Rate quotes',
                'actions': [
                    ('get_rates', 'POST', '/express/rates', 'Get shipping rates'),
                ]
            },
            {
                'alias': 'locations', 'name': 'locations', 'description': 'Service points',
                'actions': [
                    ('find', 'GET', '/location-finder/v1/find-by-address', 'Find service points'),
                ]
            },
        ]
    )

    # DB Schenker
    create_system_with_api(
        name='db_schenker',
        alias='schenker',
        display_name='DB Schenker',
        description='Global logistics provider. Land, air, ocean freight. Part of Deutsche Bahn. Strong in Europe.',
        system_type='logistics',
        icon='train-front',
        website_url='https://www.dbschenker.com',
        industry=logistics,
        api_base_url='https://api.dbschenker.com/v1',
        auth_type='bearer',
        country='DE',
        resources_config=[
            {
                'alias': 'shipments', 'name': 'shipments', 'description': 'Shipments',
                'actions': [
                    ('track', 'GET', '/shipments/{id}/track', 'Track shipment'),
                    ('create', 'POST', '/shipments', 'Create shipment'),
                    ('get', 'GET', '/shipments/{id}', 'Get shipment'),
                ]
            },
            {
                'alias': 'quotes', 'name': 'quotes', 'description': 'Rate quotes',
                'actions': [
                    ('get_quote', 'POST', '/quotes', 'Get quote'),
                ]
            },
        ]
    )

    # DSV
    create_system_with_api(
        name='dsv',
        alias='dsv',
        display_name='DSV',
        description='Global transport and logistics. Road, air, sea freight. Danish company, 3rd largest globally.',
        system_type='logistics',
        icon='globe',
        website_url='https://www.dsv.com',
        industry=logistics,
        api_base_url='https://api.dsv.com/v1',
        auth_type='bearer',
        country='DK',
        resources_config=[
            {
                'alias': 'shipments', 'name': 'shipments', 'description': 'Shipments',
                'actions': [
                    ('track', 'GET', '/shipments/{id}/tracking', 'Track shipment'),
                    ('list', 'GET', '/shipments', 'List shipments'),
                ]
            },
            {
                'alias': 'bookings', 'name': 'bookings', 'description': 'Bookings',
                'actions': [
                    ('create', 'POST', '/bookings', 'Create booking'),
                    ('get', 'GET', '/bookings/{id}', 'Get booking'),
                ]
            },
        ]
    )

    # Kuehne + Nagel
    create_system_with_api(
        name='kuehne_nagel',
        alias='kn',
        display_name='Kuehne + Nagel',
        description='Global logistics company. Sea freight, air freight, overland, contract logistics. Swiss company.',
        system_type='logistics',
        icon='water',
        website_url='https://www.kuehne-nagel.com',
        industry=logistics,
        api_base_url='https://api.kuehne-nagel.com/v1',
        auth_type='bearer',
        country='CH',
        resources_config=[
            {
                'alias': 'shipments', 'name': 'shipments', 'description': 'Shipments',
                'actions': [
                    ('track', 'GET', '/tracking/{reference}', 'Track shipment'),
                    ('list', 'GET', '/shipments', 'List shipments'),
                ]
            },
            {
                'alias': 'quotes', 'name': 'quotes', 'description': 'Quotes',
                'actions': [
                    ('request', 'POST', '/quotes', 'Request quote'),
                ]
            },
        ]
    )

    # Posti
    create_system_with_api(
        name='posti',
        alias='posti',
        display_name='Posti',
        description='Finnish postal and logistics company. Parcels, freight, fulfillment. Finland\'s largest logistics company.',
        system_type='logistics',
        icon='envelope',
        website_url='https://www.posti.fi',
        industry=logistics,
        api_base_url='https://api.posti.fi/v1',
        auth_type='bearer',
        country='FI',
        resources_config=[
            {
                'alias': 'shipments', 'name': 'shipments', 'description': 'Shipments',
                'actions': [
                    ('create', 'POST', '/shipments', 'Create shipment'),
                    ('track', 'GET', '/shipments/{id}/events', 'Track shipment'),
                    ('get_label', 'GET', '/shipments/{id}/label', 'Get label'),
                ]
            },
            {
                'alias': 'pickups', 'name': 'pickups', 'description': 'Pickups',
                'actions': [
                    ('find_points', 'GET', '/pickup-points', 'Find pickup points'),
                ]
            },
        ]
    )

    # Bring
    create_system_with_api(
        name='bring',
        alias='bring',
        display_name='Bring',
        description='Nordic logistics company. Part of Posten Norge. Parcels, express, freight across Nordics.',
        system_type='logistics',
        icon='box-seam',
        website_url='https://www.bring.com',
        industry=logistics,
        api_base_url='https://api.bring.com',
        auth_type='bearer',
        country='NO',
        resources_config=[
            {
                'alias': 'tracking', 'name': 'tracking', 'description': 'Tracking',
                'actions': [
                    ('track', 'GET', '/tracking/v2/track/{id}', 'Track shipment'),
                ]
            },
            {
                'alias': 'booking', 'name': 'booking', 'description': 'Booking',
                'actions': [
                    ('create', 'POST', '/booking/api/booking', 'Create booking'),
                    ('get_prices', 'GET', '/shippingguide/v2/products', 'Get shipping prices'),
                ]
            },
        ]
    )

    # Transporeon
    create_system_with_api(
        name='transporeon',
        alias='transporeon',
        display_name='Transporeon',
        description='Digital freight platform. Transport management, visibility, dock scheduling. Part of Trimble.',
        system_type='logistics',
        icon='diagram-2',
        website_url='https://www.transporeon.com',
        industry=logistics,
        api_base_url='https://api.transporeon.com/v1',
        auth_type='oauth2',
        country='DE',
        resources_config=[
            {
                'alias': 'transports', 'name': 'transports', 'description': 'Transports',
                'actions': [
                    ('list', 'GET', '/transports', 'List transports'),
                    ('create', 'POST', '/transports', 'Create transport'),
                    ('track', 'GET', '/transports/{id}/tracking', 'Track transport'),
                ]
            },
            {
                'alias': 'slots', 'name': 'slots', 'description': 'Time slots',
                'actions': [
                    ('list', 'GET', '/locations/{id}/slots', 'List available slots'),
                    ('book', 'POST', '/locations/{id}/slots', 'Book slot'),
                ]
            },
        ]
    )

    # nShift (Unifaun rebranded)
    create_system_with_api(
        name='nshift',
        alias='nshift',
        display_name='nShift',
        description='Delivery and experience management. Multi-carrier shipping platform. Formerly Unifaun. Nordic market leader.',
        system_type='logistics',
        icon='shuffle',
        website_url='https://www.nshift.com',
        industry=logistics,
        api_base_url='https://api.nshift.com/v1',
        auth_type='bearer',
        country='SE',
        resources_config=[
            {
                'alias': 'shipments', 'name': 'shipments', 'description': 'Shipments',
                'actions': [
                    ('create', 'POST', '/shipments', 'Create shipment'),
                    ('track', 'GET', '/shipments/{id}/events', 'Track shipment'),
                    ('get_label', 'GET', '/shipments/{id}/labels', 'Get labels'),
                ]
            },
            {
                'alias': 'carriers', 'name': 'carriers', 'description': 'Carriers',
                'actions': [
                    ('list', 'GET', '/carriers', 'List carriers'),
                    ('get_services', 'GET', '/carriers/{id}/services', 'Get carrier services'),
                ]
            },
        ]
    )

    # ==========================================================================
    # GENERAL INTEGRATIONS / COLLABORATION
    # ==========================================================================

    # Create general industry template if not exists
    general, _ = IndustryTemplate.objects.get_or_create(
        name='general',
        defaults={
            'display_name': 'General / Cross-Industry',
            'description': 'General purpose integrations that work across industries. Communication, storage, signatures.',
            'icon': 'grid',
            'is_active': True
        }
    )

    # Microsoft Teams
    create_system_with_api(
        name='microsoft_teams',
        alias='teams',
        display_name='Microsoft Teams',
        description='Team collaboration and communication. Chat, meetings, file sharing, integrations via Graph API.',
        system_type='collaboration',
        icon='chat-dots',
        website_url='https://www.microsoft.com/teams',
        industry=general,
        api_base_url='https://graph.microsoft.com/v1.0',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'teams', 'name': 'teams', 'description': 'Teams',
                'actions': [
                    ('list', 'GET', '/me/joinedTeams', 'List joined teams'),
                    ('get', 'GET', '/teams/{id}', 'Get team'),
                ]
            },
            {
                'alias': 'channels', 'name': 'channels', 'description': 'Channels',
                'actions': [
                    ('list', 'GET', '/teams/{team_id}/channels', 'List channels'),
                    ('create', 'POST', '/teams/{team_id}/channels', 'Create channel'),
                ]
            },
            {
                'alias': 'messages', 'name': 'messages', 'description': 'Messages',
                'actions': [
                    ('list', 'GET', '/teams/{team_id}/channels/{channel_id}/messages', 'List messages'),
                    ('send', 'POST', '/teams/{team_id}/channels/{channel_id}/messages', 'Send message'),
                ]
            },
        ]
    )

    # Slack
    create_system_with_api(
        name='slack',
        alias='slack',
        display_name='Slack',
        description='Business communication platform. Channels, direct messages, integrations, workflows.',
        system_type='collaboration',
        icon='slack',
        website_url='https://slack.com',
        industry=general,
        api_base_url='https://slack.com/api',
        auth_type='bearer',
        country='US',
        resources_config=[
            {
                'alias': 'channels', 'name': 'channels', 'description': 'Channels',
                'actions': [
                    ('list', 'GET', '/conversations.list', 'List channels'),
                    ('create', 'POST', '/conversations.create', 'Create channel'),
                    ('info', 'GET', '/conversations.info', 'Get channel info'),
                ]
            },
            {
                'alias': 'messages', 'name': 'messages', 'description': 'Messages',
                'actions': [
                    ('post', 'POST', '/chat.postMessage', 'Post message'),
                    ('history', 'GET', '/conversations.history', 'Get message history'),
                ]
            },
            {
                'alias': 'users', 'name': 'users', 'description': 'Users',
                'actions': [
                    ('list', 'GET', '/users.list', 'List users'),
                    ('info', 'GET', '/users.info', 'Get user info'),
                ]
            },
        ]
    )

    # Microsoft SharePoint
    create_system_with_api(
        name='microsoft_sharepoint',
        alias='sharepoint',
        display_name='Microsoft SharePoint',
        description='Document management and collaboration. Sites, lists, document libraries. Via Graph API.',
        system_type='storage',
        icon='share',
        website_url='https://www.microsoft.com/sharepoint',
        industry=general,
        api_base_url='https://graph.microsoft.com/v1.0',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'sites', 'name': 'sites', 'description': 'Sites',
                'actions': [
                    ('list', 'GET', '/sites', 'List sites'),
                    ('get', 'GET', '/sites/{id}', 'Get site'),
                    ('search', 'GET', '/sites?search={query}', 'Search sites'),
                ]
            },
            {
                'alias': 'drives', 'name': 'drives', 'description': 'Document libraries',
                'actions': [
                    ('list', 'GET', '/sites/{site_id}/drives', 'List drives'),
                    ('list_items', 'GET', '/drives/{drive_id}/root/children', 'List items'),
                    ('upload', 'PUT', '/drives/{drive_id}/root:/{path}:/content', 'Upload file'),
                ]
            },
            {
                'alias': 'lists', 'name': 'lists', 'description': 'Lists',
                'actions': [
                    ('list', 'GET', '/sites/{site_id}/lists', 'List lists'),
                    ('get_items', 'GET', '/sites/{site_id}/lists/{list_id}/items', 'Get list items'),
                ]
            },
        ]
    )

    # Google Drive
    create_system_with_api(
        name='google_drive',
        alias='gdrive',
        display_name='Google Drive',
        description='Cloud storage and file synchronization. Documents, spreadsheets, file sharing.',
        system_type='storage',
        icon='google',
        website_url='https://drive.google.com',
        industry=general,
        api_base_url='https://www.googleapis.com/drive/v3',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'files', 'name': 'files', 'description': 'Files',
                'actions': [
                    ('list', 'GET', '/files', 'List files'),
                    ('get', 'GET', '/files/{id}', 'Get file metadata'),
                    ('download', 'GET', '/files/{id}?alt=media', 'Download file'),
                    ('upload', 'POST', '/files', 'Upload file'),
                ]
            },
            {
                'alias': 'folders', 'name': 'folders', 'description': 'Folders',
                'actions': [
                    ('create', 'POST', '/files', 'Create folder'),
                    ('list_contents', 'GET', '/files?q=\'{folder_id}\' in parents', 'List folder contents'),
                ]
            },
        ]
    )

    # DocuSign
    create_system_with_api(
        name='docusign',
        alias='docusign',
        display_name='DocuSign',
        description='Electronic signature and agreement cloud. Sign, send, and manage documents.',
        system_type='collaboration',
        icon='pen',
        website_url='https://www.docusign.com',
        industry=general,
        api_base_url='https://api.docusign.com/restapi/v2.1',
        auth_type='oauth2',
        country='US',
        resources_config=[
            {
                'alias': 'envelopes', 'name': 'envelopes', 'description': 'Envelopes',
                'actions': [
                    ('list', 'GET', '/accounts/{account_id}/envelopes', 'List envelopes'),
                    ('create', 'POST', '/accounts/{account_id}/envelopes', 'Create envelope'),
                    ('get', 'GET', '/accounts/{account_id}/envelopes/{id}', 'Get envelope'),
                    ('send', 'PUT', '/accounts/{account_id}/envelopes/{id}', 'Send envelope'),
                ]
            },
            {
                'alias': 'templates', 'name': 'templates', 'description': 'Templates',
                'actions': [
                    ('list', 'GET', '/accounts/{account_id}/templates', 'List templates'),
                    ('get', 'GET', '/accounts/{account_id}/templates/{id}', 'Get template'),
                ]
            },
        ]
    )

    # ==========================================================================
    # Add term mappings for new construction systems
    # ==========================================================================
    if construction:
        # Get newly created systems
        new_construction_systems = System.objects.filter(
            alias__in=[
                'acc', 'procore', 'dalux', 'aconex', 'itwo', 'thinkproject',
                'projectsight', 'asite', 'planradar', 'revit', 'archicad',
                'trimble_connect', 'bimcollab', 'allplan', 'msproject',
                'primavera', 'synchro', 'powerproject', 'sap', 'ifs',
                'visma', 'unit4', 'dynamics365', 'monitor', 'lemonsoft',
                'openspace', 'holobuilder', 'navvis', 'matterport', 'buildots'
            ]
        )

        term_mappings = [
            # Project management systems
            ('acc', [('project', 'Project'), ('document', 'Document'), ('observation', 'Issue')]),
            ('procore', [('project', 'Project'), ('observation', 'Observation'), ('inspection', 'Inspection')]),
            ('dalux', [('project', 'Project'), ('observation', 'Issue'), ('inspection', 'Checklist')]),
            ('aconex', [('project', 'Project'), ('document', 'Document')]),
            ('itwo', [('project', 'Project'), ('schedule', 'Schedule')]),
            ('thinkproject', [('project', 'Project'), ('document', 'Document'), ('observation', 'Defect')]),
            ('projectsight', [('project', 'Project'), ('document', 'Document')]),
            ('asite', [('project', 'Project'), ('document', 'Document')]),
            ('planradar', [('project', 'Project'), ('observation', 'Ticket')]),
            # BIM systems
            ('revit', [('model', 'Model'), ('drawing', 'View')]),
            ('archicad', [('project', 'Project'), ('model', 'Model')]),
            ('trimble_connect', [('project', 'Project'), ('model', 'Model'), ('observation', 'ToDo')]),
            ('bimcollab', [('project', 'Project'), ('observation', 'Issue'), ('model', 'Model')]),
            ('allplan', [('project', 'Project'), ('model', 'Model')]),
            # Scheduling
            ('msproject', [('project', 'Plan'), ('schedule', 'Schedule')]),
            ('primavera', [('project', 'Project'), ('schedule', 'Activity')]),
            ('synchro', [('project', 'Project'), ('schedule', 'Schedule')]),
            ('powerproject', [('project', 'Project'), ('schedule', 'Task')]),
            # ERP
            ('sap', [('project', 'Project'), ('contractor', 'Vendor')]),
            ('ifs', [('project', 'Project'), ('equipment', 'Asset')]),
            ('visma', [('project', 'Project'), ('contractor', 'Customer')]),
            ('unit4', [('project', 'Project')]),
            ('dynamics365', [('project', 'Project'), ('contractor', 'Vendor')]),
            ('monitor', [('project', 'Project')]),
            ('lemonsoft', [('project', 'Project')]),
            # Documentation
            ('openspace', [('project', 'Project'), ('inspection', 'Capture')]),
            ('holobuilder', [('project', 'Project'), ('drawing', 'Sheet')]),
            ('navvis', [('site', 'Site'), ('model', 'Scan')]),
            ('matterport', [('model', 'Model'), ('site', 'Space')]),
            ('buildots', [('project', 'Project'), ('inspection', 'Capture')]),
        ]

        for system_alias, terms in term_mappings:
            system = System.objects.filter(alias=system_alias).first()
            if system:
                for canonical, system_term in terms:
                    TermMapping.objects.get_or_create(
                        template=construction,
                        canonical_term=canonical,
                        system=system,
                        defaults={'system_term': system_term}
                    )

    print("Created global construction and enterprise systems")


def remove_global_construction_systems(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    aliases = [
        # Construction PM
        'acc', 'procore', 'dalux', 'aconex', 'itwo', 'thinkproject',
        'projectsight', 'asite', 'planradar',
        # BIM
        'revit', 'archicad', 'trimble_connect', 'bimcollab', 'allplan',
        # Scheduling
        'msproject', 'primavera', 'synchro', 'powerproject',
        # ERP
        'sap', 'ifs', 'visma', 'unit4', 'dynamics365', 'monitor', 'lemonsoft',
        # Documentation
        'openspace', 'holobuilder', 'navvis', 'matterport', 'buildots',
        # Logistics
        'dhl', 'schenker', 'dsv', 'kn', 'posti', 'bring', 'transporeon', 'nshift',
        # General
        'teams', 'slack', 'sharepoint', 'gdrive', 'docusign',
    ]
    System.objects.filter(alias__in=aliases).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0042_add_system_confirmation'),
    ]

    operations = [
        migrations.RunPython(add_global_construction_systems, remove_global_construction_systems),
    ]
