from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "quad_tasks",
    broker=settings.REDIS_URI,
    backend=settings.REDIS_URI
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Optional: Periodic tasks (beat configuration)
celery_app.conf.beat_schedule = {
    "sync-market-data-every-min": {
        "task": "app.workers.tasks.data_sync.sync_market_data",
        "schedule": 60.0,
    },
    "generate-signals-every-5-min": {
        "task": "app.workers.tasks.signal_generation.generate_signals",
        "schedule": 300.0,
    },
}
