# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0003_accountuser_is_current_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='System',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('display_name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('system_type', models.CharField(choices=[('project_management', 'Project Management'), ('communication', 'Communication'), ('version_control', 'Version Control'), ('ci_cd', 'CI/CD'), ('monitoring', 'Monitoring'), ('storage', 'Storage'), ('other', 'Other')], max_length=50)),
                ('icon', models.CharField(blank=True, max_length=50)),
                ('website_url', models.URLField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['display_name'],
            },
        ),
        migrations.CreateModel(
            name='SystemEndpoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('base_url', models.URLField()),
                ('api_version', models.CharField(blank=True, max_length=20)),
                ('auth_type', models.CharField(choices=[('none', 'No Authentication'), ('api_key', 'API Key'), ('oauth2', 'OAuth 2.0'), ('basic', 'Basic Authentication'), ('bearer', 'Bearer Token'), ('custom', 'Custom')], default='none', max_length=20)),
                ('auth_config', models.JSONField(default=dict)),
                ('headers', models.JSONField(default=dict)),
                ('timeout', models.IntegerField(default=30)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='endpoints', to='systems.system')),
            ],
            options={
                'ordering': ['system', 'name'],
                'unique_together': {('system', 'name')},
            },
        ),
        migrations.CreateModel(
            name='AccountSystem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, max_length=200)),
                ('password', models.CharField(blank=True, max_length=500)),
                ('api_key', models.CharField(blank=True, max_length=500)),
                ('token', models.CharField(blank=True, max_length=1000)),
                ('client_id', models.CharField(blank=True, max_length=200)),
                ('client_secret', models.CharField(blank=True, max_length=500)),
                ('oauth_token', models.TextField(blank=True)),
                ('oauth_refresh_token', models.TextField(blank=True)),
                ('oauth_expires_at', models.DateTimeField(blank=True, null=True)),
                ('custom_settings', models.JSONField(default=dict)),
                ('is_enabled', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('last_verified_at', models.DateTimeField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='systems', to='accounts.account')),
                ('endpoint', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='systems.systemendpoint')),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='account_configs', to='systems.system')),
            ],
            options={
                'ordering': ['system__display_name'],
                'unique_together': {('account', 'system')},
            },
        ),
    ]
