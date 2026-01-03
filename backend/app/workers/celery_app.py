"""Celery worker configuration."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "compliance_worker",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
    include=[
        "app.workers.sync_tasks",
        "app.workers.narrative_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 min soft limit
    worker_prefetch_multiplier=1,  # One task at a time
    task_acks_late=True,  # Ack after task completion
    task_reject_on_worker_lost=True,
    result_expires=86400,  # Results expire after 1 day
)

# Task routing
celery_app.conf.task_routes = {
    "app.workers.sync_tasks.*": {"queue": "sync"},
    "app.workers.narrative_tasks.*": {"queue": "ai"},
}
