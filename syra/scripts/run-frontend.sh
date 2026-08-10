#!/usr/bin/env bash
# SYRA - Start frontend (from project root)
export PATH="$HOME/.local/bin:$HOME/.local/node/bin:$HOME/.local/python/bin:$PATH"
cd "$(dirname "$0")/.."
cd frontend
[[ -d node_modules ]] || npm install
PORT="${PORT:-3001}"
export PORT
echo "Starting frontend on http://localhost:${PORT}"
npm run dev
