# Data migration to encrypt existing unencrypted credentials

from django.db import migrations


def encrypt_existing_credentials(apps, schema_editor):
    """
    Encrypt any existing unencrypted credentials.
    The EncryptedCharField handles this automatically on save,
    so we just need to re-save each AccountSystem.
    """
    AccountSystem = apps.get_model('systems', 'AccountSystem')

    # Import the encryption function
    from apps.core.crypto import encrypt_value, decrypt_value

    encrypted_fields = [
        'password', 'api_key', 'token', 'client_secret',
        'oauth_token', 'oauth_refresh_token', 'session_cookie', 'csrf_token'
    ]

    for account_system in AccountSystem.objects.all():
        updated = False
        for field_name in encrypted_fields:
            value = getattr(account_system, field_name)
            if value:
                # Try to decrypt - if it fails, the value is not encrypted
                try:
                    decrypted = decrypt_value(value)
                    # If decrypt returns the same value, it wasn't encrypted
                    if decrypted == value:
                        # Encrypt it
                        encrypted = encrypt_value(value)
                        setattr(account_system, field_name, encrypted)
                        updated = True
                except Exception:
                    # Value is not encrypted, encrypt it
                    encrypted = encrypt_value(value)
                    setattr(account_system, field_name, encrypted)
                    updated = True

        if updated:
            # Use update() to avoid triggering model save logic
            AccountSystem.objects.filter(pk=account_system.pk).update(
                password=account_system.password,
                api_key=account_system.api_key,
                token=account_system.token,
                client_secret=account_system.client_secret,
                oauth_token=account_system.oauth_token,
                oauth_refresh_token=account_system.oauth_refresh_token,
                session_cookie=account_system.session_cookie,
                csrf_token=account_system.csrf_token,
            )


def reverse_encrypt(apps, schema_editor):
    """
    Decrypt all credentials (reverse migration).
    Warning: This exposes sensitive data - use with caution.
    """
    AccountSystem = apps.get_model('systems', 'AccountSystem')
    from apps.core.crypto import decrypt_value

    encrypted_fields = [
        'password', 'api_key', 'token', 'client_secret',
        'oauth_token', 'oauth_refresh_token', 'session_cookie', 'csrf_token'
    ]

    for account_system in AccountSystem.objects.all():
        updated = False
        for field_name in encrypted_fields:
            value = getattr(account_system, field_name)
            if value:
                decrypted = decrypt_value(value)
                if decrypted != value:
                    setattr(account_system, field_name, decrypted)
                    updated = True

        if updated:
            AccountSystem.objects.filter(pk=account_system.pk).update(
                password=account_system.password,
                api_key=account_system.api_key,
                token=account_system.token,
                client_secret=account_system.client_secret,
                oauth_token=account_system.oauth_token,
                oauth_refresh_token=account_system.oauth_refresh_token,
                session_cookie=account_system.session_cookie,
                csrf_token=account_system.csrf_token,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0018_alter_accountsystem_api_key_and_more'),
    ]

    operations = [
        migrations.RunPython(encrypt_existing_credentials, reverse_encrypt),
    ]
