from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "synthteam",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task
def test_task(): 
    return "Celery working"
