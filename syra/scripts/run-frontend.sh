#!/usr/bin/env bash
# SYRA - Start frontend (from project root)
set -e
cd "$(dirname "$0")/.."
cd frontend
[[ -d node_modules ]] || npm install
PORT="${PORT:-3001}"
export PORT
echo "Starting frontend on http://localhost:${PORT}"
npm run dev
