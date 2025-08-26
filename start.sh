#!/usr/bin/env bash
set -euo pipefail
echo "[start] Running DB migrations..."
flask --app src.main db upgrade
echo "[start] Starting Gunicorn..."
exec gunicorn -c gunicorn.conf.py "src.main:create_app()"
