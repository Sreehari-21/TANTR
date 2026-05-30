#!/usr/bin/env bash
# SYRA - Start Celery worker (from project root)
set -e
cd "$(dirname "$0")/.."
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
echo "Starting Celery worker..."
celery -A celery_app worker --loglevel=info
