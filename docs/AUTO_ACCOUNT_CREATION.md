# Automatic Account Creation

## Overview

When a user signs up (via regular signup or Google OAuth), the system automatically creates a personal account for them. This ensures every user has at least one account to work with immediately.

## How It Works

### 1. **Signup Signal**
When a user signs up (either via regular form or social login), a Django signal fires:

```python
@receiver(user_signed_up)
def create_personal_account_on_signup(sender, request, user, **kwargs):
    # Creates "{username}'s Account" or "{first_name}'s Account"
    # Links user as admin with is_current_active=True
```

Location: `apps/accounts/signals.py`

### 2. **Fallback Signal**
As a backup, when a User object is created, another signal ensures they have an account:

```python
@receiver(post_save, sender=User)
def ensure_user_has_account(sender, instance, created, **kwargs):
    # Only fires if user somehow doesn't have an account
```

### 3. **Welcome Page**
If a user logs in without an account (edge case), they're redirected to `/account/welcome/` which:
- Creates an account if needed
- Shows a loading screen
- Redirects to home after 2 seconds

## User Flow

### First-Time Google Login:
1. User clicks "Continue with Google"
2. Google authentication
3. User account created
4. **Signal fires → Personal account created automatically**
5. User lands on home page with active account ✅

### First-Time Regular Signup:
1. User fills signup form
2. Account created
3. **Signal fires → Personal account created automatically**
4. User lands on home page with active account ✅

### Edge Case (No Account):
1. User somehow has no account
2. Middleware detects this
3. User redirected to `/account/welcome/`
4. Welcome page creates account
5. User redirected to home ✅

## Account Details

Each automatically created account:
- **Name**: `{username}'s Account` (or `{first_name}'s Account` if available)
- **User Role**: Admin
- **Status**: Active (is_current_active=True)

## Multi-Account Support

Users can:
1. **Have multiple accounts** via invitations
2. **Switch between accounts** at `/account/switch/`
3. **Create additional accounts** (can be implemented)
4. **Be invited to team accounts** via email invitation system

## Configuration

No configuration needed! The system works automatically via:
- `apps/accounts/signals.py` - Signal handlers
- `apps/accounts/apps.py` - Signal registration
- `apps/accounts/middleware.py` - Welcome page redirect
- `apps/accounts/views.py` - Welcome page view

## Related Files

- `apps/accounts/signals.py` - Account creation signals
- `apps/accounts/middleware.py` - Active account middleware
- `apps/accounts/templates/accounts/welcome.html` - Welcome page
- `apps/accounts/models.py` - Account and AccountUser models

## Benefits

✅ **Seamless onboarding** - No manual setup required
✅ **Works with OAuth** - Google login creates accounts automatically  
✅ **Fallback protection** - Multiple layers ensure account creation
✅ **Multi-account ready** - Users can join multiple accounts later
✅ **Admin by default** - Users are admins of their own accounts

## Testing

To test the automatic account creation:

1. **New Google Login**:
   ```bash
   # Login with a new Google account at /auth/login/
   # Check that account was created automatically
   ```

2. **Regular Signup**:
   ```bash
   # Sign up at /auth/signup/
   # Check that account was created
   ```

3. **Check Account**:
   ```python
   python manage.py shell
   from django.contrib.auth import get_user_model
   from apps.accounts.models import AccountUser
   
   User = get_user_model()
   user = User.objects.last()
   accounts = AccountUser.objects.filter(user=user)
   print(f"User {user.username} has {accounts.count()} account(s)")
   ```

## Future Enhancements

Possible improvements:
- Allow users to customize account name during signup
- Offer team account creation flow
- Add account templates (personal, team, organization)
- Support account transfer/ownership changes

