"""
Management command to test automatic account creation.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import Account, AccountUser

User = get_user_model()


class Command(BaseCommand):
    help = "Test automatic account creation for users"

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Account Creation Test")
        self.stdout.write("=" * 60 + "\n")

        # Check existing users
        users = User.objects.all()
        self.stdout.write(f"Total users in system: {users.count()}\n")

        for user in users:
            accounts = AccountUser.objects.filter(user=user).select_related("account")

            self.stdout.write(f"User: {user.username} ({user.email})")

            if accounts.exists():
                self.stdout.write(self.style.SUCCESS(f"  Has {accounts.count()} account(s):"))
                for acc_user in accounts:
                    active = " (ACTIVE)" if acc_user.is_current_active else ""
                    admin = " [Admin]" if acc_user.is_admin else ""
                    self.stdout.write(f"    - {acc_user.account.name}{admin}{active}")
            else:
                self.stdout.write(self.style.ERROR("  No accounts!"))

                # Try to create account
                self.stdout.write("  Attempting to create account...")
                try:
                    account = Account.objects.create(name=f"{user.username}'s Account")
                    AccountUser.objects.create(account=account, user=user, is_admin=True, is_current_active=True)
                    self.stdout.write(self.style.SUCCESS(f"  Created account: {account.name}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Failed: {e}"))

            self.stdout.write("")

        # Summary
        self.stdout.write("=" * 60)
        total_accounts = Account.objects.count()
        users_with_accounts = User.objects.filter(id__in=AccountUser.objects.values_list("user_id", flat=True)).count()
        users_without_accounts = users.count() - users_with_accounts

        self.stdout.write(f"Total accounts: {total_accounts}")
        self.stdout.write(f"Users with accounts: {users_with_accounts}")

        if users_without_accounts > 0:
            self.stdout.write(self.style.WARNING(f"Users without accounts: {users_without_accounts}"))
        else:
            self.stdout.write(self.style.SUCCESS("All users have accounts!"))

        self.stdout.write("=" * 60 + "\n")
