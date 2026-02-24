"""
Finalize constraints: make AgentProfile.project non-nullable,
add new unique_together (project, name).
"""

import django.db.models.deletion
from django.db import migrations, models


def delete_orphan_profiles(apps, schema_editor):
    """Delete profiles that still have no project (shouldn't happen normally)."""
    AgentProfile = apps.get_model("mcp", "AgentProfile")
    AgentProfile.objects.filter(project__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("mcp", "0015_data_migrate_profiles"),
    ]

    operations = [
        # Clean up any remaining null-project profiles
        migrations.RunPython(delete_orphan_profiles, migrations.RunPython.noop),
        # Make project non-nullable
        migrations.AlterField(
            model_name="agentprofile",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="agent_profiles",
                to="mcp.project",
            ),
        ),
        # Add new unique constraint
        migrations.AlterUniqueTogether(
            name="agentprofile",
            unique_together={("project", "name")},
        ),
    ]
