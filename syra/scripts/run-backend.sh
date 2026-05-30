#!/usr/bin/env bash
# SYRA - Start backend (from project root)
set -e
cd "$(dirname "$0")/.."
cd backend
[[ -d venv ]] || python3 -m venv venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install -q -r requirements.txt
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit DATABASE_URL / CORS if needed"
fi
echo "Starting backend on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
