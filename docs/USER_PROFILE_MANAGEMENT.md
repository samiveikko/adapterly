# User Profile & Account Management

## Overview

Users can now manage their personal settings and account information through the dashboard:

1. **Change Password** - Update account password securely
2. **Edit Account Name** - Rename accounts (admin only)

## Features

### 1. Password Change

**Location**: Dashboard → "My Profile" card → "Change Password" button

**How it works:**
- Click "Change Password" button
- Enter current password
- Enter new password (twice)
- Password validation ensures strong passwords
- Session remains active after password change

**Security Features:**
- Requires current password verification
- Password strength requirements enforced
- User stays logged in after change
- Django's built-in `PasswordChangeForm` for security

**URL**: `/account/change-password/`

**Access**: All authenticated users

### 2. Account Name Editing

**Location**: Dashboard → Account Info card → Pencil icon next to account name

**How it works:**
- Click the pencil icon next to account name
- Inline editing form appears
- Enter new name and click checkmark (✓)
- Or cancel with X button
- Name updates immediately

**Restrictions:**
- Only account admins can edit
- Account name cannot be empty

**URL**: `/account/change-name/` (POST only)

**Access**: Account admins only

## User Interface

### Dashboard Changes

#### **New "My Profile" Card**
Located in the right sidebar, shows:
- Username
- Email address
- "Change Password" button

#### **Enhanced Account Info Card**
- Account name with inline edit capability (admins only)
- Pencil icon for quick editing
- Edit form appears inline without page reload

## Technical Implementation

### Files Added/Modified

#### 1. **`apps/accounts/views.py`**
Added views:
```python
def change_password(request):
    """Allow user to change their password."""
    # Uses Django's PasswordChangeForm
    # Keeps session active with update_session_auth_hash
    
def change_account_name(request):
    """Change the name of the active account (admin only)."""
    # POST only
    # Validates permissions and input
```

#### 2. **`apps/accounts/urls.py`**
Added URL patterns:
```python
path('change-name/', views.change_account_name, name='change_account_name'),
path('change-password/', views.change_password, name='change_password'),
```

#### 3. **`apps/accounts/templates/accounts/change_password.html`**
New template for password change page:
- Clean, modern Material Design style
- Matches site theme (purple gradient accents)
- Security tips displayed
- Clear error messages
- Password strength requirements shown

#### 4. **`apps/accounts/templates/accounts/dashboard.html`**
Enhanced with:
- "My Profile" card in sidebar
- Inline account name editing
- JavaScript functions for smooth UX:
  - `showEditAccountName()` - Shows edit form
  - `hideEditAccountName()` - Hides edit form

## User Experience Flow

### Changing Password

```
1. User → Dashboard
2. Click "Change Password" in "My Profile" card
3. Password change page loads
4. Fill form:
   - Current password
   - New password
   - Confirm new password
5. Submit
6. Success message → Redirect to dashboard
7. User stays logged in ✓
```

### Changing Account Name

```
1. Admin → Dashboard  
2. Click pencil icon next to account name
3. Inline form appears
4. Type new name
5. Click checkmark ✓
6. Page reloads with new name
7. Success message displayed
```

## Security Considerations

### Password Change
- ✅ Requires authentication
- ✅ Requires current password verification
- ✅ Enforces password strength rules
- ✅ Session maintained after change
- ✅ CSRF protection enabled

### Account Name Change
- ✅ Admin-only access
- ✅ Input validation (non-empty)
- ✅ CSRF protection enabled
- ✅ Permission checks enforced

## Error Handling

### Password Change Errors
- **Wrong current password**: "Your old password was entered incorrectly"
- **Weak password**: Password strength requirements displayed
- **Passwords don't match**: "The two password fields didn't match"
- **Form validation errors**: Displayed inline with icons

### Account Name Change Errors
- **Empty name**: "Account name cannot be empty"
- **No permission**: "You don't have permission to change the account name"
- **Not admin**: Button not displayed

## Testing

### Test Password Change

```bash
# Login as a user
# Navigate to /account/
# Click "Change Password"
# Enter:
#   Current: old_password
#   New: new_strong_password_123!
#   Confirm: new_strong_password_123!
# Submit
# Verify: Still logged in, password changed
```

### Test Account Name Change

```bash
# Login as account admin
# Navigate to /account/
# Click pencil icon next to account name
# Enter new name: "My New Account"
# Click checkmark
# Verify: Name updated, success message shown
```

### Test Permissions

```bash
# Login as non-admin user
# Navigate to /account/
# Verify: No pencil icon shown for account name
# Try POST to /account/change-name/
# Verify: Permission denied
```

## UI/UX Features

### Visual Design
- 🎨 **Material Design** styling throughout
- 💜 **Purple gradient** accents matching site theme
- 🔒 **Security icons** (shield, lock, key)
- ✨ **Smooth transitions** for inline editing
- 📱 **Responsive** design for mobile

### User Feedback
- ✅ Success messages with icons
- ❌ Error messages with clear explanations
- 💡 Helpful hints and tips
- 🎯 Focused input fields on edit

### Accessibility
- Proper semantic HTML
- ARIA labels where needed
- Keyboard navigation support
- High contrast color scheme

## Future Enhancements

Potential additions:
- **Email change** functionality
- **Two-factor authentication** (2FA)
- **Profile picture** upload
- **Password strength meter** (visual)
- **Password history** (prevent reuse)
- **Account deletion** (with confirmation)
- **Account transfer** (ownership change)
- **Activity log** (recent changes)

## Related Documentation

- `docs/AUTO_ACCOUNT_CREATION.md` - Account creation on signup
- `docs/SECURITY_USER_INVITATIONS.md` - User invitation security
- `docs/GOOGLE_OAUTH_SETUP.md` - OAuth login setup

