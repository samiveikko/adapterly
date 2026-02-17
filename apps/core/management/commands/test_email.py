from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send a test email to verify email configuration"

    def add_arguments(self, parser):
        parser.add_argument("recipient", type=str, help="Email recipient address")
        parser.add_argument("--subject", type=str, default=None, help="Email subject (optional, defaults to app name)")

    def handle(self, *args, **options):
        recipient = options["recipient"]
        app_name = getattr(settings, "APP_NAME", "Adapterly")
        subject = options["subject"] or f"Test Email from {app_name}"

        # Check if email is configured
        if not settings.EMAIL_HOST_USER:
            self.stdout.write(self.style.ERROR("Email not configured! Please set EMAIL_HOST_USER in .env file"))
            return

        app_tagline = getattr(settings, "APP_TAGLINE", "AI integration platform for fragmented industries")
        message = f"""
This is a test email from {app_name} to verify your email configuration.

Configuration Details:
- Email Backend: {settings.EMAIL_BACKEND}
- SMTP Host: {settings.EMAIL_HOST}
- SMTP Port: {settings.EMAIL_PORT}
- Use TLS: {settings.EMAIL_USE_TLS}
- Use SSL: {settings.EMAIL_USE_SSL}
- From Email: {settings.DEFAULT_FROM_EMAIL}

If you received this email, your email configuration is working correctly!

---
{app_name} - {app_tagline}
        """.strip()

        try:
            self.stdout.write(f"Sending test email to {recipient}...")

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )

            self.stdout.write(self.style.SUCCESS(f"[OK] Successfully sent test email to {recipient}"))
            self.stdout.write(self.style.SUCCESS(f"     From: {settings.DEFAULT_FROM_EMAIL}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] Failed to send email: {str(e)}"))
            self.stdout.write("")
            self.stdout.write("Common issues:")
            self.stdout.write("1. Check EMAIL_HOST, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD in .env")
            self.stdout.write("2. For Gmail, use an App Password (not your regular password)")
            self.stdout.write("3. Verify EMAIL_PORT (587 for TLS, 465 for SSL)")
            self.stdout.write("4. Check firewall allows outbound connections")
            self.stdout.write("")
            self.stdout.write("Current settings:")
            self.stdout.write(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
            self.stdout.write(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
            self.stdout.write(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
            self.stdout.write(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
