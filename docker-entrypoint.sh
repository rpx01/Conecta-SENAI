#!/bin/sh

echo "Waiting for database..."
# TODO: Add wait-for-db logic if necessary

echo "Applying database migrations..."
flask --app src.main db upgrade

echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8080 "src.main:app"
