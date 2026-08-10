#!/usr/bin/env bash
# TANTR - Start frontend (from project root)
export PATH="$HOME/.local/bin:$HOME/.local/node/bin:$HOME/.local/python/bin:$PATH"
cd "$(dirname "$0")/.."
cd frontend
[[ -d node_modules ]] || npm install
PORT="${PORT:-3001}"
export PORT
echo "Starting frontend on http://localhost:${PORT}"
# Webpack is more stable here after the SYRA→TANTR rename (Turbopack cache panics)
npm run dev -- --webpack -p "${PORT}"
