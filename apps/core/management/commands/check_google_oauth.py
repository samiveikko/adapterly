"""
Management command to check Google OAuth configuration.
"""

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check Google OAuth configuration status"

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Google OAuth Configuration Check")
        self.stdout.write("=" * 60 + "\n")

        # Check INSTALLED_APPS
        from django.conf import settings

        has_google = "allauth.socialaccount.providers.google" in settings.INSTALLED_APPS
        self.stdout.write(f"Google provider installed: {self._status(has_google)}")

        if not has_google:
            self.stdout.write(self.style.ERROR("\nGoogle provider not in INSTALLED_APPS!"))
            return

        # Check Site
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            self.stdout.write("\nSite Configuration:")
            self.stdout.write(f"  ID: {site.id}")
            self.stdout.write(f"  Domain: {site.domain}")
            self.stdout.write(f"  Name: {site.name}")

            # Check if domain is still default
            if site.domain == "example.com":
                self.stdout.write(self.style.WARNING("  Warning: Site domain is still 'example.com'!"))
                self.stdout.write(self.style.WARNING("  Update it to your actual domain (e.g., '127.0.0.1:8000')"))
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"\nSite with ID {settings.SITE_ID} not found!"))
            return

        # Check Social App
        self.stdout.write("\nGoogle OAuth Apps:")
        google_apps = SocialApp.objects.filter(provider="google")

        if not google_apps.exists():
            self.stdout.write(self.style.ERROR("  No Google OAuth apps configured!"))
            self.stdout.write("\nTo configure Google OAuth:")
            self.stdout.write("1. Go to Django admin: /admin/")
            self.stdout.write("2. Navigate to 'Social applications'")
            self.stdout.write("3. Add a new social application")
            self.stdout.write("4. See docs/GOOGLE_OAUTH_SETUP.md for details")
            return

        for app in google_apps:
            self.stdout.write(f"\n  App: {app.name}")
            self.stdout.write(
                f"    Client ID: {app.client_id[:20]}..."
                if len(app.client_id) > 20
                else f"    Client ID: {app.client_id}"
            )
            self.stdout.write(f"    Secret: {'*' * 20} (hidden)")

            # Check sites
            app_sites = app.sites.all()
            if app_sites.exists():
                self.stdout.write("    Associated sites:")
                for s in app_sites:
                    self.stdout.write(f"      - {s.domain}")
                    if s.id == site.id:
                        self.stdout.write(self.style.SUCCESS("        (matches current site)"))
            else:
                self.stdout.write(self.style.ERROR("    No sites associated with this app!"))
                self.stdout.write(self.style.WARNING("    You need to add your site to this social app in admin."))

        # Summary
        self.stdout.write("\n" + "=" * 60)
        configured = has_google and google_apps.exists() and any(site in app.sites.all() for app in google_apps)

        if configured:
            self.stdout.write(self.style.SUCCESS("Google OAuth is properly configured!"))
            self.stdout.write("\nNext steps:")
            self.stdout.write("1. Visit /auth/login/ to see the Google login button")
            self.stdout.write("2. Make sure redirect URIs in Google Console match:")
            self.stdout.write(f"   http://{site.domain}/auth/google/login/callback/")
        else:
            self.stdout.write(self.style.ERROR("Google OAuth is NOT properly configured!"))
            self.stdout.write("\nSee docs/GOOGLE_OAUTH_SETUP.md for setup instructions.")

        self.stdout.write("=" * 60 + "\n")

    def _status(self, condition):
        if condition:
            return self.style.SUCCESS("Yes")
        return self.style.ERROR("No")
