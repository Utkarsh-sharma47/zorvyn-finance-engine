#!/bin/sh
# Always use the backend-root alembic.ini so Alembic finds script_location regardless of CWD.
set -e
exec /opt/venv/bin/_alembic -c /app/alembic.ini "$@"
