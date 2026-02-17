# Static Files Guide

This guide explains how static files (images, CSS, JavaScript) work in Adapterly.

## Directory Structure

```
workflow-server/
├── static/                  # ← SOURCE: Project-level static files
│   ├── images/
│   │   └── logo.png
│   └── js/
│       └── dashboard.js
│
├── staticfiles/            # ← TARGET: collectstatic output (NOT in GIT!)
│   └── (collected files)
│
└── apps/
    └── core/
        └── static/         # ← App-specific statics (collected automatically)
            └── core/
                └── styles.css
```

## Development Usage (DEBUG=True)

Django serves static files automatically:

```python
# settings.py
DEBUG = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # Source directories
```

URLs in development:
- `http://127.0.0.1:8000/static/images/logo.png`
- `http://127.0.0.1:8000/static/js/dashboard.js`

## Production Usage (DEBUG=False)

### Step 1: Collect static files

```bash
# Locally or on the server:
python manage.py collectstatic --noinput
```

This copies all static files to the `STATIC_ROOT` directory:
- `/opt/adapterly/staticfiles/` (production)
- `./staticfiles/` (development)

### Step 2: Configure web server

Nginx/Apache serves files directly from the `STATIC_ROOT` directory:

**Nginx example:**
```nginx
server {
    listen 80;
    server_name example.com;

    location /static/ {
        alias /opt/adapterly/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Where Django Collects Static Files From

### 1. STATICFILES_DIRS (Project-level files)

```python
STATICFILES_DIRS = [
    BASE_DIR / "static",  # ← From here
]
```

**Use for:**
- Shared images (logos, icons)
- Shared JavaScript
- Shared CSS
- Third-party libraries

### 2. App-specific static/ directories (Automatic)

```
apps/core/static/core/styles.css  → /static/core/styles.css
apps/runs/static/runs/chart.js    → /static/runs/chart.js
```

**Use for:**
- App-specific resources
- Modular structure

## Referencing Files in Templates

### HTML Template

```django
{% load static %}

<!-- Project-level file -->
<img src="{% static 'images/logo.png' %}" alt="Logo">
<script src="{% static 'js/dashboard.js' %}"></script>

<!-- App-specific file -->
<link rel="stylesheet" href="{% static 'core/styles.css' %}">
```

### JavaScript

```javascript
// Absolute path
const logoUrl = '/static/images/logo.png';

// Or use template variable
const logoUrl = '{{ static("images/logo.png") }}';
```

### CSS

```css
/* Absolute path */
background-image: url('/static/images/background.jpg');

/* Relative path (if CSS is in static/css/styles.css) */
background-image: url('../images/background.jpg');
```

## Adding a New Static File

### Option 1: Project-level file (RECOMMENDED for shared files)

```bash
# Add the file
static/
├── images/
│   └── new-logo.png        # ← Add here
└── js/
    └── new-script.js       # ← Or here

# Use in template
{% static 'images/new-logo.png' %}
```

### Option 2: App-specific file

```bash
# Add the file (note the app name twice!)
apps/core/static/core/icons.svg

# Use in template
{% static 'core/icons.svg' %}
```

## Deploying to Production

### 1. Locally: Test collectstatic

```bash
# Collect files
python manage.py collectstatic --noinput

# Verify staticfiles/ contains everything
ls -la staticfiles/
```

### 2. On server: Deploy process

```bash
# SSH to server
ssh user@example.com

# Go to project directory
cd /opt/adapterly

# Activate virtual environment
source venv/bin/activate

# Update code
git pull

# Collect static files
python manage.py collectstatic --noinput

# Restart
sudo systemctl restart adapterly
```

### 3. Nginx serves the files

Nginx serves directly from the `/opt/adapterly/staticfiles/` directory.

## Environment Variables

### Development (.env)

```env
DEBUG=True
# No need for STATIC_ROOT, uses default
```

### Production (.env)

```env
DEBUG=False
STATIC_ROOT=/opt/adapterly/staticfiles
```

## Common Issues

### Issue: Files not showing in production

**Solution:**
```bash
# 1. Verify collectstatic has been run
python manage.py collectstatic --noinput

# 2. Check Nginx configuration
sudo nginx -t
sudo systemctl reload nginx

# 3. Check file permissions
ls -la /opt/adapterly/staticfiles/
```

### Issue: 404 Not Found for static files

**Solution:**
```python
# settings.py - make sure these are correct
STATIC_URL = "/static/"  # URL path
STATIC_ROOT = "/opt/adapterly/staticfiles"  # Physical path
STATICFILES_DIRS = [BASE_DIR / "static"]  # Source directories
```

### Issue: Old files showing (cache)

**Solution:**
```bash
# 1. Clear old staticfiles
rm -rf /opt/adapterly/staticfiles/*

# 2. Collect again
python manage.py collectstatic --noinput

# 3. Clear browser cache
# Ctrl+F5 or Cmd+Shift+R
```

## Cache Busting

Use versioned filenames to avoid cache issues:

### Manual versioning

```
static/js/dashboard.v2.js
static/css/styles.v3.css
```

### Django Template Cache Busting

```django
{% load static %}
<script src="{% static 'js/dashboard.js' %}?v=2"></script>
```

### WhiteNoise (Automatic, recommended)

```bash
pip install whitenoise
```

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Add here
    # ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## Checklist: Static Files in Production

- [ ] `STATIC_ROOT` set correctly
- [ ] `STATICFILES_DIRS` includes source directories
- [ ] `collectstatic` has been run
- [ ] Nginx/Apache configured to serve `/static/` → `STATIC_ROOT`
- [ ] File permissions are correct
- [ ] Cache busting enabled (WhiteNoise or versions)
- [ ] `DEBUG=False` in production

## Current Configuration

Adapterly's current settings:

```python
# Development (DEBUG=True)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # Collection target
STATICFILES_DIRS = [BASE_DIR / "static"]  # Source

# Production (DEBUG=False + .env)
STATIC_URL = "/static/"
STATIC_ROOT = "/opt/adapterly/staticfiles"  # Nginx serves from here
STATICFILES_DIRS = [BASE_DIR / "static"]  # Source
```

## File Locations

**Project-level statics (shared):**
```
static/
├── images/          # Logos, icons
├── js/             # Shared JavaScript
└── css/            # Shared CSS (if needed)
```

**App-specific statics (modular):**
```
apps/core/static/core/
apps/runs/static/runs/
```

## Testing

```bash
# In development
python manage.py runserver
# → http://127.0.0.1:8000/static/images/logo.png

# Production mode locally
DEBUG=False python manage.py collectstatic
python manage.py runserver --insecure  # Serves statics even when DEBUG=False
```

## More Information

- [Django Static Files Howto](https://docs.djangoproject.com/en/4.2/howto/static-files/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)
