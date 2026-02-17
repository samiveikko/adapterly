# Environment Variables Configuration

This file documents the environment variables used by the workflow server application.

## Object Storage Configuration

The application supports storing large workflow table data in Hetzner Object Storage (S3-compatible) instead of the database. This keeps the database size minimal and improves performance.

### Required Environment Variables

```bash
# Enable object storage for storing large workflow table data
OBJECT_STORAGE_ENABLED=false

# Hetzner Object Storage endpoint
# Example: https://fsn1.your-objectstorage.com
OBJECT_STORAGE_ENDPOINT=

# Access credentials for Hetzner Object Storage
OBJECT_STORAGE_ACCESS_KEY=your_access_key_here
OBJECT_STORAGE_SECRET_KEY=your_secret_key_here

# S3 bucket name for storing workflow tables
OBJECT_STORAGE_BUCKET=workflow-tables

# Region for the object storage (typically eu-central for Hetzner)
OBJECT_STORAGE_REGION=eu-central
```

### Setup Instructions

1. **Create a bucket** in your Hetzner Object Storage account
2. **Generate access keys** (Access Key ID and Secret Access Key)
3. **Create a `.env` file** in the project root directory
4. **Add the variables** with your actual values
5. **Set `OBJECT_STORAGE_ENABLED=true`** to enable the feature

### How It Works

- When enabled, workflow table data is automatically uploaded to S3
- Only metadata (storage type, URI, row count) is stored in the database
- Tables are lazy-loaded from S3 when needed by SQL queries
- Fallback to database storage if S3 upload fails
- Old workflows with data in the database continue to work

### Testing

To test the configuration:

```bash
# With object storage disabled (default)
OBJECT_STORAGE_ENABLED=false python manage.py runserver

# With object storage enabled
OBJECT_STORAGE_ENABLED=true python manage.py runserver
```

## Other Environment Variables

### Django Configuration

```bash
# Django secret key (required for production)
SECRET_KEY=your-secret-key-here

# Debug mode (set to False in production)
DEBUG=True

# Allowed hosts (comma-separated)
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database Configuration

The application uses SQLite by default. For production, configure PostgreSQL:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/workflow_db
```

## Creating the .env File

Create a `.env` file in the project root directory:

```bash
# Copy from this template
cp ENV_VARIABLES.md .env

# Edit the file with your actual values
nano .env
```

**Note:** The `.env` file should never be committed to version control. It's automatically ignored by git.
