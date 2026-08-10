# TANTR production checklist

## Before go-live

1. **Secrets**
   - `SECRET_KEY`: at least 32 random bytes (`openssl rand -hex 32`).
   - Database password: strong; if it contains URL-special characters, set a full `DATABASE_URL` with proper encoding.
   - `OPENAI_API_KEY`: only if you use live AI evaluation.

2. **Environment**
   - `ENVIRONMENT=production`
   - `DEBUG=false`
   - `DEV_AUTO_CREATE_SCHEMA=false`
   - Schema applied with **Alembic** (`alembic upgrade head` via API Docker entrypoint or CI).

3. **Networking**
   - Set `CORS_ORIGINS` to your real frontend origin(s), comma-separated.
   - Set `NEXT_PUBLIC_API_URL` to the **public** API URL used by browsers (HTTPS in production).
   - Optionally set `TRUSTED_HOSTS` when behind a known hostname.

4. **Process model**
   - API: Gunicorn + Uvicorn workers (see `backend/Dockerfile`).
   - Celery worker: separate container; shares `/app/repos` volume with API.
   - Redis and PostgreSQL: managed services or hardened containers with persistence.

5. **Observability**
   - Ship container logs to your platform (CloudWatch, Datadog, etc.).
   - Use `GET /health` (liveness) and `GET /health/ready` (DB + Redis) for probes.

6. **OpenAPI**
   - `/docs` and `/redoc` are **disabled** when `ENVIRONMENT=production` (unless you temporarily set `DEBUG=true`, which production config forbids).

## Docker

**Quick start** (from `tantr/`):

```bash
./deploy/prod-up.sh
```

On first run this copies `docker/.env.production.example` → `docker/.env.production` and generates `SECRET_KEY` and `POSTGRES_PASSWORD`. Edit `CORS_ORIGINS` and `NEXT_PUBLIC_API_URL` when you have a real domain.

**Manual** (from `tantr/docker`):

```bash
cp .env.production.example .env.production
# edit .env.production — fill SECRET_KEY, POSTGRES_PASSWORD, CORS_ORIGINS, NEXT_PUBLIC_API_URL

docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

**Stop:** `./deploy/prod-down.sh`

## Migrations

- **Docker API image**: `scripts/docker-entrypoint.sh` runs `alembic upgrade head` before Gunicorn.
- **Manual**: `cd backend && alembic upgrade head`

## TLS

Terminate TLS at a reverse proxy (nginx, Caddy, cloud LB) in front of `web` and `api`; do not expose Postgres or Redis publicly.
