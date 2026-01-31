#!/usr/bin/env sh
set -e

cd /app/api
/app/.venv/bin/alembic upgrade head

exec /app/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8080}"
