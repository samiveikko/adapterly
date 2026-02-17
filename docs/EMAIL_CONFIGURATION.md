# Email Configuration Guide

This guide explains how to configure email sending for Adapterly.

## Environment Variables

Add the following variables to your `.env` file:

### Required Settings

```env
# Email Server Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Optional Settings (with defaults)

```env
# Email Port (default: 587 for TLS)
EMAIL_PORT=587

# Use TLS (default: true)
EMAIL_USE_TLS=true

# Use SSL (default: false) - set to true for port 465
EMAIL_USE_SSL=false

# Default sender email (default: uses EMAIL_HOST_USER)
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## Email Provider Examples

### Gmail
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Note:** For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an "App Password" at https://myaccount.google.com/apppasswords
3. Use the app password (not your regular Gmail password)

### Outlook/Office 365
```env
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

### SendGrid
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

### Amazon SES
```env
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-smtp-username
EMAIL_HOST_PASSWORD=your-smtp-password
```

### Custom SMTP Server
```env
EMAIL_HOST=mail.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=smtp-user@yourdomain.com
EMAIL_HOST_PASSWORD=your-smtp-password
```

## Testing Email Configuration

### Method 1: Django Shell

```bash
python manage.py shell
```

Then run:

```python
from django.core.mail import send_mail

send_mail(
    'Test Email from Adapterly',
    'This is a test email to verify email configuration.',
    None,  # Uses DEFAULT_FROM_EMAIL
    ['recipient@example.com'],
    fail_silently=False,
)
```

### Method 2: Management Command

Create a test email command:

```python
# apps/core/management/commands/test_email.py
from django.core.management.base import BaseCommand
from django.core.mail import send_mail

class Command(BaseCommand):
    help = 'Send a test email'

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email recipient')

    def handle(self, *args, **options):
        recipient = options['recipient']
        
        try:
            send_mail(
                'Test Email from Adapterly',
                'This is a test email to verify email configuration.',
                None,
                [recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully sent test email to {recipient}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email: {str(e)}'))
```

Then run:
```bash
python manage.py test_email your-email@example.com
```

## Features Using Email

### 1. Password Reset
- Users can request password reset via email
- Reset link is sent to user's registered email
- Configured URLs:
  - Request: `/auth/password/reset/`
  - Confirmation: `/auth/password/reset/done/`

### 2. Account Verification (if enabled)
To enable email verification for new accounts, update `config/settings.py`:

```python
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # or 'optional'
```

### 3. User Invitations
The system can send invitation emails when:
- Admin invites users to an account
- Account shares require notification

## Troubleshooting

### Common Issues

**1. Authentication Failed**
- Check username and password are correct
- For Gmail: Use App Password, not regular password
- Verify 2FA is enabled (if required by provider)

**2. Connection Timeout**
- Check EMAIL_HOST is correct
- Verify firewall allows outbound connections on the port
- Try different port (587 for TLS, 465 for SSL)

**3. TLS/SSL Errors**
- If using port 465, set `EMAIL_USE_SSL=true` and `EMAIL_USE_TLS=false`
- If using port 587, set `EMAIL_USE_TLS=true` and `EMAIL_USE_SSL=false`

**4. Emails Go to Spam**
- Set proper `DEFAULT_FROM_EMAIL` with your domain
- Configure SPF, DKIM, and DMARC records for your domain
- Use a reputable email service provider

### Debug Mode

To see email content in console instead of sending (for development):

```python
# In settings.py (for development only)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Or in `.env`:
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Log Email Errors

Check Django logs for email errors:

```bash
# In your Django logs
tail -f /path/to/django.log
```

Or enable email error logging in `settings.py`:

```python
import logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

## Security Best Practices

1. **Never commit `.env` file to Git**
   - Add `.env` to `.gitignore`
   - Use environment-specific `.env` files

2. **Use App Passwords**
   - Don't use your main email password
   - Generate service-specific passwords

3. **Limit Email Rate**
   - Configure rate limiting to prevent abuse
   - Use email service provider's rate limits

4. **Secure Credentials**
   - Store credentials in environment variables
   - Use secret management in production (AWS Secrets Manager, Azure Key Vault, etc.)

5. **Monitor Email Usage**
   - Track sent emails
   - Set up alerts for unusual activity

## Production Recommendations

For production, consider using:

1. **Dedicated Email Service**
   - SendGrid
   - Amazon SES
   - Mailgun
   - Postmark

2. **Email Queue**
   - Use Celery for async email sending
   - Prevents blocking web requests
   - Better error handling and retries

3. **Email Templates**
   - Use HTML email templates
   - Maintain consistent branding
   - Support for multiple languages

## Current Configuration

Your current settings (from `config/settings.py`):

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
```

## Next Steps

1. ✅ Add email variables to `.env`
2. ✅ Restart Django server
3. ✅ Test email sending
4. ✅ Configure email templates (optional)
5. ✅ Set up monitoring (optional)

