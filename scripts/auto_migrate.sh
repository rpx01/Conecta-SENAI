#!/usr/bin/env bash
# Automates Alembic migrations based on SQLAlchemy models.
# Usage: ./scripts/auto_migrate.sh [migration message]

set -euo pipefail

MESSAGE=${1:-"Auto migration $(date +%Y%m%d%H%M)"}

# Ensure database is up to date
flask --app src.main db upgrade

# Autogenerate a new migration if there are model changes
flask --app src.main db migrate -m "$MESSAGE" || true

# Apply new migrations (if any)
flask --app src.main db upgrade
