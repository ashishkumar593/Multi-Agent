"""Celery task queue configuration."""
from backend.core.config import settings

try:
    from celery import Celery

    celery_app = Celery(
        "research_tasks",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )
except ImportError:
    celery_app = None  # type: ignore
