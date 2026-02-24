# Generated manually - Add AuthenticationStep model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0004_add_infrakit_system'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthenticationStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('step_order', models.PositiveIntegerField(default=1)),
                ('step_type', models.CharField(choices=[('login', 'Login'), ('password', 'Password'), ('two_factor', 'Two-Factor Authentication'), ('iam', 'Identity and Access Management'), ('oauth', 'OAuth'), ('saml', 'SAML'), ('ldap', 'LDAP'), ('api_key', 'API Key'), ('custom', 'Custom')], max_length=20)),
                ('step_name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_required', models.BooleanField(default=True)),
                ('is_optional', models.BooleanField(default=False)),
                ('timeout_seconds', models.IntegerField(default=300)),
                ('input_fields', models.JSONField(default=dict)),
                ('validation_rules', models.JSONField(default=dict)),
                ('success_message', models.CharField(blank=True, max_length=200)),
                ('failure_message', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('next_step_on_failure', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='failure_next', to='systems.authenticationstep')),
                ('next_step_on_success', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='success_next', to='systems.authenticationstep')),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auth_steps', to='systems.system')),
            ],
            options={
                'ordering': ['system', 'step_order'],
                'unique_together': {('system', 'step_order')},
            },
        ),
    ]
