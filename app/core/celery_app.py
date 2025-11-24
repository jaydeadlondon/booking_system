from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "booking_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.services.tasks"]
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-bookings-every-minute": {
        "task": "app.services.tasks.cleanup_bookings",
        "schedule": 60.0,
    },
}

celery_app.conf.timezone = "UTC"
