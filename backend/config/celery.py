"""Celery app for background jobs (code execution).

Start a worker from backend/ with:
    .venv/bin/celery -A config worker -l info --concurrency 2
"""

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('learnlens')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
