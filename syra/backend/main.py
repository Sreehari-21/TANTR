"""
SYRA Backend - FastAPI application entry point.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import settings
from models.database import Base, engine

from models import User, Repository, Commit, CommitAnalysis, Grade, Enquiry  # noqa: F401

from api import auth, repos, commits, enquiries, admin

logger = logging.getLogger("syra")


def configure_logging() -> None:
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )


def run_migrations() -> None:
    from pathlib import Path

    from alembic.config import Config
    from alembic import command

    ini = Path(__file__).resolve().parent / "alembic.ini"
    alembic_cfg = Config(str(ini))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied (alembic upgrade head).")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting SYRA (%s)", settings.ENVIRONMENT)

    if settings.RUN_MIGRATIONS_ON_STARTUP:
        run_migrations()
    elif settings.DEV_AUTO_CREATE_SCHEMA:
        Base.metadata.create_all(bind=engine)
        if settings.ENVIRONMENT == "development":
            logger.warning(
                "DEV_AUTO_CREATE_SCHEMA is on; tables created via SQLAlchemy. "
                "For production use Alembic only (DEV_AUTO_CREATE_SCHEMA=false, RUN_MIGRATIONS_ON_STARTUP or CI migrate)."
            )

    yield

    logger.info("SYRA shutdown complete.")


app = FastAPI(
    title="SYRA",
    description="GitHub-like learning platform with AI-powered code evaluation",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if (settings.DEBUG or settings.ENVIRONMENT != "production") else None,
    redoc_url="/redoc" if (settings.DEBUG or settings.ENVIRONMENT != "production") else None,
)

if settings.TRUSTED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    logger.exception("Unhandled error: %s %s", request.method, request.url.path)
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "syra-backend", "environment": settings.ENVIRONMENT}


@app.get("/health/ready")
def health_ready():
    from sqlalchemy import text

    checks: dict[str, str] = {}
    ok = True

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        ok = False

    try:
        import redis

        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        ok = False

    return {"status": "ready" if ok else "degraded", "checks": checks}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(repos.router, prefix="/api/repos", tags=["repos"])
app.include_router(commits.router, prefix="/api", tags=["commits"])
app.include_router(enquiries.router, prefix="/api/enquiries", tags=["enquiries"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
