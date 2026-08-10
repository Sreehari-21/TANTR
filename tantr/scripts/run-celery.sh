#!/usr/bin/env bash
# TANTR - Start Celery worker (from project root)
export PATH="$HOME/.local/bin:$HOME/.local/node/bin:$HOME/.local/python/bin:$PATH"
cd "$(dirname "$0")/.."
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
echo "Starting Celery worker..."
celery -A celery_app worker --loglevel=info
