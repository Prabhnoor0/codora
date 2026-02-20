"""Celery application configuration."""
from celery import Celery
from config import settings

celery_app = Celery(
    "ai_mentor",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.analyze_repo",
        "tasks.build_embeddings",
        "tasks.build_graph",
        "tasks.update_user_graph",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "tasks.analyze_repo.*": {"queue": "analysis"},
        "tasks.build_embeddings.*": {"queue": "embeddings"},
        "tasks.build_graph.*": {"queue": "analysis"},
        "tasks.update_user_graph.*": {"queue": "default"},
    },
    beat_schedule={},
)
