import os
from celery import Celery

# Setup Celery
# Defaulting to localhost for local testing outside of docker if needed
redis_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery(
    "jurisbot",
    broker=redis_url,
    backend=redis_url,
    include=["tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Mexico_City",
    enable_utc=True,
)
