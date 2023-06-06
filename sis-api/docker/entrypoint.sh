#!/usr/bin/env sh

echo "Collecting static..."
python manage.py collectstatic --noinput

echo 'Synchronizing database...'
python manage.py migrate --noinput

echo 'Starting'
"$@"  # execute command passed to script
