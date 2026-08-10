#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../docker"
docker compose -f docker-compose.prod.yml --env-file .env.production down "$@"
