#!/usr/bin/env bash
# Start full local SYRA stack (API, optional Celery, frontend).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if command -v docker >/dev/null 2>&1; then
  echo "Starting Postgres + Redis (Docker)..."
  (cd "$ROOT/docker" && docker compose up -d) || true
fi

chmod +x "$ROOT/scripts/run-backend.sh" "$ROOT/scripts/run-celery.sh" "$ROOT/scripts/run-frontend.sh"

echo ""
echo "Starting backend → http://localhost:8000"
"$ROOT/scripts/run-backend.sh" &
BACKEND_PID=$!
sleep 3

if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
  echo "Backend OK"
else
  echo "WARN: Backend not ready — check logs above"
fi

echo "Starting Celery worker (optional)..."
"$ROOT/scripts/run-celery.sh" &
CELERY_PID=$!

echo "Starting frontend → http://localhost:3001"
"$ROOT/scripts/run-frontend.sh" &
FRONTEND_PID=$!

echo ""
echo "SYRA dev stack running (Ctrl+C stops this script; child processes may keep running)"
echo "  App:  http://localhost:3001"
echo "  API:  http://localhost:8000/docs"
echo "  Test: ./scripts/smoke-test.sh"
echo ""

trap 'kill $BACKEND_PID $CELERY_PID $FRONTEND_PID 2>/dev/null || true' INT TERM
wait
