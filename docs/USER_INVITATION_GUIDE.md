# User Invitation System Guide

This guide explains how to invite users to your Adapterly account via email.

## Overview

The user invitation system allows account administrators to:
- Invite new users via email
- Automatically add existing users to the account
- Send beautifully formatted HTML invitation emails
- Manage invitation expiration (default: 7 days)
- Grant administrator privileges during invitation

## How It Works

### Flow Diagram

```
Admin invites user
       ↓
System checks if email is registered
       ↓
   ┌───────────────┴───────────────┐
   │                               │
Registered                    Not Registered
   │                               │
Add to account               Create invitation
immediately                        ↓
                           Send email with link
                                   ↓
                           User clicks link
                                   ↓
                           Create account
                                   ↓
                           Add to account
```

## Features

### 1. **Email-Based Invitations**
- Beautiful HTML email template with Adapterly branding
- Plain text fallback for email clients
- One-click acceptance link
- Invitation status tracking

### 2. **Automatic User Detection**
- If email is already registered → Add directly to account
- If email is not registered → Send invitation email

### 3. **Invitation Management**
- Unique token for each invitation (UUID)
- Expiration tracking (default 7 days)
- Prevent duplicate invitations
- Mark invitations as used

### 4. **Administrator Privileges**
- Optionally grant admin rights during invitation
- Clearly indicated in invitation email
- Automatically applied when account is created

## Usage

### As an Administrator

#### Step 1: Navigate to Invite Page

```
Account Dashboard → Invite User
or
/accounts/invite/
```

#### Step 2: Enter User Details

Fill in the form:
- **Email**: User's email address (required)
- **Admin privileges**: Check if user should be an administrator

#### Step 3: Send Invitation

Click "Send Invitation" button.

**What happens next:**

**If user exists:**
```
✅ User [username] added to account.
```

**If user doesn't exist:**
```
✅ Invitation sent to [email].
📧 Email sent with invitation link
```

### As an Invited User

#### Step 1: Check Your Email

You'll receive an email with subject:
```
Invitation to join [Account Name] on Adapterly
```

#### Step 2: Click Accept Link

Click the "Accept Invitation & Create Account" button in the email.

#### Step 3: Create Account

Fill in the registration form:
- **Username**: Choose your username
- **Password**: Create a secure password
- **Confirm Password**: Re-enter your password

#### Step 4: Start Using Adapterly

After successful registration:
- You're automatically added to the account
- The account is set as your active account
- You can log in immediately

## Email Template

The invitation email includes:

### Header
- Adapterly branding with gradient logo
- "You've been invited! 🎉" heading

### Body
- Inviter's name
- Account name
- Admin badge (if applicable)
- Brief description of Adapterly
- Call-to-action button

### Footer
- Company information
- Expiration notice
- Alternative text link

### Example Email

```html
===========================================
            Adapterly
===========================================

You've been invited! 🎉

Hi there,

John Smith has invited you to join their
team on Adapterly.

┌─────────────────────────────────────┐
│  Project Alpha                      │
│  [Administrator Privileges]         │
└─────────────────────────────────────┘

Adapterly is an integration platform
that helps teams streamline their
processes and boost productivity.

    [Accept Invitation & Create Account]

⏱️ This invitation expires in 7 days.

-------------------------------------------
If you weren't expecting this invitation,
you can safely ignore this email.
===========================================
```

## Database Models

### UserInvitation Model

```python
class UserInvitation(models.Model):
    email = models.EmailField()
    account = models.ForeignKey(Account)
    invited_by = models.ForeignKey(User)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_admin = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at_days = models.IntegerField(default=7)
```

### Key Properties

**`expires_at`** (property):
```python
@property
def expires_at(self):
    from datetime import timedelta
    return self.created_at + timedelta(days=self.expires_at_days)
```

**`is_expired()`** (method):
```python
def is_expired(self):
    return timezone.now() > self.expires_at
```

**`send_invitation_email(request)`** (method):
Sends HTML email with invitation link.

## URL Routes

### Invitation URLs

| Route | View | Description |
|-------|------|-------------|
| `/accounts/invite/` | `invite_user` | Show invitation form (admin only) |
| `/accounts/invite/<token>/` | `accept_invitation` | Accept invitation and register |

### Example URLs

