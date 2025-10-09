#!/usr/bin/env bash
set -euo pipefail

export FLASK_APP="${FLASK_APP:-src.main}"
echo "[start] Running DB migrations..."
SCHEDULER_ENABLED=${SCHEDULER_ENABLED:-0} flask db upgrade || true
echo "[start] Starting Gunicorn..."
exec gunicorn "src.main:create_app()" \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers 1 \
  --threads 1 \
  --max-requests 200 \
  --max-requests-jitter 50 \
  --timeout 30 \
  --graceful-timeout 30 \
  --keep-alive 2 \
  --log-level info
