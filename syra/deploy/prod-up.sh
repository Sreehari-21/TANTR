#!/usr/bin/env bash
# Bootstrap and start SYRA production stack (Docker Compose).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_DIR="$ROOT/docker"
ENV_FILE="$DOCKER_DIR/.env.production"
EXAMPLE="$DOCKER_DIR/.env.production.example"

cd "$DOCKER_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Creating $ENV_FILE from example..."
  cp "$EXAMPLE" "$ENV_FILE"
  SECRET_KEY="$(openssl rand -hex 32)"
  POSTGRES_PASSWORD="$(openssl rand -hex 16)"
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" "$ENV_FILE"
    sed -i '' "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" "$ENV_FILE"
  else
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" "$ENV_FILE"
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" "$ENV_FILE"
  fi
  echo "Generated SECRET_KEY and POSTGRES_PASSWORD in .env.production"
else
  echo "Using existing $ENV_FILE"
fi

# Require SECRET_KEY to be set (not empty)
if grep -qE '^SECRET_KEY=$' "$ENV_FILE"; then
  echo "ERROR: Set SECRET_KEY in $ENV_FILE (openssl rand -hex 32)" >&2
  exit 1
fi
if grep -q '^POSTGRES_PASSWORD=generate-a-strong-password-here' "$ENV_FILE"; then
  echo "ERROR: Set POSTGRES_PASSWORD in $ENV_FILE" >&2
  exit 1
fi

chmod +x "$ROOT/backend/scripts/docker-entrypoint.sh" 2>/dev/null || true

echo "Building and starting production stack..."
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

echo ""
echo "Waiting for API health..."
for i in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:${API_PORT:-8000}/health/ready" >/dev/null 2>&1; then
    echo "API is ready."
    break
  fi
  sleep 2
  if [[ "$i" -eq 60 ]]; then
    echo "WARN: API not ready yet. Check: docker compose -f docker-compose.prod.yml logs api"
  fi
done

# Show URLs using ports from .env.production
WEB_PORT="$(grep -E '^WEB_PORT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true)"
API_PORT="$(grep -E '^API_PORT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true)"
WEB_PORT="${WEB_PORT:-3001}"
API_PORT="${API_PORT:-8000}"

echo ""
echo "SYRA production stack is up:"
echo "  App:  http://localhost:${WEB_PORT}"
echo "  API:  http://localhost:${API_PORT}/health"
echo ""
echo "Logs:  cd $DOCKER_DIR && docker compose -f docker-compose.prod.yml logs -f"
echo "Stop:  cd $DOCKER_DIR && docker compose -f docker-compose.prod.yml down"
