# Generated manually - Add sample systems

from django.db import migrations


def create_sample_systems(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    SystemEndpoint = apps.get_model('systems', 'SystemEndpoint')
    
    # Jira
    jira = System.objects.create(
        name='jira',
        display_name='Jira',
        description='Project management and issue tracking system',
        system_type='project_management',
        icon='kanban',
        website_url='https://www.atlassian.com/software/jira',
        is_active=True
    )
    
    SystemEndpoint.objects.create(
        system=jira,
        name='Cloud API',
        description='Jira Cloud REST API',
        base_url='https://your-domain.atlassian.net',
        api_version='3',
        auth_type='basic',
        auth_config={'api_key_name': 'Authorization'},
        headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
        timeout=30,
        is_active=True
    )
    
    # Slack
    slack = System.objects.create(
        name='slack',
        display_name='Slack',
        description='Team communication and collaboration platform',
        system_type='communication',
        icon='chat-dots',
        website_url='https://slack.com',
        is_active=True
    )
    
    SystemEndpoint.objects.create(
        system=slack,
        name='Web API',
        description='Slack Web API',
        base_url='https://slack.com/api',
        api_version='v1',
        auth_type='bearer',
        auth_config={'token_type': 'Bearer'},
        headers={'Content-Type': 'application/json'},
        timeout=30,
        is_active=True
    )
    
    # GitHub
    github = System.objects.create(
        name='github',
        display_name='GitHub',
        description='Version control and code collaboration platform',
        system_type='version_control',
        icon='github',
        website_url='https://github.com',
        is_active=True
    )
    
    SystemEndpoint.objects.create(
        system=github,
        name='REST API',
        description='GitHub REST API',
        base_url='https://api.github.com',
        api_version='v3',
        auth_type='bearer',
        auth_config={'token_type': 'Bearer'},
        headers={'Accept': 'application/vnd.github.v3+json'},
        timeout=30,
        is_active=True
    )
    
    # Jenkins
    jenkins = System.objects.create(
        name='jenkins',
        display_name='Jenkins',
        description='Continuous integration and deployment server',
        system_type='ci_cd',
        icon='gear',
        website_url='https://jenkins.io',
        is_active=True
    )
    
    SystemEndpoint.objects.create(
        system=jenkins,
        name='REST API',
        description='Jenkins REST API',
        base_url='http://your-jenkins-server:8080',
        api_version='1.0',
        auth_type='basic',
        auth_config={'api_key_name': 'Authorization'},
        headers={'Content-Type': 'application/json'},
        timeout=60,
        is_active=True
    )


def remove_sample_systems(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    System.objects.filter(name__in=['jira', 'slack', 'github', 'jenkins']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_sample_systems, remove_sample_systems),
    ]
