"""
Add comprehensive Nordic construction industry systems.
Finnish, Danish, Norwegian, Swedish systems + global systems popular in Nordics.
"""
from django.db import migrations


def add_nordic_construction_systems(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')
    IndustryTemplate = apps.get_model('systems', 'IndustryTemplate')
    TermMapping = apps.get_model('systems', 'TermMapping')

    # Get construction industry template
    construction = IndustryTemplate.objects.filter(name='construction').first()

    # ==========================================================================
    # ADMICOM - Finnish Construction ERP (Ultima)
    # ==========================================================================
    admicom = System.objects.create(
        name='admicom',
        alias='admicom',
        display_name='Admicom Ultima',
        description='Finnish construction ERP system. Project management, TR/MVR measurements, payroll with Finnish collective agreements, reversed VAT handling.',
        system_type='erp',
        icon='calculator',
        website_url='https://www.admicom.fi',
        industry=construction,
        variables={'api_url': 'https://api.admicom.fi'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    admicom_api = Interface.objects.create(
        system=admicom, alias='api', name='api', type='API',
        base_url='https://api.admicom.fi/v1',
        auth={'type': 'oauth2', 'token_url': 'https://api.admicom.fi/oauth/token'},
        rate_limits={'requests_per_minute': 60}
    )

    # Projects
    admicom_projects = Resource.objects.create(
        interface=admicom_api, alias='projects', name='projects',
        description='Construction projects and work sites'
    )
    for action_def in [
        ('list', 'GET', '/projects', 'List all projects'),
        ('get', 'GET', '/projects/{project_id}', 'Get project details'),
        ('create', 'POST', '/projects', 'Create new project'),
        ('get_budget', 'GET', '/projects/{project_id}/budget', 'Get project budget'),
        ('get_costs', 'GET', '/projects/{project_id}/costs', 'Get actual costs'),
    ]:
        Action.objects.create(
            resource=admicom_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # TR/MVR Measurements
    admicom_measurements = Resource.objects.create(
        interface=admicom_api, alias='measurements', name='measurements',
        description='TR and MVR safety measurements'
    )
    for action_def in [
        ('list_tr', 'GET', '/projects/{project_id}/tr-measurements', 'List TR measurements'),
        ('create_tr', 'POST', '/projects/{project_id}/tr-measurements', 'Create TR measurement'),
        ('list_mvr', 'GET', '/projects/{project_id}/mvr-measurements', 'List MVR measurements'),
        ('create_mvr', 'POST', '/projects/{project_id}/mvr-measurements', 'Create MVR measurement'),
    ]:
        Action.objects.create(
            resource=admicom_measurements, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Time entries and payroll
    admicom_time = Resource.objects.create(
        interface=admicom_api, alias='time_entries', name='time_entries',
        description='Time tracking and payroll'
    )
    for action_def in [
        ('list', 'GET', '/time-entries', 'List time entries'),
        ('create', 'POST', '/time-entries', 'Create time entry'),
        ('get_payroll', 'GET', '/payroll', 'Get payroll data'),
    ]:
        Action.objects.create(
            resource=admicom_time, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Invoicing
    admicom_invoices = Resource.objects.create(
        interface=admicom_api, alias='invoices', name='invoices',
        description='Invoicing with reversed VAT support'
    )
    for action_def in [
        ('list', 'GET', '/invoices', 'List invoices'),
        ('create', 'POST', '/invoices', 'Create invoice'),
        ('get', 'GET', '/invoices/{invoice_id}', 'Get invoice details'),
    ]:
        Action.objects.create(
            resource=admicom_invoices, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # BUILDERHEAD - Finnish Project Development & Construction Management
    # ==========================================================================
    builderhead = System.objects.create(
        name='builderhead',
        alias='builderhead',
        display_name='Builderhead',
        description='Project management for real estate development, construction management and production control. Finnish company.',
        system_type='project_management',
        icon='building-gear',
        website_url='https://builderhead.com',
        industry=construction,
        variables={'api_url': 'https://api.builderhead.com'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    builderhead_api = Interface.objects.create(
        system=builderhead, alias='api', name='api', type='API',
        base_url='https://api.builderhead.com/v1',
        auth={'type': 'bearer'},
        rate_limits={'requests_per_minute': 100}
    )

    # Projects
    bh_projects = Resource.objects.create(
        interface=builderhead_api, alias='projects', name='projects',
        description='Development projects'
    )
    for action_def in [
        ('list', 'GET', '/projects', 'List all projects'),
        ('get', 'GET', '/projects/{id}', 'Get project details'),
        ('create', 'POST', '/projects', 'Create project'),
        ('update', 'PATCH', '/projects/{id}', 'Update project'),
        ('get_phases', 'GET', '/projects/{id}/phases', 'Get project phases'),
        ('get_milestones', 'GET', '/projects/{id}/milestones', 'Get milestones'),
    ]:
        Action.objects.create(
            resource=bh_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Tasks
    bh_tasks = Resource.objects.create(
        interface=builderhead_api, alias='tasks', name='tasks',
        description='Project tasks and assignments'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_id}/tasks', 'List tasks'),
        ('create', 'POST', '/projects/{project_id}/tasks', 'Create task'),
        ('update', 'PATCH', '/tasks/{id}', 'Update task'),
        ('assign', 'POST', '/tasks/{id}/assign', 'Assign task'),
    ]:
        Action.objects.create(
            resource=bh_tasks, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Documents
    bh_documents = Resource.objects.create(
        interface=builderhead_api, alias='documents', name='documents',
        description='Project documents'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_id}/documents', 'List documents'),
        ('upload', 'POST', '/projects/{project_id}/documents', 'Upload document'),
        ('get', 'GET', '/documents/{id}', 'Get document'),
    ]:
        Action.objects.create(
            resource=bh_documents, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # FONDION - Finnish Construction Project Management
    # ==========================================================================
    fondion = System.objects.create(
        name='fondion',
        alias='fondion',
        display_name='Fondion',
        description='Modern project management for construction. Budgeting, scheduling, document management. Finnish company.',
        system_type='project_management',
        icon='graph-up-arrow',
        website_url='https://fondion.com',
        industry=construction,
        variables={'api_url': 'https://api.fondion.com'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    fondion_api = Interface.objects.create(
        system=fondion, alias='api', name='api', type='API',
        base_url='https://api.fondion.com/v1',
        auth={'type': 'bearer'},
        rate_limits={'requests_per_minute': 100}
    )

    # Projects
    fondion_projects = Resource.objects.create(
        interface=fondion_api, alias='projects', name='projects',
        description='Construction projects'
    )
    for action_def in [
        ('list', 'GET', '/projects', 'List projects'),
        ('get', 'GET', '/projects/{id}', 'Get project'),
        ('create', 'POST', '/projects', 'Create project'),
        ('get_budget', 'GET', '/projects/{id}/budget', 'Get budget'),
        ('get_schedule', 'GET', '/projects/{id}/schedule', 'Get schedule'),
        ('get_cashflow', 'GET', '/projects/{id}/cashflow', 'Get cash flow forecast'),
    ]:
        Action.objects.create(
            resource=fondion_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Cost tracking
    fondion_costs = Resource.objects.create(
        interface=fondion_api, alias='costs', name='costs',
        description='Cost tracking and actuals'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_id}/costs', 'List costs'),
        ('create', 'POST', '/projects/{project_id}/costs', 'Add cost entry'),
        ('get_variance', 'GET', '/projects/{project_id}/costs/variance', 'Get cost variance'),
    ]:
        Action.objects.create(
            resource=fondion_costs, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # SOLIBRI - BIM Quality Assurance (Finnish origin)
    # ==========================================================================
    solibri = System.objects.create(
        name='solibri',
        alias='solibri',
        display_name='Solibri',
        description='BIM quality assurance and model checking. Clash detection, code compliance, design validation. Originally Finnish.',
        system_type='bim',
        icon='check2-square',
        website_url='https://www.solibri.com',
        industry=construction,
        variables={'api_url': 'https://api.solibri.com'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    solibri_api = Interface.objects.create(
        system=solibri, alias='api', name='api', type='API',
        base_url='https://api.solibri.com/v1',
        auth={'type': 'bearer'},
        rate_limits={'requests_per_minute': 60}
    )

    # Models
    solibri_models = Resource.objects.create(
        interface=solibri_api, alias='models', name='models',
        description='BIM models'
    )
    for action_def in [
        ('list', 'GET', '/models', 'List models'),
        ('get', 'GET', '/models/{id}', 'Get model details'),
        ('upload', 'POST', '/models', 'Upload model (IFC)'),
        ('check', 'POST', '/models/{id}/check', 'Run quality checks'),
        ('get_issues', 'GET', '/models/{id}/issues', 'Get issues/clashes'),
    ]:
        Action.objects.create(
            resource=solibri_models, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Rules and rulesets
    solibri_rules = Resource.objects.create(
        interface=solibri_api, alias='rules', name='rules',
        description='Checking rules and rulesets'
    )
    for action_def in [
        ('list_rulesets', 'GET', '/rulesets', 'List rulesets'),
        ('get_ruleset', 'GET', '/rulesets/{id}', 'Get ruleset details'),
        ('apply_ruleset', 'POST', '/models/{model_id}/apply-ruleset', 'Apply ruleset to model'),
    ]:
        Action.objects.create(
            resource=solibri_rules, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # VISILEAN - Lean Construction & BIM (Finnish)
    # ==========================================================================
    visilean = System.objects.create(
        name='visilean',
        alias='visilean',
        display_name='VisiLean',
        description='Lean construction planning with BIM visualization. Last Planner System, 4D BIM, takt planning. Finnish company.',
        system_type='project_management',
        icon='diagram-3',
        website_url='https://visilean.com',
        industry=construction,
        variables={'api_url': 'https://api.visilean.com'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    visilean_api = Interface.objects.create(
        system=visilean, alias='api', name='api', type='API',
        base_url='https://api.visilean.com/v1',
        auth={'type': 'bearer'},
        rate_limits={'requests_per_minute': 60}
    )

    # Projects
    visilean_projects = Resource.objects.create(
        interface=visilean_api, alias='projects', name='projects',
        description='Lean construction projects'
    )
    for action_def in [
        ('list', 'GET', '/projects', 'List projects'),
        ('get', 'GET', '/projects/{id}', 'Get project'),
    ]:
        Action.objects.create(
            resource=visilean_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Last Planner / Lookahead
    visilean_planning = Resource.objects.create(
        interface=visilean_api, alias='planning', name='planning',
        description='Last Planner System planning'
    )
    for action_def in [
        ('get_master_schedule', 'GET', '/projects/{id}/master-schedule', 'Get master schedule'),
        ('get_phase_schedule', 'GET', '/projects/{id}/phase-schedule', 'Get phase schedule'),
        ('get_lookahead', 'GET', '/projects/{id}/lookahead', 'Get lookahead plan'),
        ('get_weekly_plan', 'GET', '/projects/{id}/weekly-plan', 'Get weekly work plan'),
        ('get_ppc', 'GET', '/projects/{id}/ppc', 'Get PPC (Percent Plan Complete)'),
        ('create_task', 'POST', '/projects/{id}/tasks', 'Create planning task'),
        ('update_task', 'PATCH', '/tasks/{task_id}', 'Update task status'),
        ('add_constraint', 'POST', '/tasks/{task_id}/constraints', 'Add constraint'),
        ('resolve_constraint', 'POST', '/constraints/{id}/resolve', 'Resolve constraint'),
    ]:
        Action.objects.create(
            resource=visilean_planning, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Takt planning
    visilean_takt = Resource.objects.create(
        interface=visilean_api, alias='takt', name='takt',
        description='Takt time planning'
    )
    for action_def in [
        ('get_takt_plan', 'GET', '/projects/{id}/takt-plan', 'Get takt plan'),
        ('get_takt_trains', 'GET', '/projects/{id}/takt-trains', 'Get takt trains'),
        ('update_takt_progress', 'POST', '/takt-areas/{id}/progress', 'Update takt progress'),
    ]:
        Action.objects.create(
            resource=visilean_takt, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # REMATO - Finnish Site Management
    # ==========================================================================
    remato = System.objects.create(
        name='remato',
        alias='remato',
        display_name='Remato',
        description='Construction site management platform. Time tracking, resource management, transparent site operations. Finnish company.',
        system_type='project_management',
        icon='clock-history',
        website_url='https://remato.com',
        industry=construction,
        variables={'api_url': 'https://api.remato.com'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    remato_api = Interface.objects.create(
        system=remato, alias='api', name='api', type='API',
        base_url='https://api.remato.com/v1',
        auth={'type': 'bearer'},
        rate_limits={'requests_per_minute': 100}
    )

    # Sites
    remato_sites = Resource.objects.create(
        interface=remato_api, alias='sites', name='sites',
        description='Construction sites'
    )
    for action_def in [
        ('list', 'GET', '/sites', 'List sites'),
        ('get', 'GET', '/sites/{id}', 'Get site details'),
        ('get_workers', 'GET', '/sites/{id}/workers', 'Get workers on site'),
        ('get_attendance', 'GET', '/sites/{id}/attendance', 'Get attendance log'),
    ]:
        Action.objects.create(
            resource=remato_sites, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Time tracking
    remato_time = Resource.objects.create(
        interface=remato_api, alias='time', name='time',
        description='Time tracking'
    )
    for action_def in [
        ('list_entries', 'GET', '/time-entries', 'List time entries'),
        ('create_entry', 'POST', '/time-entries', 'Create time entry'),
        ('get_summary', 'GET', '/sites/{id}/time-summary', 'Get time summary'),
    ]:
        Action.objects.create(
            resource=remato_time, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # SIGMA ESTIMATES - Danish Cost Estimation
    # ==========================================================================
    sigma = System.objects.create(
        name='sigma_estimates',
        alias='sigma',
        display_name='Sigma Estimates',
        description='Construction cost estimation and quantity takeoff. Danish company, popular in Nordics.',
        system_type='erp',
        icon='calculator-fill',
        website_url='https://sigmaestimates.com',
        industry=construction,
        variables={'api_url': 'https://api.sigmaestimates.com'},
        meta={'api_version': 'v1', 'country': 'DK'},
        is_active=True
    )

    sigma_api = Interface.objects.create(
        system=sigma, alias='api', name='api', type='API',
        base_url='https://api.sigmaestimates.com/v1',
        auth={'type': 'api_key', 'header': 'X-API-Key'},
        rate_limits={'requests_per_minute': 60}
    )

    # Estimates
    sigma_estimates = Resource.objects.create(
        interface=sigma_api, alias='estimates', name='estimates',
        description='Cost estimates'
    )
    for action_def in [
        ('list', 'GET', '/estimates', 'List estimates'),
        ('get', 'GET', '/estimates/{id}', 'Get estimate details'),
        ('create', 'POST', '/estimates', 'Create estimate'),
        ('get_items', 'GET', '/estimates/{id}/items', 'Get line items'),
        ('get_summary', 'GET', '/estimates/{id}/summary', 'Get cost summary'),
        ('export', 'GET', '/estimates/{id}/export', 'Export estimate'),
    ]:
        Action.objects.create(
            resource=sigma_estimates, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Price database
    sigma_prices = Resource.objects.create(
        interface=sigma_api, alias='prices', name='prices',
        description='Price database'
    )
    for action_def in [
        ('search', 'GET', '/prices/search', 'Search prices'),
        ('get_category', 'GET', '/prices/categories/{id}', 'Get price category'),
    ]:
        Action.objects.create(
            resource=sigma_prices, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # INTEMPUS - Norwegian Time & Resource Management (Visma owned)
    # ==========================================================================
    intempus = System.objects.create(
        name='intempus',
        alias='intempus',
        display_name='Intempus',
        description='Time tracking and resource management for construction. Norwegian, owned by Visma.',
        system_type='erp',
        icon='stopwatch',
        website_url='https://intempus.com',
        industry=construction,
        variables={'api_url': 'https://api.intempus.com'},
        meta={'api_version': 'v1', 'country': 'NO'},
        is_active=True
    )

    intempus_api = Interface.objects.create(
        system=intempus, alias='api', name='api', type='API',
        base_url='https://api.intempus.com/v1',
        auth={'type': 'oauth2'},
        rate_limits={'requests_per_minute': 60}
    )

    # Time registration
    intempus_time = Resource.objects.create(
        interface=intempus_api, alias='time', name='time',
        description='Time registration'
    )
    for action_def in [
        ('list', 'GET', '/time-entries', 'List time entries'),
        ('create', 'POST', '/time-entries', 'Create time entry'),
        ('approve', 'POST', '/time-entries/{id}/approve', 'Approve time entry'),
        ('get_summary', 'GET', '/time-summary', 'Get time summary'),
    ]:
        Action.objects.create(
            resource=intempus_time, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Resources
    intempus_resources = Resource.objects.create(
        interface=intempus_api, alias='resources', name='resources',
        description='Resource management'
    )
    for action_def in [
        ('list_employees', 'GET', '/employees', 'List employees'),
        ('get_availability', 'GET', '/employees/{id}/availability', 'Get availability'),
        ('get_allocations', 'GET', '/allocations', 'Get resource allocations'),
    ]:
        Action.objects.create(
            resource=intempus_resources, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # 24SEVENOFFICE - Norwegian ERP
    # ==========================================================================
    twentyfour = System.objects.create(
        name='24sevenoffice',
        alias='24sevenoffice',
        display_name='24SevenOffice',
        description='Cloud ERP and accounting for Nordic businesses. Project accounting, invoicing.',
        system_type='erp',
        icon='cloud-arrow-up',
        website_url='https://24sevenoffice.com',
        industry=construction,
        variables={'api_url': 'https://api.24sevenoffice.com'},
        meta={'api_version': 'v1', 'country': 'NO'},
        is_active=True
    )

    twentyfour_api = Interface.objects.create(
        system=twentyfour, alias='api', name='api', type='API',
        base_url='https://api.24sevenoffice.com/v1',
        auth={'type': 'oauth2'},
        rate_limits={'requests_per_minute': 60}
    )

    # Projects
    twentyfour_projects = Resource.objects.create(
        interface=twentyfour_api, alias='projects', name='projects',
        description='Projects'
    )
    for action_def in [
        ('list', 'GET', '/projects', 'List projects'),
        ('get', 'GET', '/projects/{id}', 'Get project'),
        ('create', 'POST', '/projects', 'Create project'),
    ]:
        Action.objects.create(
            resource=twentyfour_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Invoices
    twentyfour_invoices = Resource.objects.create(
        interface=twentyfour_api, alias='invoices', name='invoices',
        description='Invoicing'
    )
    for action_def in [
        ('list', 'GET', '/invoices', 'List invoices'),
        ('create', 'POST', '/invoices', 'Create invoice'),
        ('get', 'GET', '/invoices/{id}', 'Get invoice'),
    ]:
        Action.objects.create(
            resource=twentyfour_invoices, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # FIELDWIRE - Site Management (Global, strong in EU)
    # ==========================================================================
    fieldwire = System.objects.create(
        name='fieldwire',
        alias='fieldwire',
        display_name='Fieldwire',
        description='Construction site management. Task management, drawings, punch lists. Now part of Hilti.',
        system_type='project_management',
        icon='hammer',
        website_url='https://fieldwire.com',
        industry=construction,
        variables={'api_url': 'https://api.fieldwire.com'},
        meta={'api_version': 'v1', 'country': 'US'},
        is_active=True
    )

    fieldwire_api = Interface.objects.create(
        system=fieldwire, alias='api', name='api', type='API',
        base_url='https://api.fieldwire.com/v1',
        auth={'type': 'bearer'},
        rate_limits={'requests_per_minute': 100}
    )

    # Projects
    fw_projects = Resource.objects.create(
        interface=fieldwire_api, alias='projects', name='projects',
        description='Projects'
    )
    for action_def in [
        ('list', 'GET', '/projects', 'List projects'),
        ('get', 'GET', '/projects/{id}', 'Get project'),
    ]:
        Action.objects.create(
            resource=fw_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Tasks
    fw_tasks = Resource.objects.create(
        interface=fieldwire_api, alias='tasks', name='tasks',
        description='Field tasks and punch lists'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_id}/tasks', 'List tasks'),
        ('create', 'POST', '/projects/{project_id}/tasks', 'Create task'),
        ('update', 'PATCH', '/tasks/{id}', 'Update task'),
        ('add_photo', 'POST', '/tasks/{id}/photos', 'Add photo to task'),
    ]:
        Action.objects.create(
            resource=fw_tasks, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Drawings/Plans
    fw_plans = Resource.objects.create(
        interface=fieldwire_api, alias='plans', name='plans',
        description='Drawings and plans'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_id}/plans', 'List plans'),
        ('upload', 'POST', '/projects/{project_id}/plans', 'Upload plan'),
        ('get', 'GET', '/plans/{id}', 'Get plan'),
    ]:
        Action.objects.create(
            resource=fw_plans, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # BLUEBEAM REVU - PDF Markup & Collaboration
    # ==========================================================================
    bluebeam = System.objects.create(
        name='bluebeam',
        alias='bluebeam',
        display_name='Bluebeam Revu',
        description='PDF markup, editing and collaboration for construction. Drawing annotations, measurements, punch lists.',
        system_type='bim',
        icon='pencil-square',
        website_url='https://www.bluebeam.com',
        industry=construction,
        variables={'api_url': 'https://api.bluebeam.com'},
        meta={'api_version': 'v1', 'country': 'US'},
        is_active=True
    )

    bluebeam_api = Interface.objects.create(
        system=bluebeam, alias='api', name='api', type='API',
        base_url='https://api.bluebeam.com/v1',
        auth={'type': 'oauth2'},
        rate_limits={'requests_per_minute': 60}
    )

    # Sessions (Studio Sessions)
    bb_sessions = Resource.objects.create(
        interface=bluebeam_api, alias='sessions', name='sessions',
        description='Studio collaboration sessions'
    )
    for action_def in [
        ('list', 'GET', '/sessions', 'List sessions'),
        ('create', 'POST', '/sessions', 'Create session'),
        ('get', 'GET', '/sessions/{id}', 'Get session'),
        ('get_documents', 'GET', '/sessions/{id}/documents', 'Get session documents'),
        ('invite', 'POST', '/sessions/{id}/invite', 'Invite users'),
    ]:
        Action.objects.create(
            resource=bb_sessions, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Documents
    bb_documents = Resource.objects.create(
        interface=bluebeam_api, alias='documents', name='documents',
        description='PDF documents'
    )
    for action_def in [
        ('upload', 'POST', '/documents', 'Upload document'),
        ('get', 'GET', '/documents/{id}', 'Get document'),
        ('get_markups', 'GET', '/documents/{id}/markups', 'Get markups'),
        ('export_markups', 'GET', '/documents/{id}/markups/export', 'Export markups'),
    ]:
        Action.objects.create(
            resource=bb_documents, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # PLANGRID - Construction Document Management (Autodesk)
    # ==========================================================================
    plangrid = System.objects.create(
        name='plangrid',
        alias='plangrid',
        display_name='PlanGrid',
        description='Construction document management. Drawings, photos, RFIs, punch lists. Part of Autodesk Construction Cloud.',
        system_type='storage',
        icon='file-earmark-image',
        website_url='https://www.plangrid.com',
        industry=construction,
        variables={'api_url': 'https://io.plangrid.com'},
        meta={'api_version': 'v1', 'country': 'US'},
        is_active=True
    )

    plangrid_api = Interface.objects.create(
        system=plangrid, alias='api', name='api', type='API',
        base_url='https://io.plangrid.com',
        auth={'type': 'oauth2'},
        rate_limits={'requests_per_minute': 100}
    )

    # Projects
    pg_projects = Resource.objects.create(
        interface=plangrid_api, alias='projects', name='projects',
        description='Projects'
    )
    for action_def in [
        ('list', 'GET', '/projects', 'List projects'),
        ('get', 'GET', '/projects/{uid}', 'Get project'),
    ]:
        Action.objects.create(
            resource=pg_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Sheets
    pg_sheets = Resource.objects.create(
        interface=plangrid_api, alias='sheets', name='sheets',
        description='Drawing sheets'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_uid}/sheets', 'List sheets'),
        ('get', 'GET', '/projects/{project_uid}/sheets/{sheet_uid}', 'Get sheet'),
        ('get_versions', 'GET', '/projects/{project_uid}/sheets/{sheet_uid}/versions', 'Get versions'),
    ]:
        Action.objects.create(
            resource=pg_sheets, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # RFIs
    pg_rfis = Resource.objects.create(
        interface=plangrid_api, alias='rfis', name='rfis',
        description='Requests for Information'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_uid}/rfis', 'List RFIs'),
        ('create', 'POST', '/projects/{project_uid}/rfis', 'Create RFI'),
        ('get', 'GET', '/projects/{project_uid}/rfis/{rfi_uid}', 'Get RFI'),
    ]:
        Action.objects.create(
            resource=pg_rfis, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Photos
    pg_photos = Resource.objects.create(
        interface=plangrid_api, alias='photos', name='photos',
        description='Site photos'
    )
    for action_def in [
        ('list', 'GET', '/projects/{project_uid}/photos', 'List photos'),
        ('upload', 'POST', '/projects/{project_uid}/photos', 'Upload photo'),
    ]:
        Action.objects.create(
            resource=pg_photos, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # TEKLA STRUCTURES - BIM for Steel/Concrete (Trimble, Finnish origin)
    # ==========================================================================
    tekla = System.objects.create(
        name='tekla',
        alias='tekla',
        display_name='Tekla Structures',
        description='BIM software for structural engineering. Steel and concrete detailing, precast, cast-in-place. Finnish origin, now Trimble.',
        system_type='bim',
        icon='bricks',
        website_url='https://www.tekla.com',
        industry=construction,
        variables={'api_url': 'https://api.tekla.com'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    tekla_api = Interface.objects.create(
        system=tekla, alias='api', name='api', type='API',
        base_url='https://api.tekla.com/v1',
        auth={'type': 'oauth2'},
        rate_limits={'requests_per_minute': 60}
    )

    # Models
    tekla_models = Resource.objects.create(
        interface=tekla_api, alias='models', name='models',
        description='Tekla models'
    )
    for action_def in [
        ('list', 'GET', '/models', 'List models'),
        ('get', 'GET', '/models/{id}', 'Get model'),
        ('get_objects', 'GET', '/models/{id}/objects', 'Get model objects'),
        ('export_ifc', 'POST', '/models/{id}/export/ifc', 'Export as IFC'),
    ]:
        Action.objects.create(
            resource=tekla_models, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # BENTLEY PROJECTWISE - Document Management for Infrastructure
    # ==========================================================================
    projectwise = System.objects.create(
        name='bentley_projectwise',
        alias='projectwise',
        display_name='Bentley ProjectWise',
        description='Document and project information management for infrastructure. CAD/BIM file management, workflows.',
        system_type='storage',
        icon='folder2-open',
        website_url='https://www.bentley.com/software/projectwise',
        industry=construction,
        variables={'api_url': 'https://api.bentley.com'},
        meta={'api_version': 'v1', 'country': 'US'},
        is_active=True
    )

    pw_api = Interface.objects.create(
        system=projectwise, alias='api', name='api', type='API',
        base_url='https://api.bentley.com/projectwise',
        auth={'type': 'oauth2'},
        rate_limits={'requests_per_minute': 60}
    )

    # Repositories
    pw_repos = Resource.objects.create(
        interface=pw_api, alias='repositories', name='repositories',
        description='Document repositories'
    )
    for action_def in [
        ('list', 'GET', '/repositories', 'List repositories'),
        ('get', 'GET', '/repositories/{id}', 'Get repository'),
    ]:
        Action.objects.create(
            resource=pw_repos, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Documents
    pw_documents = Resource.objects.create(
        interface=pw_api, alias='documents', name='documents',
        description='Documents'
    )
    for action_def in [
        ('list', 'GET', '/repositories/{repo_id}/documents', 'List documents'),
        ('get', 'GET', '/documents/{id}', 'Get document'),
        ('upload', 'POST', '/repositories/{repo_id}/documents', 'Upload document'),
        ('checkout', 'POST', '/documents/{id}/checkout', 'Check out document'),
        ('checkin', 'POST', '/documents/{id}/checkin', 'Check in document'),
    ]:
        Action.objects.create(
            resource=pw_documents, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # TRIPLETEX - Norwegian Accounting (OpenAPI)
    # ==========================================================================
    tripletex = System.objects.create(
        name='tripletex',
        alias='tripletex',
        display_name='Tripletex',
        description='Norwegian cloud accounting and ERP. Project accounting, invoicing, time tracking. Has OpenAPI.',
        system_type='erp',
        icon='receipt',
        website_url='https://tripletex.no',
        industry=construction,
        variables={'api_url': 'https://tripletex.no/v2'},
        meta={'api_version': 'v2', 'country': 'NO'},
        is_active=True
    )

    tripletex_api = Interface.objects.create(
        system=tripletex, alias='api', name='api', type='API',
        base_url='https://tripletex.no/v2',
        auth={'type': 'basic'},
        rate_limits={'requests_per_minute': 100}
    )

    # Projects
    tt_projects = Resource.objects.create(
        interface=tripletex_api, alias='projects', name='projects',
        description='Projects'
    )
    for action_def in [
        ('list', 'GET', '/project', 'List projects'),
        ('get', 'GET', '/project/{id}', 'Get project'),
        ('create', 'POST', '/project', 'Create project'),
    ]:
        Action.objects.create(
            resource=tt_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Invoices
    tt_invoices = Resource.objects.create(
        interface=tripletex_api, alias='invoices', name='invoices',
        description='Invoices'
    )
    for action_def in [
        ('list', 'GET', '/invoice', 'List invoices'),
        ('create', 'POST', '/invoice', 'Create invoice'),
        ('send', 'PUT', '/invoice/{id}/:send', 'Send invoice'),
    ]:
        Action.objects.create(
            resource=tt_invoices, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Time entries
    tt_time = Resource.objects.create(
        interface=tripletex_api, alias='timesheets', name='timesheets',
        description='Timesheet entries'
    )
    for action_def in [
        ('list', 'GET', '/timesheet/entry', 'List time entries'),
        ('create', 'POST', '/timesheet/entry', 'Create time entry'),
    ]:
        Action.objects.create(
            resource=tt_time, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # FORTNOX - Swedish Accounting
    # ==========================================================================
    fortnox = System.objects.create(
        name='fortnox',
        alias='fortnox',
        display_name='Fortnox',
        description='Swedish cloud accounting and business software. Invoicing, accounting, project management.',
        system_type='erp',
        icon='currency-exchange',
        website_url='https://www.fortnox.se',
        industry=construction,
        variables={'api_url': 'https://api.fortnox.se'},
        meta={'api_version': 'v3', 'country': 'SE'},
        is_active=True
    )

    fortnox_api = Interface.objects.create(
        system=fortnox, alias='api', name='api', type='API',
        base_url='https://api.fortnox.se/3',
        auth={'type': 'oauth2'},
        rate_limits={'requests_per_minute': 300}
    )

    # Invoices
    fnx_invoices = Resource.objects.create(
        interface=fortnox_api, alias='invoices', name='invoices',
        description='Invoices'
    )
    for action_def in [
        ('list', 'GET', '/invoices', 'List invoices'),
        ('create', 'POST', '/invoices', 'Create invoice'),
        ('get', 'GET', '/invoices/{DocumentNumber}', 'Get invoice'),
    ]:
        Action.objects.create(
            resource=fnx_invoices, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Projects
    fnx_projects = Resource.objects.create(
        interface=fortnox_api, alias='projects', name='projects',
        description='Projects'
    )
    for action_def in [
        ('list', 'GET', '/projects', 'List projects'),
        ('create', 'POST', '/projects', 'Create project'),
        ('get', 'GET', '/projects/{ProjectNumber}', 'Get project'),
    ]:
        Action.objects.create(
            resource=fnx_projects, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # Add term mappings for new systems
    # ==========================================================================
    if construction:
        new_systems = [
            (admicom, [('project', 'Projekti'), ('worker', 'Työntekijä'), ('inspection', 'TR-mittaus')]),
            (builderhead, [('project', 'Project'), ('site', 'Site')]),
            (fondion, [('project', 'Project'), ('schedule', 'Schedule')]),
            (solibri, [('model', 'Model'), ('inspection', 'Check')]),
            (visilean, [('project', 'Project'), ('schedule', 'Plan'), ('observation', 'Constraint')]),
            (remato, [('site', 'Site'), ('worker', 'Worker')]),
            (sigma, [('project', 'Estimate')]),
            (intempus, [('worker', 'Employee'), ('project', 'Project')]),
            (fieldwire, [('project', 'Project'), ('observation', 'Task'), ('drawing', 'Plan')]),
            (bluebeam, [('document', 'Document'), ('observation', 'Markup')]),
            (plangrid, [('project', 'Project'), ('drawing', 'Sheet'), ('observation', 'Issue')]),
            (tekla, [('model', 'Model'), ('drawing', 'Drawing')]),
            (projectwise, [('document', 'Document'), ('project', 'Repository')]),
            (tripletex, [('project', 'Project'), ('contractor', 'Customer')]),
            (fortnox, [('project', 'Project'), ('contractor', 'Customer')]),
        ]

        for system, terms in new_systems:
            for canonical, system_term in terms:
                TermMapping.objects.get_or_create(
                    template=construction,
                    canonical_term=canonical,
                    system=system,
                    defaults={'system_term': system_term}
                )

    print(f"Created 15 new Nordic construction systems with adapters")


def remove_nordic_construction_systems(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    aliases = [
        'admicom', 'builderhead', 'fondion', 'solibri', 'visilean', 'remato',
        'sigma', 'intempus', '24sevenoffice', 'fieldwire', 'bluebeam',
        'plangrid', 'tekla', 'projectwise', 'tripletex', 'fortnox'
    ]
    System.objects.filter(alias__in=aliases).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0037_alter_interface_type_alter_system_system_type'),
    ]

    operations = [
        migrations.RunPython(add_nordic_construction_systems, remove_nordic_construction_systems),
    ]
