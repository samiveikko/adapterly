"""
Add project-scoping to AccountSystem.

- Adds nullable project FK to AccountSystem
- Removes old unique_together ('account', 'system')
- Adds two new constraints:
  - uix_accountsystem_account_system_project: unique (account, system, project)
  - uix_accountsystem_account_system_shared: unique (account, system) WHERE project IS NULL
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0044_alter_system_alias'),
        ('mcp', '0008_errordiagnostic'),
    ]

    operations = [
        # 1. Add project FK (nullable)
        migrations.AddField(
            model_name='accountsystem',
            name='project',
            field=models.ForeignKey(
                blank=True,
                help_text='Project-scoped credential. NULL = account-level (shared).',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='account_systems',
                to='mcp.project',
            ),
        ),
        # 2. Drop old unique_together
        migrations.AlterUniqueTogether(
            name='accountsystem',
            unique_together=set(),
        ),
        # 3. Add new constraints
        migrations.AddConstraint(
            model_name='accountsystem',
            constraint=models.UniqueConstraint(
                fields=['account', 'system', 'project'],
                name='uix_accountsystem_account_system_project',
            ),
        ),
        migrations.AddConstraint(
            model_name='accountsystem',
            constraint=models.UniqueConstraint(
                condition=models.Q(project__isnull=True),
                fields=['account', 'system'],
                name='uix_accountsystem_account_system_shared',
            ),
        ),
    ]
