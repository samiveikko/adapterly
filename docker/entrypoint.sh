#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-adapterly}" -q; do
    sleep 1
done
echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Loading adapters..."
python manage.py load_adapters

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
