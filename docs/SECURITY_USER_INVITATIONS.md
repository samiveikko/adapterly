# Security: User Invitations

## Overview

For security and privacy reasons, the system **only supports email-based invitations**. Direct user addition from a list has been removed to prevent:
- Exposing all system users to account admins
- Privacy violations
- Potential security risks from seeing other users' information

## How User Invitations Work

### 1. **Email-Only Invitations**
Account admins can only invite users by email address. They cannot:
- See a list of all system users
- Add existing users directly from a dropdown
- Browse who else is using the system

### 2. **Invitation Process**

**Step 1: Admin Invites**
```
Admin → /account/invite/ → Enter email → Send invitation
```

**Step 2: User Receives Email**
- Stylish HTML email with invitation link
- Link expires in 7 days (configurable)
- Link format: `/account/invite/{token}/`

**Step 3: User Accepts**
- If user exists: Directly joins the account
- If new user: Signs up and joins the account
- Invalid/expired tokens are rejected

### 3. **Pending Invitations**
Admins can see their own pending invitations on the dashboard:
- Email address invited
- When invitation was sent
- Expiration time
- Current status (pending/used/expired)

## Security Benefits

### ✅ **Privacy Protection**
- Users cannot see who else is in the system
- Only email addresses of invited users are visible
- No user enumeration attacks possible

### ✅ **Access Control**
- All access is explicitly granted via invitation
- Invitations can be tracked and audited
- Expired invitations are automatically invalid

### ✅ **Email Verification**
- Users must have access to the invited email
- Prevents unauthorized account access
- Links are one-time use tokens

## Technical Implementation

### Files Modified

#### 1. **`apps/accounts/views.py`**
- ❌ **Removed**: `add_user_to_account()` function
- ✅ **Updated**: `account_dashboard()` - Shows pending invitations
- ✅ **Kept**: `invite_user()` - Email-based invitations only

#### 2. **`apps/accounts/urls.py`**
- ❌ **Removed**: `/add-user/` endpoint
- ✅ **Kept**: `/invite/` and `/invite/<token>/` endpoints

#### 3. **`apps/accounts/templates/accounts/dashboard.html`**
- ❌ **Removed**: "Add User" modal (~270 lines)
- ❌ **Removed**: User selection dropdown
- ❌ **Removed**: `available_users` list display
- ❌ **Removed**: JavaScript functions:
  - `openAddUserModal()`
  - `closeAddUserModal()`
  - `addUser()`
- ✅ **Added**: Pending invitations table
- ✅ **Simplified**: Single "Invite User" button

### What Was Removed

#### ❌ **Direct User Addition**
```python
# OLD - SECURITY RISK
available_users = User.objects.exclude(
    id__in=account_users.values_list('user_id', flat=True)
).order_by('username')
# This exposed ALL system users!
```

#### ❌ **User List Modal**
```html
<!-- OLD - SECURITY RISK -->
<select id="userSelect">
  {% for user in available_users %}
    <option value="{{ user.id }}">
      {{ user.username }} ({{ user.email }})
    </option>
  {% endfor %}
</select>
<!-- This showed all users to admins! -->
```

### What Remains

#### ✅ **Email-Based Invitations**
```python
# CURRENT - SECURE
pending_invitations = UserInvitation.objects.filter(
    account=active_account,
    is_used=False
)
# Only shows invitations sent by this account
```

#### ✅ **Pending Invitations Display**
```html
<!-- CURRENT - SECURE -->
{% for invitation in pending_invitations %}
  <tr>
    <td>{{ invitation.email }}</td>
    <td>{{ invitation.created_at|timesince }} ago</td>
    <td>{{ invitation.expires_at|timeuntil }}</td>
    <td><span class="badge">Pending</span></td>
  </tr>
{% endfor %}
```

## User Experience

### For Account Admins

**Before (Insecure)**:
1. Click "Add User"
2. See dropdown with ALL system users
3. Select user from list
4. User added immediately

**After (Secure)**:
1. Click "Invite User"
2. Enter email address
3. Send invitation email
4. User receives email and accepts
5. User joins account

### For Invited Users

**Existing User**:
1. Receive invitation email
2. Click link in email
3. Log in (if not already)
4. Automatically join account

**New User**:
1. Receive invitation email
2. Click link in email
3. Sign up with credentials
4. Automatically join account

## Configuration

### Invitation Settings

Location: `apps/accounts/models.py` → `UserInvitation`

```python
class UserInvitation(models.Model):
    expires_at_days = models.IntegerField(default=7)  # Change expiration days
```

### Email Template

Location: `apps/accounts/templates/accounts/emails/invitation.html`

Customize the invitation email:
- Branding
- Message text
- Button styling
- Footer information

## Best Practices

### For Admins

1. **Verify Email Addresses**
   - Double-check spelling before sending
   - Confirm with recipient out-of-band

2. **Monitor Pending Invitations**
   - Check dashboard for unused invitations
   - Resend if not accepted within a few days
   - Clean up expired invitations

3. **Use Role-Based Access**
   - Only grant admin privileges when necessary
   - Review user roles regularly

### For Development

1. **Never Expose User Lists**
   - Avoid queries that return all users
   - Use invitations for all user addition

2. **Validate Tokens**
   - Check expiration before accepting
   - Mark tokens as used immediately
   - Use UUIDs for unpredictable tokens

3. **Audit Invitations**
   - Log who invited whom
   - Track invitation acceptance
   - Monitor for suspicious patterns

## Migration Note

If you have existing code or scripts that use `add_user_to_account`:

```python
# OLD - NO LONGER AVAILABLE
response = requests.post('/account/add-user/', {
    'account_id': account_id,
    'user_id': user_id
})

# NEW - USE INVITATION INSTEAD
response = requests.post('/account/invite/', {
    'email': 'user@example.com',
    'is_admin': False
})
```

## Testing

### Test Email Invitations

```bash
python manage.py shell
```

```python
from apps.accounts.models import UserInvitation, Account
from django.contrib.auth import get_user_model

User = get_user_model()

# Get account and inviter
account = Account.objects.first()
inviter = User.objects.first()

# Create invitation
invitation = UserInvitation.objects.create(
    email='test@example.com',
    account=account,
    invited_by=inviter,
    is_admin=False
)

# Check expiration
print(f"Expires at: {invitation.expires_at}")
print(f"Is expired: {invitation.expires_at < timezone.now()}")

# Send email
invitation.send_invitation_email()
print(f"Invitation link: /account/invite/{invitation.token}/")
```

## Troubleshooting

### "No way to add existing users"
- **Correct**: This is by design for security
- **Solution**: Use email invitations
- **Note**: Users can sign up if they don't exist

### "Can't see all system users"
- **Correct**: This is intentional for privacy
- **Solution**: Invite users by their known email addresses
- **Note**: This prevents user enumeration attacks

### "Invitation email not received"
- Check email configuration in `.env`
- Verify EMAIL_HOST settings
- Check spam folder
- Test with `python manage.py test_email`

## Related Documentation

- `docs/AUTO_ACCOUNT_CREATION.md` - Auto account creation on signup
- `docs/EMAIL_CONFIGURATION.md` - Email setup
- `docs/GOOGLE_OAUTH_SETUP.md` - OAuth login setup

