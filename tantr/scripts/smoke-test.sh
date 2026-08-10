#!/usr/bin/env bash
# TANTR API smoke test — run while backend is up on :8000
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/smoke_test.py"
