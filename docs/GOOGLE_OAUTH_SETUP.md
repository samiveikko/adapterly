# Google OAuth Configuration Guide

This guide explains how to enable Google authentication for your Adapterly application.

## Overview

The application is already configured to support Google OAuth login. You just need to:
1. Create Google OAuth credentials
2. Add them to Django admin
3. Test the login

## Step 1: Create Google OAuth Credentials

### 1.1 Go to Google Cloud Console
Visit: https://console.cloud.google.com/

### 1.2 Create a New Project (or select existing)
1. Click on the project dropdown at the top
2. Click "New Project"
3. Name it (e.g., "Adapterly")
4. Click "Create"

### 1.3 Enable Google+ API
1. Go to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click on it and press "Enable"

### 1.4 Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" (or "Internal" if you have Google Workspace)
3. Fill in required fields:
   - **App name**: Adapterly
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Click "Save and Continue"
5. Skip "Scopes" (click "Save and Continue")
6. Add test users if needed (for development)
7. Click "Save and Continue"

### 1.5 Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Web application"
4. Configure:
   - **Name**: Adapterly Web Client
   - **Authorized JavaScript origins**:
     - `http://127.0.0.1:8000` (for local development)
     - `http://localhost:8000` (for local development)
     - `https://example.com` (for production)
   - **Authorized redirect URIs**:
     - `http://127.0.0.1:8000/auth/google/login/callback/`
     - `http://localhost:8000/auth/google/login/callback/`
     - `https://example.com/auth/google/login/callback/`
5. Click "Create"
6. **IMPORTANT**: Copy your **Client ID** and **Client Secret**

## Step 2: Add Credentials to Django

### Method 1: Django Admin (Recommended)

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. Go to Django admin: http://127.0.0.1:8000/admin/

3. Navigate to:
   - **Sites** > **Sites** > Click on "example.com"
   - Change:
     - **Domain name**: `127.0.0.1:8000` (for local) or `example.com` (for production)
     - **Display name**: Adapterly
   - Click "Save"

4. Go back and navigate to:
   - **Social Applications** > **Social applications** > Click "Add social application"

5. Fill in:
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: [Your Client ID from Google]
   - **Secret key**: [Your Client Secret from Google]
   - **Sites**: Select your site (should be "127.0.0.1:8000" or "example.com")
   - Click "Save"

### Method 2: Django Shell (Alternative)

```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# Update site
site = Site.objects.get(id=1)
site.domain = '127.0.0.1:8000'  # or 'example.com' for production
site.name = 'Adapterly'
site.save()

# Create social app
social_app = SocialApp.objects.create(
    provider='google',
    name='Google OAuth',
    client_id='YOUR_CLIENT_ID_HERE',
    secret='YOUR_CLIENT_SECRET_HERE',
)
social_app.sites.add(site)
print("Google OAuth configured successfully!")
```

## Step 3: Test the Login

1. Go to login page: http://127.0.0.1:8000/auth/login/

2. You should see:
   - Traditional email/username & password form
   - **"Continue with Google"** button below

3. Click "Continue with Google"

4. You'll be redirected to Google's login page

5. After successful login, you'll be redirected back to the application

## Troubleshooting

### "redirect_uri_mismatch" Error
- Make sure the redirect URI in Google Console exactly matches your Django site
- Check that the domain in Django's `Site` model matches your current domain
- Common mistake: Using `http://localhost:8000` in Google but `http://127.0.0.1:8000` in Django (or vice versa)

### "Social application not found" Error
- Make sure you've added the site to the social application in Django admin
- Check that `SITE_ID` in settings.py matches your site's ID

### Google Button Not Showing
- Check that `allauth.socialaccount.providers.google` is in `INSTALLED_APPS`
- Verify that the social application is configured in Django admin
- Check browser console for JavaScript errors

### "invalid_client" Error
- Double-check your Client ID and Client Secret
- Make sure you're using OAuth 2.0 credentials (not API key or service account)

## Production Configuration

For production (`example.com`):

1. Update Google Console:
   - Add `https://example.com` to authorized origins
   - Add `https://example.com/auth/google/login/callback/` to redirect URIs

2. Update Django Site:
   ```python
   site = Site.objects.get(id=1)
   site.domain = 'example.com'
   site.save()
   ```

3. Update social app to use the new site if needed

## Security Notes

- **Never commit** Client Secret to Git
- Use environment variables for production secrets (optional enhancement)
- Keep your OAuth consent screen information up to date
- Regularly review authorized domains in Google Console

## Additional Features

### Auto-create Account on First Login
Django-allauth automatically creates a user account when someone logs in with Google for the first time. The email from Google is used as the primary identifier.

### Automatic Username Generation
The custom `CustomSocialAccountAdapter` automatically generates usernames from:
1. Email address (before @)
2. First name (if available)
3. Provider ID (fallback)

This means users can sign in with Google without seeing any additional forms - the system automatically creates everything needed.

### Link Google to Existing Account
If a user already has an account with the same email, they can link their Google account by:
1. Logging in with username/password
2. Going to account settings (you can add this feature)
3. Connecting Google OAuth

### Disconnect Google Account
Users can disconnect their Google account in Django admin under "Social Accounts".

## Environment Variable Configuration (Optional)

If you want to store credentials in `.env` instead of the database, you can create a custom configuration:

```python
# In config/settings.py
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', ''),
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
```

Then add to `.env`:
```
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
```

However, the database method (Method 1 above) is simpler and Django's standard approach.