```
# Invitation form
https://example.com/accounts/invite/

# Accept invitation
https://example.com/accounts/invite/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

## API / AJAX Integration

Currently, invitations are handled via Django views. 

**Future enhancement:** Create REST API endpoints:
```
POST /api/accounts/invitations/        - Create invitation
GET  /api/accounts/invitations/        - List invitations
GET  /api/accounts/invitations/<id>/   - Get invitation details
POST /api/accounts/invitations/<id>/accept/  - Accept invitation
DELETE /api/accounts/invitations/<id>/  - Cancel invitation
```

## Security Features

### 1. **UUID Tokens**
- Cryptographically secure random tokens
- 128-bit UUID (v4)
- Virtually impossible to guess

### 2. **Expiration**
- Invitations expire after 7 days
- Prevents indefinite valid links
- Configurable per invitation

### 3. **One-Time Use**
- Marked as used after acceptance
- Cannot be reused
- Prevents account takeover

### 4. **Admin-Only Access**
- Only account administrators can invite users
- Permission checked on every request
- Prevents unauthorized invitations

### 5. **Email Ownership Verification**
- User must have access to invited email
- Registers with invited email address
- Prevents impersonation

## Configuration

### Email Settings

Required environment variables:
```env
EMAIL_HOST=email-smtp.eu-west-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-smtp-username
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=noreply@example.com
```

See `docs/EMAIL_CONFIGURATION.md` for details.

### Invitation Expiration

Change default expiration:
```python
# Create invitation with custom expiration
invitation = UserInvitation.objects.create(
    email='user@example.com',
    account=account,
    invited_by=request.user,
    is_admin=False,
    expires_at_days=14  # 14 days instead of 7
)
```

## Troubleshooting

### Email Not Received

**Problem:** User didn't receive invitation email

**Solutions:**
1. Check spam/junk folder
2. Verify email configuration (run `python manage.py test_email`)
3. Check email is verified in Amazon SES (if using SES)
4. Check server logs for email errors
5. Resend invitation from dashboard

### Invitation Expired

**Problem:** User gets "This invitation has expired" error

**Solutions:**
1. Admin resends invitation (creates new token)
2. Admin adds user directly if they're registered
3. Increase expiration days for future invitations

### Username Already Taken

**Problem:** User can't complete registration

**Solutions:**
1. Try a different username
2. Admin can check existing users
3. User can log in if account already exists

### Invitation Already Used

**Problem:** User gets "invitation already used" error

**Solutions:**
1. User should log in with existing credentials
2. Admin can check if user is already in account
3. Admin resends new invitation if needed

## Best Practices

### 1. **Verify Email Before Sending**
```python
# Check email format
import re
email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
if not re.match(email_pattern, email):
    return "Invalid email format"
```

### 2. **Provide Context**
- Tell user what account they're being invited to
- Explain who invited them
- Include link to learn more about Adapterly

### 3. **Set Appropriate Expiration**
- 7 days is good for internal teams
- 14 days for external partners
- 3 days for time-sensitive projects

### 4. **Track Invitations**
```python
# Get pending invitations
pending = UserInvitation.objects.filter(
    account=account,
    is_used=False,
    created_at__gt=timezone.now() - timedelta(days=7)
)
```

### 5. **Clean Up Old Invitations**
```python
# Delete expired unused invitations
from django.utils import timezone
UserInvitation.objects.filter(
    is_used=False,
    created_at__lt=timezone.now() - timedelta(days=30)
).delete()
```

## Admin View

### Pending Invitations

Show pending invitations on dashboard:

```python
# In view
pending_invitations = UserInvitation.objects.filter(
    account=active_account,
    is_used=False
).order_by('-created_at')

# In template
{% for inv in pending_invitations %}
  <tr>
    <td>{{ inv.email }}</td>
    <td>{{ inv.invited_by.username }}</td>
    <td>
      {% if inv.is_expired %}
        <span class="badge bg-danger">Expired</span>
      {% else %}
        <span class="badge bg-warning">Pending</span>
      {% endif %}
    </td>
    <td>{{ inv.created_at|timesince }} ago</td>
    <td>
      <button class="btn btn-sm btn-danger" 
              onclick="cancelInvitation('{{ inv.id }}')">
        Cancel
      </button>
    </td>
  </tr>
{% endfor %}
```

## Future Enhancements

### 1. **Invitation Templates**
- Multiple email templates
- Customizable per account
- Localization support

### 2. **Bulk Invitations**
- Import CSV with email list
- Mass invite multiple users
- Track bulk invitation status

### 3. **Custom Roles**
- Define custom roles beyond admin/member
- Assign permissions per role
- Role-based access control

### 4. **Invitation Reminders**
- Send reminder after 3 days
- Notify admin of pending invitations
- Auto-cancel after expiration

### 5. **Analytics**
- Track invitation acceptance rate
- Time to acceptance
- Most active inviters

## Testing

### Manual Testing

1. **Invite existing user:**
```bash
# Should add directly to account
Email: existing@example.com
Result: "User added to account"
```

2. **Invite new user:**
```bash
# Should send email
Email: new@example.com
Result: "Invitation sent"
Check: Email received
```

3. **Accept invitation:**
```bash
# Click link in email
# Fill registration form
Result: Account created and logged in
```

4. **Test expiration:**
```bash
# In Django shell
from apps.accounts.models import UserInvitation
inv = UserInvitation.objects.last()
inv.created_at = timezone.now() - timedelta(days=8)
inv.save()

# Try to accept
Result: "This invitation has expired"
```

### Automated Testing

```python
from django.test import TestCase, Client
from apps.accounts.models import Account, UserInvitation
from django.contrib.auth import get_user_model

class InvitationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.admin = User.objects.create_user('admin', 'admin@test.com', 'pass')
        self.account = Account.objects.create(name='Test Account')
        # Add admin to account...
    
    def test_invite_new_user(self):
        self.client.login(username='admin', password='pass')
        response = self.client.post('/accounts/invite/', {
            'email': 'newuser@test.com',
            'is_admin': 'on'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            UserInvitation.objects.filter(email='newuser@test.com').exists()
        )
    
    def test_accept_invitation(self):
        invitation = UserInvitation.objects.create(
            email='invited@test.com',
            account=self.account,
            invited_by=self.admin
        )
        response = self.client.post(f'/accounts/invite/{invitation.token}/', {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(invitation.is_used)
```

## Support

For issues or questions:
1. Check this documentation
2. Check `docs/EMAIL_CONFIGURATION.md`
3. Check `docs/AMAZON_SES_SETUP.md`
4. Contact system administrator

