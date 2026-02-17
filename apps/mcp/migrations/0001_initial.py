# Generated migration for MCP models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MCPAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tool_name', models.CharField(db_index=True, max_length=255)),
                ('tool_type', models.CharField(choices=[('workflow', 'Workflow Tool'), ('system_read', 'System Tool (Read)'), ('system_write', 'System Tool (Write)'), ('resource', 'Resource Access')], max_length=50)),
                ('parameters', models.JSONField(default=dict)),
                ('result_summary', models.JSONField(default=dict)),
                ('duration_ms', models.IntegerField(default=0)),
                ('success', models.BooleanField(default=True)),
                ('error_message', models.TextField(blank=True)),
                ('session_id', models.CharField(blank=True, db_index=True, max_length=100)),
                ('transport', models.CharField(choices=[('stdio', 'Standard I/O'), ('sse', 'Server-Sent Events')], default='stdio', max_length=20)),
                ('mode', models.CharField(choices=[('safe', 'Safe Mode'), ('power', 'Power Mode')], default='safe', max_length=20)),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mcp_audit_logs', to='accounts.account')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mcp_audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='MCPSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(db_index=True, max_length=100, unique=True)),
                ('mode', models.CharField(choices=[('safe', 'Safe Mode'), ('power', 'Power Mode')], default='safe', max_length=20)),
                ('transport', models.CharField(choices=[('stdio', 'Standard I/O'), ('sse', 'Server-Sent Events')], default='stdio', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('tool_calls_count', models.IntegerField(default=0)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mcp_sessions', to='accounts.account')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-last_activity'],
            },
        ),
        migrations.CreateModel(
            name='MCPApiKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('key_prefix', models.CharField(db_index=True, max_length=10)),
                ('key_hash', models.CharField(max_length=128)),
                ('mode', models.CharField(choices=[('safe', 'Safe Mode'), ('power', 'Power Mode')], default='safe', max_length=20)),
                ('allowed_tools', models.JSONField(blank=True, default=list, help_text='List of allowed tool patterns (empty = all allowed for mode)')),
                ('blocked_tools', models.JSONField(blank=True, default=list, help_text='List of blocked tool patterns')),
                ('is_active', models.BooleanField(default=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mcp_api_keys', to='accounts.account')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'MCP API Key',
                'verbose_name_plural': 'MCP API Keys',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='mcpauditlog',
            index=models.Index(fields=['account', 'tool_name'], name='mcp_mcpaudi_account_a90d65_idx'),
        ),
        migrations.AddIndex(
            model_name='mcpauditlog',
            index=models.Index(fields=['account', 'timestamp'], name='mcp_mcpaudi_account_3a8c2e_idx'),
        ),
    ]
