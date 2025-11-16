#!/bin/bash

# Run the Django development server with local settings

export DJANGO_SETTINGS_MODULE=config.settings.local

echo "Starting Django development server..."
echo "Visit: http://localhost:8000"
echo "Admin: http://localhost:8000/admin (username: admin, password: admin)"
echo "Demo: http://localhost:8000/demo"
echo ""
echo "Press Ctrl+C to stop the server"

poetry run python manage.py runserver