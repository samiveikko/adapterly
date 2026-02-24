"""
Remove ToolCategory system: drop category models, M2M fields, and policy models.

Replaced by direct tool selection via AgentProfile.include_tools.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("mcp", "0016_finalize_constraints"),
    ]

    operations = [
        # 1. Remove M2M field (drops the through table)
        migrations.RemoveField(
            model_name="agentprofile",
            name="allowed_categories",
        ),
        # 2. Remove exclude_tools from AgentProfile
        migrations.RemoveField(
            model_name="agentprofile",
            name="exclude_tools",
        ),
        # 3. Remove allowed_categories from Project
        migrations.RemoveField(
            model_name="project",
            name="allowed_categories",
        ),
        # 4. Remove policy models (they reference ToolCategory via JSON, not FK)
        migrations.DeleteModel(
            name="AgentPolicy",
        ),
        migrations.DeleteModel(
            name="ProjectPolicy",
        ),
        migrations.DeleteModel(
            name="UserPolicy",
        ),
        # 5. Remove ToolCategoryMapping (has FK to ToolCategory)
        migrations.DeleteModel(
            name="ToolCategoryMapping",
        ),
        # 6. Remove ToolCategory last (other models may reference it)
        migrations.DeleteModel(
            name="ToolCategory",
        ),
    ]
