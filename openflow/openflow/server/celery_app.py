"""
Celery application for background tasks
"""
from celery import Celery
from openflow.server.config.settings import settings

# Create Celery app
celery_app = Celery(
    "openflow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks from installed addons
celery_app.autodiscover_tasks(
    packages=["openflow.server.addons"],
    force=True,
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f"Request: {self.request!r}")
    return {"status": "ok", "task_id": self.request.id}
