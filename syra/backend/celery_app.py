"""
SYRA Celery application.
Uses Redis as broker and result backend.
"""

from celery import Celery

from config import settings

app = Celery(
    "syra",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.commit_tasks"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min max per task
)
