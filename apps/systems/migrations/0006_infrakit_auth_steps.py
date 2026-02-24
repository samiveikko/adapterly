# Generated manually - Add authentication steps for Infrakit

from django.db import migrations


def create_infrakit_auth_steps(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    AuthenticationStep = apps.get_model('systems', 'AuthenticationStep')
    
    # Get Infrakit system
    infrakit = System.objects.get(name='infrakit')
    
    # Step 1: Login
    login_step = AuthenticationStep.objects.create(
        system=infrakit,
        step_order=1,
        step_type='login',
        step_name='Username/Email',
        description='Enter your Infrakit username or email address',
        is_required=True,
        timeout_seconds=300,
        input_fields={
            'username': {
                'type': 'text',
                'label': 'Username or Email',
                'placeholder': 'Enter your username or email',
                'required': True
            }
        },
        validation_rules={
            'username': {
                'required': True,
                'type': 'email',
                'min_length': 3,
                'max_length': 100
            }
        },
        success_message='Username validated successfully',
        failure_message='Invalid username format',
        is_active=True
    )
    
    # Step 2: Password
    password_step = AuthenticationStep.objects.create(
        system=infrakit,
        step_order=2,
        step_type='password',
        step_name='Password',
        description='Enter your Infrakit password',
        is_required=True,
        timeout_seconds=300,
        input_fields={
            'password': {
                'type': 'password',
                'label': 'Password',
                'placeholder': 'Enter your password',
                'required': True
            }
        },
        validation_rules={
            'password': {
                'required': True,
                'min_length': 8,
                'max_length': 128
            }
        },
        success_message='Password validated successfully',
        failure_message='Invalid password',
        is_active=True
    )
    
    # Step 3: Two-Factor Authentication (Optional)
    twofa_step = AuthenticationStep.objects.create(
        system=infrakit,
        step_order=3,
        step_type='two_factor',
        step_name='Two-Factor Authentication',
        description='Enter your 2FA code from authenticator app',
        is_required=False,
        is_optional=True,
        timeout_seconds=300,
        input_fields={
            'twofa_code': {
                'type': 'text',
                'label': '2FA Code',
                'placeholder': 'Enter 6-digit code',
                'required': False,
                'maxlength': 6
            }
        },
        validation_rules={
            'twofa_code': {
                'required': False,
                'type': 'number',
                'min_length': 6,
                'max_length': 6
            }
        },
        success_message='2FA code validated successfully',
        failure_message='Invalid 2FA code',
        is_active=True
    )
    
    # Step 4: IAM Role Selection
    iam_step = AuthenticationStep.objects.create(
        system=infrakit,
        step_order=4,
        step_type='iam',
        step_name='IAM Role Selection',
        description='Select your IAM role for infrastructure access',
        is_required=True,
        timeout_seconds=300,
        input_fields={
            'iam_role': {
                'type': 'select',
                'label': 'IAM Role',
                'required': True,
                'options': [
                    {'value': 'admin', 'label': 'Administrator'},
                    {'value': 'developer', 'label': 'Developer'},
                    {'value': 'viewer', 'label': 'Viewer'},
                    {'value': 'deployer', 'label': 'Deployer'}
                ]
            },
            'environment': {
                'type': 'select',
                'label': 'Environment',
                'required': True,
                'options': [
                    {'value': 'development', 'label': 'Development'},
                    {'value': 'staging', 'label': 'Staging'},
                    {'value': 'production', 'label': 'Production'}
                ]
            }
        },
        validation_rules={
            'iam_role': {
                'required': True,
                'enum': ['admin', 'developer', 'viewer', 'deployer']
            },
            'environment': {
                'required': True,
                'enum': ['development', 'staging', 'production']
            }
        },
        success_message='IAM role selected successfully',
        failure_message='Invalid IAM role or environment',
        is_active=True
    )
    
    # Set up step flow
    login_step.next_step_on_success = password_step
    login_step.save()
    
    password_step.next_step_on_success = twofa_step
    password_step.save()
    
    twofa_step.next_step_on_success = iam_step
    twofa_step.save()
    
    # IAM step is the final step, no next step


def remove_infrakit_auth_steps(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    AuthenticationStep = apps.get_model('systems', 'AuthenticationStep')
    
    infrakit = System.objects.get(name='infrakit')
    AuthenticationStep.objects.filter(system=infrakit).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0005_add_authentication_step'),
    ]

    operations = [
        migrations.RunPython(create_infrakit_auth_steps, remove_infrakit_auth_steps),
    ]
