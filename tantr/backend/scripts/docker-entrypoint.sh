#!/bin/sh
set -e
cd /app
echo "Running database migrations..."
alembic upgrade head
exec "$@"
