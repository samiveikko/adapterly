# Generated migration for tool categories

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
        ('mcp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToolCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, help_text='Unique identifier for the category (e.g., "crm.read", "workflow.run")', max_length=100)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('risk_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=20)),
                ('is_global', models.BooleanField(default=False, help_text='If true, this category is available to all accounts')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tool_categories', to='accounts.account')),
            ],
            options={
                'verbose_name': 'Tool Category',
                'verbose_name_plural': 'Tool Categories',
                'ordering': ['key'],
                'unique_together': {('account', 'key')},
            },
        ),
        migrations.CreateModel(
            name='ToolCategoryMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tool_key_pattern', models.CharField(help_text='fnmatch pattern to match tool names (e.g., "salesforce_*", "*_read")', max_length=255)),
                ('is_auto', models.BooleanField(default=False, help_text='If true, this mapping was auto-generated')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tool_category_mappings', to='accounts.account')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mappings', to='mcp.toolcategory')),
            ],
            options={
                'verbose_name': 'Tool Category Mapping',
                'verbose_name_plural': 'Tool Category Mappings',
                'ordering': ['tool_key_pattern'],
                'unique_together': {('account', 'tool_key_pattern', 'category')},
            },
        ),
        migrations.CreateModel(
            name='AgentPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200)),
                ('allowed_categories', models.JSONField(default=list, help_text='List of allowed category keys. Empty list = all categories allowed.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_policies', to='accounts.account')),
                ('api_key', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='policy', to='mcp.mcpapikey')),
            ],
            options={
                'verbose_name': 'Agent Policy',
                'verbose_name_plural': 'Agent Policies',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProjectPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_identifier', models.CharField(help_text='Project identifier (e.g., "PROJ-*" or workflow ID)', max_length=255)),
                ('name', models.CharField(max_length=200)),
                ('allowed_categories', models.JSONField(blank=True, help_text='List of allowed category keys. Null = no restriction.', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_policies', to='accounts.account')),
            ],
            options={
                'verbose_name': 'Project Policy',
                'verbose_name_plural': 'Project Policies',
                'ordering': ['project_identifier'],
                'unique_together': {('account', 'project_identifier')},
            },
        ),
        migrations.CreateModel(
            name='UserPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allowed_categories', models.JSONField(blank=True, help_text='List of allowed category keys. Null = no restriction.', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_policies', to='accounts.account')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mcp_policies', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Policy',
                'verbose_name_plural': 'User Policies',
                'ordering': ['-created_at'],
                'unique_together': {('account', 'user')},
            },
        ),
    ]
