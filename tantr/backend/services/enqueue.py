"""
Helpers for enqueueing commit analysis without hanging when Redis is down.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from config import settings

log = logging.getLogger("tantr.enqueue")


@lru_cache(maxsize=1)
def redis_reachable() -> bool:
    """Fast probe (cached per process). Returns False if Redis is unavailable."""
    if not settings.USE_CELERY:
        return False
    try:
        import redis

        client = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
        )
        client.ping()
        return True
    except Exception as e:
        log.info("Redis unavailable for Celery (%s); using in-process background tasks", e)
        return False


def clear_redis_cache() -> None:
    redis_reachable.cache_clear()


def enqueue_analyze_commit(commit_id: int, background_tasks) -> str:
    """
    Prefer Celery when Redis is up; otherwise FastAPI BackgroundTasks.
    Returns 'celery' | 'background'.
    """
    if redis_reachable():
        try:
            from tasks.commit_tasks import analyze_commit_task

            analyze_commit_task.delay(commit_id)
            return "celery"
        except Exception as e:
            log.warning("Celery delay failed for commit_id=%s (%s); falling back", commit_id, e)
            clear_redis_cache()

    from tasks.commit_tasks import analyze_commit_task

    def _run() -> None:
        try:
            analyze_commit_task(commit_id)
        except Exception:
            log.exception("In-process commit analysis failed for commit_id=%s", commit_id)

    background_tasks.add_task(_run)
    return "background"
