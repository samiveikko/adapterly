# Generated manually - Add schema fields to SystemEndpoint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0002_sample_systems'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemendpoint',
            name='input_schema',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='systemendpoint',
            name='pagination_schema',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='systemendpoint',
            name='output_schema',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='systemendpoint',
            name='parameter_schema',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
