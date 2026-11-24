# Loads the Celery app with Django, so tasks can be queued from the API.
from .celery import app as celery_app

__all__ = ('celery_app',)
