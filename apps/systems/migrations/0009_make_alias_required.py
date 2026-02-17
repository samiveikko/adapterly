# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0008_update_system_aliases'),
    ]

    operations = [
        migrations.AlterField(
            model_name='system',
            name='alias',
            field=models.CharField(help_text="Unique alias used in workflow DSL (e.g., 'jira', 'slack')", max_length=50, unique=True),
        ),
    ]
