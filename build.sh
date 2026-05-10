#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Make database migrations
python manage.py makemigrations

# Apply database migrations
python manage.py migrate

# Create superuser if the environment variable is set
if [[ $CREATE_SUPERUSER ]]; then
  python manage.py createsuperuser --noinput
fi
