# TANTR

GitHub-like learning platform where students commit code and an AI "Professor Engine" evaluates commits with grades and feedback.

## Project structure

```
tantr/
├── backend/          # FastAPI backend
│   ├── main.py
│   ├── celery_app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── tasks/        # Celery tasks
│   ├── ai_engine/
│   ├── analyzer/
│   └── vcs/          # Custom content-addressed VCS (no Git)
├── frontend/         # Next.js + Tailwind + Monaco
├── database/
└── docker/
```

## Running locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (optional, for PostgreSQL + Redis)

---

### Option A: Docker for PostgreSQL & Redis

```bash
cd tantr/docker
docker compose up -d
```

Then use `DATABASE_URL=postgresql://tantr:tantr@localhost:5432/tantr` and `REDIS_URL=redis://localhost:6379/0` in backend `.env`.

---

### Option B: Manual PostgreSQL & Redis

**PostgreSQL:**
```bash
# Create database and user
createdb tantr
# Or: CREATE USER tantr WITH PASSWORD 'tantr'; CREATE DATABASE tantr OWNER tantr;
```

**Redis:**
```bash
brew install redis && brew services start redis   # macOS
# Or: redis-server
```

---

### 1. Backend

```bash
cd tantr/backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Edit DATABASE_URL, SECRET_KEY if needed
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000 · Docs: http://localhost:8000/docs

**Health:** `GET /health` (liveness) · `GET /health/ready` (database + Redis checks for deploy/orchestration)

### 2. Celery worker (separate terminal)

```bash
cd tantr/backend
source venv/bin/activate
celery -A celery_app worker --loglevel=info
```

### 3. Frontend (separate terminal)

```bash
cd tantr/frontend
npm install
npm run dev
```

App: http://localhost:3001 (or set `PORT=3000` in `scripts/run-frontend.sh`)

---

### Scripts (from tantr/ root)

```bash
./scripts/run-dev.sh        # Postgres/Redis (Docker) + API + Celery + frontend
./scripts/run-backend.sh    # Backend only
./scripts/run-celery.sh     # Celery worker (optional — API falls back without it)
./scripts/run-frontend.sh   # Frontend (default port 3001)
./scripts/smoke-test.sh     # End-to-end API smoke test
```

---

## Environment variables (backend)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection (default: redis://localhost:6379/0) |
| `SECRET_KEY` | JWT signing key |
| `REPOS_BASE_PATH` | Path for Git repos (default: /repos) |
| `OPENAI_API_KEY` | Optional: real professor feedback via OpenAI (falls back to placeholder if empty) |
| `OPENAI_MODEL` | OpenAI chat model (default: `gpt-4o-mini`) |

## Commit flow

1. Student creates commit via API or frontend editor
2. Commit stored in DB, Git repo updated
3. **Celery task** enqueued automatically
4. Worker: static analysis → AI evaluation → grade + feedback stored
5. Student views results on AI feedback page

---

## Production (Docker)

One command from the repo root:

```bash
chmod +x deploy/prod-up.sh deploy/prod-down.sh
./deploy/prod-up.sh
```

This creates `docker/.env.production` (with generated secrets on first run), builds images, runs Postgres + Redis + API + Celery + Next.js, and runs Alembic migrations on API startup.

| Service | URL |
|---------|-----|
| App | http://localhost:3001 (set `WEB_PORT` in `docker/.env.production` if needed) |
| API | http://localhost:8000 |
| Ready check | http://localhost:8000/health/ready |

**Stop:** `./deploy/prod-down.sh`

**Logs:** `cd docker && docker compose -f docker-compose.prod.yml logs -f api celery_worker`

Full checklist (TLS, domain, backups): [deploy/PRODUCTION.md](deploy/PRODUCTION.md)
