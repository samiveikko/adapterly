"""
Schema migration: Add AgentProfile.project FK, remove ProjectIntegration unique constraint,
change MCPApiKey.profile to CASCADE.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mcp", "0013_remove_data_mappings"),
    ]

    operations = [
        # 1. Add project FK to AgentProfile (nullable for now)
        migrations.AddField(
            model_name="agentprofile",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="agent_profiles",
                to="mcp.project",
            ),
        ),
        # 2. Remove unique_together on ProjectIntegration (project, system)
        migrations.AlterUniqueTogether(
            name="projectintegration",
            unique_together=set(),
        ),
        # 3. Change MCPApiKey.profile on_delete to CASCADE (keep nullable for now)
        migrations.AlterField(
            model_name="mcpapikey",
            name="profile",
            field=models.ForeignKey(
                blank=True,
                help_text="Agent profile defining tool access. If set, overrides mode/allowed_tools/blocked_tools.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="api_keys",
                to="mcp.agentprofile",
            ),
        ),
        # 4. Remove old unique_together on AgentProfile (account, name)
        migrations.AlterUniqueTogether(
            name="agentprofile",
            unique_together=set(),
        ),
    ]
